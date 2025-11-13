# scripts/eval_grid.py
import os
import itertools
import importlib
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm

# app internals (assumes running from project root)
import app.engine as engmod
from app.engine import get_engine
from app.reranker import rerank_pairs               # single-device CE
from app.reranker_mp import rerank_pairs_multi      # multi-GPU CE
from app.config import CE_MODEL_ID                  # your CE model id (only used for logging)

# ------------ CONFIG (edit if needed) ------------
GT_DIR      = Path("/home/lina/Downloads/matching_results_GPT")
GT_TEMPLATE = "jd_{uid}_matches.csv"     # per-JD GT filename
OUT_DIR     = Path("./eval_runs")        # outputs will go here
OUT_DIR.mkdir(parents=True, exist_ok=True)

ALPHAS          = [0.5, 0.7, 0.8]
CANDIDATE_TOPKS = [100, 200, 400]
TOPKS           = [5, 10]

# modes:
#   (label, jd_col, cv_col, ce_cv_pref)
# ce_cv_pref controls which CV text is fed to the cross-encoder
MODES = [
    ("summary", "jd_summary", "cv_summary", "summary"),
    ("clean",   "clean_jd",   "clean_cv",   "clean"),
]
# -------------------------------------------------

# ---------------- metrics ----------------
def recall_at_k(pred_ids, gt_ids, k=5):
    S = set(gt_ids)
    return float(any(p in S for p in pred_ids[:k]))

def mrr_at_k(pred_ids, gt_ids, k=5):
    S = set(gt_ids)
    for i, p in enumerate(pred_ids[:k], start=1):
        if p in S:
            return 1.0 / i
    return 0.0

def ndcg_at_k(pred_ids, gt_ids, k=5):
    S = set(gt_ids)
    dcg = 0.0
    for i, p in enumerate(pred_ids[:k], start=1):
        if p in S:
            dcg += 1.0 / np.log2(i + 1.0)
    m = min(k, len(S))
    if m == 0:
        return 0.0
    idcg = sum(1.0 / np.log2(i + 1.0) for i in range(1, m + 1))
    return dcg / idcg

# ---------------- GT loader ----------------
def load_gt_ids_for_jd(uid: int):
    path = GT_DIR / GT_TEMPLATE.format(uid=uid)
    if not path.exists():
        return set(), set()
    df = pd.read_csv(path)
    cols = [c.lower() for c in df.columns]
    df.columns = cols

    gt_uid, gt_id = [], []
    if "cv_uid" in cols:
        gt_uid = df["cv_uid"].dropna().astype(int).tolist()
    if "cv_id" in cols:
        gt_id = df["cv_id"].dropna().astype(int).tolist()

    if not gt_uid and not gt_id:
        for name in ["match", "matched", "target", "answer", "label"]:
            if name in cols:
                ints = []
                for v in df[name].dropna().astype(str):
                    try:
                        ints.append(int(v))
                    except:
                        pass
                gt_uid = ints
                break
    return set(gt_uid), set(gt_id)

# ---------------- helpers ----------------
def pick_cv_text(item: dict, pref: str) -> str:
    pref = (pref or "retrieval").lower()
    if pref == "summary":
        return str(item.get("cv_summary") or item.get("cv_text") or item.get("clean_cv_full") or "")
    if pref == "clean":
        return str(item.get("clean_cv_full") or item.get("cv_text") or item.get("cv_summary") or "")
    return str(item.get("cv_text") or item.get("cv_summary") or item.get("clean_cv_full") or "")

def ensure_engine(jd_col: str, cv_col: str):
    """Use the cached, dynamically-built engine for (jd_col, cv_col)."""
    eng = get_engine(jd_col=jd_col, cv_col=cv_col, extra_cv_cols={"summary": "cv_summary", "clean": "clean_cv"})
    return eng

def rerank_with_multi_gpu(pairs, batch_size: int):
    """Use multi-GPU if available; otherwise single device."""
    if torch.cuda.is_available() and torch.cuda.device_count() > 1:
        devices = [f"cuda:{i}" for i in range(torch.cuda.device_count())]
        print(f"[CE] Multi-GPU {devices}, batch={batch_size}, model={CE_MODEL_ID}")
        return rerank_pairs_multi(pairs, batch_size=batch_size, devices=devices)
    else:
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[CE] Single device: {dev}, batch={batch_size}, model={CE_MODEL_ID}")
        return rerank_pairs(pairs, batch_size=batch_size)

