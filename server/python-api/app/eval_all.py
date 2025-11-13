import itertools
from pathlib import Path
import importlib
import numpy as np
import pandas as pd
import torch
from tqdm import tqdm
from typing import Optional
from app.engine import get_engine
from app.reranker import rerank_pairs
from app.reranker_mp import rerank_pairs_multi

# ------------------- USER SETUP -------------------
GT_DIR       = Path("/home/lina/Downloads/matching_results_GPT")
GT_TEMPLATE  = "jd_{uid}_matches.csv"   # per-JD file with ground-truth
OUT_DIR      = Path("./eval_two_modes_out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ALPHAS          = [0.5, 0.8]
CANDIDATE_TOPKS = [100, 200]
TOPKS           = [5]

RRF_K        = 60
THRESHOLD    = None
COSINE_FLOOR = 0.0
BATCH_SIZE   = 32

# Exactly two modes, matching your API behavior:
MODES = [
    # label, jd_col, cv_col, resolve_jd_to_col, cv_text_for_ce
    ("clean",   "clean_jd", "clean_cv",   None,         "retrieval"),
]
# --------------------------------------------------


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


# -------------- GT loader ---------------
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


# -------- API-accurate helpers (match app/api.py) --------
def _resolve_to_other_col(eng, jd_clean_text: str, target_col: Optional[str]) -> str:
    """
    If target_col is provided and exists in eng.jd, try exact-match lookup
    from eng.jd_col -> target_col. Otherwise return jd_clean_text as-is.
    """
    if not target_col or target_col not in eng.jd.columns or eng.jd_col not in eng.jd.columns:
        return str(jd_clean_text)
    mask = eng.jd[eng.jd_col].astype(str) == str(jd_clean_text)
    if mask.any():
        cand = eng.jd.loc[mask, target_col].astype(str)
        if not cand.empty:
            return cand.iloc[cand.str.len().argmax()]
    return str(jd_clean_text)

def _pick_cv_text(item: dict, prefer_col: str) -> str:
    """Exactly the CE text selector used in the API."""
    prefer = (prefer_col or "retrieval").lower()
    if prefer == "summary":
        return str(item.get("cv_summary") or item.get("cv_text") or item.get("clean_cv_full") or "")
    if prefer == "clean":
        return str(item.get("clean_cv_full") or item.get("cv_text") or item.get("cv_summary") or "")
    # default: use the exact retrieval text (cv_text)
    return str(item.get("cv_text") or item.get("cv_summary") or item.get("clean_cv_full") or "")


# -------------- Matching core (API-accurate) ---------------
def run_one_jd(
    *,
    eng,
    jd_input_text: str,          # always the *clean_jd* value (per your requirement)
    resolve_jd_to_col: Optional[str],
    cv_text_for_ce: str,
    candidate_topk: int,
    topk: int,
    alpha: float,
):
    # Optional resolve clean -> summary (or None)
    jd_query = _resolve_to_other_col(eng, jd_input_text, resolve_jd_to_col)

    # Retrieval: consider ALL CVs, return only candidate_topk
    all_docs = eng.N_UNIQ
    cands = eng.retrieve(
        jd_text=jd_query,
        k=int(candidate_topk),
        pool=int(all_docs),
        rrf_k=RRF_K,
        threshold=THRESHOLD,
        cosine_floor=COSINE_FLOOR,
    )
    if not cands:
        return [], [], [], [], []

    # Build CE pairs
    texts  = [_pick_cv_text(c, cv_text_for_ce) for c in cands]
    priors = [float(c.get("hybrid_score_0_100", 0.0)) / 100.0 for c in cands]
    uids   = [int(c["cv_uid"]) for c in cands]
    ids    = [int(c["cv_id"]) if c.get("cv_id") is not None else None for c in cands]

    pairs = [(jd_query, t) for t in texts]

    # Multi-GPU if available
    if torch.cuda.is_available() and torch.cuda.device_count() > 1:
        devices = [f"cuda:{i}" for i in range(torch.cuda.device_count())]
        scores = rerank_pairs_multi(pairs, "BAAI/bge-reranker-base", batch_size=BATCH_SIZE, devices=devices)
    else:
        scores = rerank_pairs(pairs, batch_size=BATCH_SIZE)

    scores = np.asarray(scores, dtype=float)
    pri    = np.asarray(priors, dtype=float)

    # Blend
    lo, hi = float(scores.min()), float(scores.max())
    ce_norm = (scores - lo) / (hi - lo) if hi > lo else (scores * 0 + 1.0)
    prior   = np.clip(pri, 0.0, 1.0)
    final   = alpha * ce_norm + (1.0 - alpha) * prior

    order = np.argsort(-final)[:topk]
    return [uids[i] for i in order], [ids[i] for i in order], final[order], scores[order], prior[order]


# ----------------------- main -----------------------
def main():
    all_rows = []

    for (mode_label, jd_col, cv_col, resolve_to, ce_pref) in MODES:
        # Build engine on EXACT columns (like API). We also expose extra CV cols for CE selection.
        eng = get_engine(jd_col=jd_col, cv_col=cv_col, extra_cv_cols={"summary": "cv_summary", "clean": "clean_cv"})

        # IMPORTANT: per your spec, JD input for BOTH modes comes from **clean_jd** column
        if "clean_jd" not in eng.jd.columns:
            raise RuntimeError("Expected 'clean_jd' column present in JD table.")
        jd_df = eng.jd_unique if hasattr(eng, "jd_unique") else eng.jd
        has_uid = "jd_uid" in jd_df.columns

        # get jd_input_texts from clean_jd (not from jd_col!)
        if "clean_jd" in jd_df.columns:
            jd_input_series = jd_df["clean_jd"].astype(str)
        else:
            # fallback to raw table if unique view lacks clean_jd
            jd_input_series = eng.jd["clean_jd"].drop_duplicates().reset_index(drop=True).astype(str)

        for alpha, candidate_topk, topk in itertools.product(ALPHAS, CANDIDATE_TOPKS, TOPKS):
            tag = f"{mode_label}_a{alpha}_cand{candidate_topk}_topk{topk}"
            part_path = OUT_DIR / f"partial_{tag}.csv"
            rows = []

            print(f"\n=== MODE={mode_label} | jd_col={jd_col} | cv_col={cv_col} | resolve={resolve_to} | "
                  f"CE={ce_pref} | alpha={alpha} | cand_topk={candidate_topk} | topk={topk} ===")

            for idx in tqdm(range(len(jd_input_series)), desc=f"JDs[{tag}]"):
                jd_uid = int(jd_df.iloc[idx]["jd_uid"]) if has_uid else idx
                jd_input_text = str(jd_input_series.iloc[idx])

                # Load ground-truth for this JD
                gt_uid, gt_id = load_gt_ids_for_jd(jd_uid)
                if not gt_uid and not gt_id:
                    continue

                uids, ids, final, ce, pri = run_one_jd(
                    eng=eng,
                    jd_input_text=jd_input_text,
                    resolve_jd_to_col=resolve_to,
                    cv_text_for_ce=ce_pref,
                    candidate_topk=candidate_topk,
                    topk=topk,
                    alpha=alpha,
                )

                # Metrics
                R_uid = recall_at_k(uids, gt_uid, k=topk) if gt_uid else 0.0
                R_id  = recall_at_k([x for x in ids if x is not None], gt_id, k=topk) if gt_id else 0.0
                R_at_k = max(R_uid, R_id)

                MRR = max(
                    mrr_at_k(uids, gt_uid, k=topk) if gt_uid else 0.0,
                    mrr_at_k([x for x in ids if x is not None], gt_id, k=topk) if gt_id else 0.0,
                )
                NDCG = max(
                    ndcg_at_k(uids, gt_uid, k=topk) if gt_uid else 0.0,
                    ndcg_at_k([x for x in ids if x is not None], gt_id, k=topk) if gt_id else 0.0,
                )

                rows.append({
                    "mode": mode_label,
                    "jd_uid": jd_uid,
                    "jd_col": jd_col,
                    "cv_col": cv_col,
                    "resolve_jd_to_col": resolve_to,
                    "ce_cv_pref": ce_pref,
                    "alpha": alpha,
                    "candidates_topk": candidate_topk,
                    "topk": topk,
                    f"Recall@{topk}": R_at_k,
                    f"MRR@{topk}": MRR,
                    f"nDCG@{topk}": NDCG,
                    "pred_cv_uids": uids,
                    "pred_cv_ids": ids,
                    "final_scores": [float(x) for x in np.asarray(final, float).tolist()],
                    "ce_scores": [float(x) for x in np.asarray(ce, float).tolist()],
                    "prior_scores": [float(x) for x in np.asarray(pri, float).tolist()],
                })

                # write incrementally
                pd.DataFrame(rows).to_csv(part_path, index=False)

            all_rows.extend(rows)

    # Save combined and summary
    if not all_rows:
        print("\nNo rows produced (no GT?).")
        return

    full = pd.DataFrame(all_rows)
    full_path = OUT_DIR / "eval_two_modes_full.csv"
    full.to_csv(full_path, index=False)
    print(f"\nSaved per-JD rows → {full_path}")

    # Summaries per (mode, alpha, candidates_topk, topk)
    summaries = []
    for tk in sorted(set(full["topk"].tolist())):
        sub = full[full["topk"] == tk]
        grp = sub.groupby(["mode", "alpha", "candidates_topk", "topk"], as_index=False).agg({
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
        ["MRR_mean", "nDCG_mean", "Recall_mean"], ascending=False
    )
    summary_path = OUT_DIR / "eval_two_modes_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"Saved summary → {summary_path}")
    print("\nTop configs:\n", summary.head(20).to_string(index=False))


if __name__ == "__main__":
    import multiprocessing as mp
    mp.set_start_method("spawn", force=True)
    main()
