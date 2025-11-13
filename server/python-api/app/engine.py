# app/engine.py
import os
import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple

import faiss
import numpy as np
import pandas as pd
import torch
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# you can still keep paths/models in config; columns will NOT come from it
from .config import (
    JD_PATH, CV_PATH, JD_FMT, CV_FMT,
    ENCODER_ID, RRF_K, POOL, USE_CUDA,
    CV_ID_COL, JD_ID_COL,         # optional id columns to include if present
)

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

device = (
    "cuda" if (USE_CUDA == "cuda" or (USE_CUDA == "auto" and torch.cuda.is_available()))
    else "cpu"
)

# ---------- utils ----------
def _load(path, fmt):
    if fmt.lower() == "csv":
        return pd.read_csv(path)
    if fmt.lower() == "parquet":
        return pd.read_parquet(path)
    raise ValueError("Unsupported format")

_keep = set("#+./_-%")
def _tok(s: str):
    s = unicodedata.normalize("NFKC", str(s).lower())
    s = re.sub(rf"[^\w{re.escape(''.join(_keep))}\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return [w for w in s.split() if w not in ENGLISH_STOP_WORDS and len(w) > 1]

def _normalize_0_100(a):
    a = np.asarray(a, dtype=float)
    if a.size == 0: return a
    lo, hi = a.min(), a.max()
    if hi <= lo: return np.full_like(a, 100.0)
    return 100.0 * (a - lo) / (hi - lo)

def _rrf_tie_sorted(b_idx, b_sc, e_idx, e_sc, rrf_k=60):
    b_map = {int(d): float(s) for d, s in zip(b_idx, b_sc)}
    e_map = {int(d): float(s) for d, s in zip(e_idx, e_sc)}
    ranks = {}
    for r, d in enumerate(b_idx, 1): ranks[int(d)] = ranks.get(int(d), 0.0) + 1.0/(rrf_k+r)
    for r, d in enumerate(e_idx, 1): ranks[int(d)] = ranks.get(int(d), 0.0) + 1.0/(rrf_k+r)
    rows = [(doc, rrf_s, e_map.get(doc, -1e9), b_map.get(doc, -1e9)) for doc, rrf_s in ranks.items()]
    rows.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
    return rows  # (cv_uid, rrf_score, emb_score, bm25_score)

# ========== Dynamic Engine keyed by (jd_col, cv_col) ==========
class MatchEngine:
    def __init__(
        self,
        jd_col: str,
        cv_col: str,
        *,
        extra_cv_cols: Optional[Dict[str, str]] = None,   # e.g., {"summary": "cv_summary", "clean": "clean_cv"}
    ):
        # load data (paths still from config)
        self.jd = _load(JD_PATH, JD_FMT).reset_index(drop=True)
        self.cv = _load(CV_PATH, CV_FMT).reset_index(drop=True)

        # columns chosen dynamically
        self.jd_col = jd_col
        self.cv_col = cv_col
        self.extra_cv_cols = extra_cv_cols or {}

        assert self.jd_col in self.jd.columns, f"Missing JD column: {self.jd_col}"
        assert self.cv_col in self.cv.columns, f"Missing CV column: {self.cv_col}"

        # create unique views
        if JD_ID_COL in self.jd.columns:
            jd_unique = self.jd[[self.jd_col, JD_ID_COL]].drop_duplicates(subset=[JD_ID_COL]).reset_index(drop=True)
            jd_unique["jd_uid"] = np.arange(len(jd_unique))
            jd_unique.set_index("jd_uid", inplace=True, drop=False)
        else:
            jd_unique = self.jd[[self.jd_col]].drop_duplicates().reset_index(drop=True)
            jd_unique["jd_uid"] = np.arange(len(jd_unique))
            jd_unique.set_index("jd_uid", inplace=True, drop=False)

        if CV_ID_COL in self.cv.columns:
            cv_unique = self.cv[[self.cv_col, CV_ID_COL]].drop_duplicates(subset=[CV_ID_COL]).reset_index(drop=True)
            cv_unique["cv_uid"] = np.arange(len(cv_unique))
            cv_unique.set_index("cv_uid", inplace=True, drop=False)
        else:
            cv_unique = self.cv[[self.cv_col]].drop_duplicates().reset_index(drop=True)
            cv_unique["cv_uid"] = np.arange(len(cv_unique))
            cv_unique.set_index("cv_uid", inplace=True, drop=False)

        self.jd_unique = jd_unique
        self.cv_unique = cv_unique
        self.N_UNIQ = len(cv_unique)

        # map uid -> original member rows (for optional full clean fallback)
        if CV_ID_COL in self.cv.columns:
            grp = self.cv.groupby(CV_ID_COL).indices
            uid2cvid = dict(zip(cv_unique["cv_uid"], cv_unique[CV_ID_COL]))
            self.cv_members = {uid: grp.get(uid2cvid[uid], []) for uid in cv_unique["cv_uid"]}
        else:
            self.cv_members = {i: [i] for i in range(self.N_UNIQ)}

        # BM25 over selected CV column
        corpus_tokens = [_tok(t) for t in cv_unique[self.cv_col].astype(str).tolist()]
        self.bm25 = BM25Okapi(corpus_tokens)

        # encoder + FAISS over selected CV column
        self.model = SentenceTransformer(ENCODER_ID, device=device)
        self.model.max_seq_length = 256

        BATCH = 8 if device == "cuda" else 64
        vecs = []
        with torch.inference_mode():
            for i in range(0, len(cv_unique), BATCH):
                chunk = cv_unique[self.cv_col].astype(str).iloc[i:i+BATCH].tolist()
                with torch.amp.autocast("cuda", enabled=(device == "cuda")):
                    embs = self.model.encode(
                        chunk,
                        batch_size=len(chunk),
                        convert_to_numpy=True,
                        normalize_embeddings=True,
                        show_progress_bar=False,
                    )
                vecs.append(embs.astype("float32"))
                if device == "cuda":
                    torch.cuda.empty_cache()
        self.cv_vecs = np.vstack(vecs)
        emb_dim = self.cv_vecs.shape[1]
        self.index = faiss.IndexFlatIP(emb_dim)
        self.index.add(self.cv_vecs)

        # helpful debug
        self.built_jd_col = self.jd_col
        self.built_cv_col = self.cv_col

    # public APIs
    def emb_scores(self, text: str, topk: int = 2000):
        topk = min(topk, self.N_UNIQ)
        with torch.inference_mode():
            with torch.amp.autocast("cuda", enabled=(device=="cuda")):
                qv = self.model.encode([text], convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False).astype("float32")
        sims, idx = self.index.search(qv, topk)
        return idx[0], sims[0]

    def bm25_scores(self, text: str, topk: int = 2000):
        topk = min(topk, self.N_UNIQ)
        sc = self.bm25.get_scores(_tok(text))
        idx = np.argsort(sc)[-topk:][::-1]
        return idx, sc[idx]

    def retrieve(
        self,
        jd_text: str,
        k: int = 10,
        pool: int = POOL,
        rrf_k: int = RRF_K,
        threshold: Optional[float] = None,
        cosine_floor: float = 0.0,
    ):
        # branch scores
        b_idx, b_sc = self.bm25_scores(jd_text)
        e_idx, e_sc = self.emb_scores(jd_text)

        # fuse + pool
        rows = _rrf_tie_sorted(b_idx, b_sc, e_idx, e_sc, rrf_k=rrf_k)
        rows = rows[:min(pool, len(rows), self.N_UNIQ)]

        cvu  = [d for d, *_ in rows]
        rrf  = np.array([s for _, s, *_ in rows], dtype=float)
        norm = _normalize_0_100(rrf)

        # optional cosine floor
        if cosine_floor > 0.0:
            with torch.inference_mode():
                with torch.amp.autocast("cuda", enabled=(device=="cuda")):
                    qv = self.model.encode([jd_text], convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False).astype("float32")[0]
            cos = np.array([float(np.dot(qv, self.cv_vecs[u])) for u in cvu], dtype=float)
        else:
            cos = np.ones_like(norm)

        keep = np.ones_like(norm, dtype=bool)
        if threshold is not None:
            keep &= (norm >= float(threshold))
        if cosine_floor > 0.0:
            keep &= (cos >= float(cosine_floor))

        cvu, rrf, norm = np.array(cvu)[keep], rrf[keep], norm[keep]
        cvu, rrf, norm = cvu[:k], rrf[:k], norm[:k]

        # package output
        def pick_full(uid: int):
            rows = self.cv_members.get(int(uid), [])
            # if user provided a "clean" column name in extra_cv_cols, use it; else None
            clean_col = self.extra_cv_cols.get("clean")
            if not rows or not clean_col or clean_col not in self.cv.columns:
                return None
            subset = self.cv.loc[rows, clean_col].astype(str)
            return subset.iloc[subset.str.len().argmax()] if not subset.empty else None

        # we expose:
        # - cv_text: the EXACT column used for retrieval/embeddings (self.cv_col)
        # - cv_summary: optional (if user provided a "summary" extra column and it exists)
        # - clean_cv_full: optional (as above)
        out = []
        for uid, s, s100 in zip(cvu, rrf, norm):
            row = {
                "cv_uid": int(uid),
                "hybrid_score": float(s),
                "hybrid_score_0_100": float(s100),
                "cv_text": str(self.cv_unique.at[int(uid), self.cv_col]),
            }
            summary_col = self.extra_cv_cols.get("summary")
            if summary_col and summary_col in self.cv_unique.columns:
                row["cv_summary"] = str(self.cv_unique.at[int(uid), summary_col])
            clean_full = pick_full(int(uid))
            if clean_full is not None:
                row["clean_cv_full"] = clean_full
            if CV_ID_COL in self.cv_unique.columns:
                row["cv_id"] = int(self.cv_unique.at[int(uid), CV_ID_COL])
            out.append(row)
        return out


# --------- engine cache keyed by (jd_col, cv_col) ----------
_ENGINE_CACHE: Dict[Tuple[str, str], MatchEngine] = {}

def get_engine(
    *,
    jd_col: str,
    cv_col: str,
    extra_cv_cols: Optional[Dict[str, str]] = None,
    force_rebuild: bool = False,
) -> MatchEngine:
    key = (jd_col, cv_col)
    if force_rebuild or key not in _ENGINE_CACHE:
        _ENGINE_CACHE[key] = MatchEngine(jd_col=jd_col, cv_col=cv_col, extra_cv_cols=extra_cv_cols)
    return _ENGINE_CACHE[key]