# ---------------- main ----------------
def run_config(mode_label, jd_col, cv_col, ce_cv_pref, alpha, cand_topk, topk):
    """Run one config across all JDs and save a CSV."""
    eng = ensure_engine(jd_col=jd_col, cv_col=cv_col)

    # list JDs from the chosen jd_col
    jd_df = eng.jd_unique if hasattr(eng, "jd_unique") else eng.jd
    has_uid = "jd_uid" in jd_df.columns
    jd_series = jd_df[jd_col].astype(str)

    rows = []
    all_docs = eng.N_UNIQ
    print(f"\n=== MODE={mode_label} | jd_col={jd_col} | cv_col={cv_col} | CE={ce_cv_pref} | "
          f"alpha={alpha} | candidates_topk={cand_topk} | topk={topk} | CVs={all_docs} ===")

    # file paths
    tag = f"{mode_label}_a{alpha}_cand{cand_topk}_topk{topk}"
    out_csv = OUT_DIR / f"eval_grid_{tag}.csv"
    partial_csv = OUT_DIR / f"eval_grid_{tag}_partial.csv"

    for idx in tqdm(range(len(jd_series)), desc=f"JDs ({tag})"):
        jd_text = str(jd_series.iloc[idx])
        jd_uid  = int(jd_df.iloc[idx]["jd_uid"]) if has_uid else idx

        # load GT
        gt_uid, gt_id = load_gt_ids_for_jd(jd_uid)
        if not gt_uid and not gt_id:
            # no GT for this JD; skip
            continue

        # 1) retrieve considering ALL CVs; return only candidates_topk
        cands = eng.retrieve(
            jd_text=jd_text,
            k=int(cand_topk),
            pool=int(all_docs),
            rrf_k=60,
            threshold=None,
            cosine_floor=0.0,
        )
        if not cands:
            continue

        # 2) build CE pairs and compute scores
        cv_texts = [pick_cv_text(c, ce_cv_pref) for c in cands]
        priors   = [float(c.get("hybrid_score_0_100", 0.0)) / 100.0 for c in cands]
        pairs    = [(jd_text, t) for t in cv_texts]

        scores = rerank_with_multi_gpu(pairs, batch_size=32)

        # 3) blend CE with prior
        lo, hi = float(scores.min()), float(scores.max())
        ce_norm = (scores - lo) / (hi - lo) if hi > lo else (scores * 0 + 1.0)
        pri     = np.clip(np.asarray(priors, dtype=float), 0.0, 1.0)
        final   = alpha * ce_norm + (1.0 - alpha) * pri

        order = np.argsort(-final)[:topk]
        uids  = [int(cands[i]["cv_uid"]) for i in order]
        ids   = [int(cands[i]["cv_id"]) if cands[i].get("cv_id") is not None else None for i in order]

        # metrics using whichever GT you have
        R_at_k = max(
            recall_at_k(uids, gt_uid, k=topk) if gt_uid else 0.0,
            recall_at_k([x for x in ids if x is not None], gt_id, k=topk) if gt_id else 0.0
        )
        MRR = max(
            mrr_at_k(uids, gt_uid, k=topk) if gt_uid else 0.0,
            mrr_at_k([x for x in ids if x is not None], gt_id, k=topk) if gt_id else 0.0
        )
        NDCG = max(
            ndcg_at_k(uids, gt_uid, k=topk) if gt_uid else 0.0,
            ndcg_at_k([x for x in ids if x is not None], gt_id, k=topk) if gt_id else 0.0
        )

        rows.append({
            "mode": mode_label,
            "jd_uid": jd_uid,
            "jd_col": jd_col,
            "cv_col": cv_col,
            "ce_cv_pref": ce_cv_pref,
            "alpha": alpha,
            "candidates_topk": cand_topk,
            "topk": topk,
            f"Recall@{topk}": R_at_k,
            f"MRR@{topk}": MRR,
            f"nDCG@{topk}": NDCG,
            "pred_cv_uids": uids,
            "pred_cv_ids": ids,
            "final_scores": [float(final[i]) for i in order],
            "ce_scores": [float(scores[i]) for i in order],
            "prior_scores": [float(pri[i]) for i in order],
        })

        # partial save after every JD
        pd.DataFrame(rows).to_csv(partial_csv, index=False)

    # final save for this config
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    print(f"Saved per-JD results → {out_csv}")

    # quick per-config summary
    if len(df):
        grp = df.groupby(["mode","alpha","candidates_topk","topk"], as_index=False).agg({
            f"MRR@{topk}": "mean",
            f"nDCG@{topk}": "mean",
            f"Recall@{topk}": "mean",
        }).rename(columns={
            f"MRR@{topk}": "MRR_mean",
            f"nDCG@{topk}": "nDCG_mean",
            f"Recall@{topk}": "Recall_mean",
        }).sort_values(["MRR_mean","nDCG_mean","Recall_mean"], ascending=False)
        print("\nConfig summary:\n", grp.to_string(index=False))

def main():
    # full grid
    for (mode_label, jd_col, cv_col, ce_cv_pref) in MODES:
        for alpha, cand_topk, topk in itertools.product(ALPHAS, CANDIDATE_TOPKS, TOPKS):
            run_config(
                mode_label=mode_label,
                jd_col=jd_col,
                cv_col=cv_col,
                ce_cv_pref=ce_cv_pref,
                alpha=alpha,
                cand_topk=int(cand_topk),
                topk=int(topk),
            )

    # combine all runs into a global summary
    all_csvs = list(OUT_DIR.glob("eval_grid_*.csv"))
    if not all_csvs:
        print("No run CSVs found; nothing to summarize.")
        return

    frames = []
    for f in all_csvs:
        try:
            frames.append(pd.read_csv(f))
        except Exception:
            pass
    if not frames:
        print("Could not read run CSVs for summary.")
        return

    big = pd.concat(frames, ignore_index=True)
    # normalize metric column names because topk varies (5 or 10)
    # we compute mean metrics separately per (mode, alpha, candidates_topk, topk)
    summaries = []
    for tk in sorted(set(big["topk"].tolist())):
        sub = big[big["topk"] == tk]
        grp = sub.groupby(["mode","alpha","candidates_topk","topk"], as_index=False).agg({
            f"MRR@{tk}": "mean",
            f"nDCG@{tk}": "mean",
            f"Recall@{tk}": "mean",
        }).rename(columns={
            f"MRR@{tk}": "MRR_mean",
            f"nDCG@{tk}": "nDCG_mean",
            f"Recall@{tk}": "Recall_mean",
        })
        summaries.append(grp)

    summary = pd.concat(summaries, ignore_index=True).sort_values(
        ["MRR_mean","nDCG_mean","Recall_mean"], ascending=False
    )
    summary_path = OUT_DIR / "eval_grid_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"\nSaved combined summary → {summary_path}")
    print("\nTop configs:\n", summary.head(20).to_string(index=False))

if __name__ == "__main__":
    import multiprocessing as mp
    mp.set_start_method("spawn", force=True)
    main()
