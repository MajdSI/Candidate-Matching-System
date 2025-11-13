# app/api.py
from typing import Optional, List, Dict, Set, Tuple, Union


import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import numpy as np
import os
from types import SimpleNamespace
from dotenv import load_dotenv

from .engine import get_engine
from .reranker import rerank_pairs
from .reranker_mp import rerank_pairs_multi
from .config import THRESHOLD, RRF_K, POOL  # only knobs/paths; NOT column choices
from .llm_explain import explain_matches

load_dotenv()
AUTO_EXPLAIN = os.getenv("AUTO_EXPLAIN", "0") == "1"
LLM_MODEL_DEFAULT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
EXPLAIN_MAX_REASONS = int(os.getenv("EXPLAIN_MAX_REASONS", "4"))
EXPLAIN_CHAR_BUDGET = int(os.getenv("EXPLAIN_CHAR_BUDGET", "4000"))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- helpers ----------
def _resolve_to_other_col(eng, jd_clean_text: str, target_col: Optional[str]) -> str:
    """If target_col is provided and exists in eng.jd, try exact-match lookup from eng.jd_col -> target_col."""
    if not target_col or target_col not in eng.jd.columns or eng.jd_col not in eng.jd.columns:
        return str(jd_clean_text)
    mask = eng.jd[eng.jd_col].astype(str) == str(jd_clean_text)
    if mask.any():
        cand = eng.jd.loc[mask, target_col].astype(str)
        if not cand.empty:
            return cand.iloc[cand.str.len().argmax()]
    return str(jd_clean_text)

def _pick_cv_text(item: dict, prefer_col: str) -> str:
    """Pick what to feed to CE from item given a preferred logical label: 'summary' or 'clean' or 'retrieval'."""
    prefer = (prefer_col or "retrieval").lower()
    if prefer == "summary":
        return str(item.get("cv_summary") or item.get("cv_text") or item.get("clean_cv_full") or "")
    if prefer == "clean":
        return str(item.get("clean_cv_full") or item.get("cv_text") or item.get("cv_summary") or "")
    # default: use the exact retrieval text (cv_text)
    return str(item.get("cv_text") or item.get("cv_summary") or item.get("clean_cv_full") or "")

# ---------- models ----------
class RetrieveReq(BaseModel):
    # free-text JD string (usually "clean" JD)
    jd_text: str

    # which JD/CV columns to build the engine on
    jd_col: str                   # e.g., "jd_summary" or "clean_jd"
    cv_col: str                   # e.g., "cv_summary" or "clean_cv"

    # optional extra CV columns to include in the response for convenience
    extra_cv_cols: Optional[Dict[str, str]] = {"summary": "cv_summary", "clean": "clean_cv"}

    # (optional) resolve the incoming jd_text by exact match from jd_col -> this target col before retrieval
    resolve_jd_to_col: Optional[str] = None      # e.g., "jd_summary". If None, use jd_text as-is.

    # retrieval knobs
    topk: int = 10
    pool: int = POOL
    rrf_k: int = RRF_K
    threshold: Optional[float] = THRESHOLD
    cosine_floor: float = 0.0

class RetrieveRes(BaseModel):
    cv_uid: int
    hybrid_score: float
    hybrid_score_0_100: float
    cv_text: Optional[str] = None        # exact text used by retriever (cv_col)
    cv_summary: Optional[str] = None     # only if provided via extra_cv_cols
    clean_cv_full: Optional[str] = None  # only if provided via extra_cv_cols
    cv_id: Optional[int] = None
    # debug
    built_jd_col: Optional[str] = None
    built_cv_col: Optional[str] = None
    used_jd_text: Optional[str] = None
    resolved_to_col: Optional[str] = None

class MatchReq(BaseModel):
    # free-text JD string
    jd_text: str

    # engine build columns
    jd_col: str
    cv_col: str
    extra_cv_cols: Optional[Dict[str, str]] = {"summary": "cv_summary", "clean": "clean_cv"}

    # resolve JD to another column before retrieval? (exact match lookup)
    resolve_jd_to_col: Optional[str] = None

    # CE text choice for CV: "retrieval" | "summary" | "clean"
    cv_text_for_ce: str = "retrieval"

    # counts/knobs
    topk: int = 5
    candidate_topk: int = 200
    pool: int = 637
    rrf_k: int = RRF_K
    threshold: Optional[float] = None
    cosine_floor: float = 0.0

    # CE blend
    alpha: float = 0.7
    batch_size: int = 32

class MatchRes(BaseModel):
    rank: int
    final_score: float
    ce_score: float
    hybrid_score_0_100: float
    cv_uid: int
    cv_id: Optional[int] = None
    cv_text: Optional[str] = None
    cv_summary: Optional[str] = None
    clean_cv_full: Optional[str] = None
    # debug
    built_jd_col: Optional[str] = None
    built_cv_col: Optional[str] = None
    used_jd_text: Optional[str] = None
    resolved_to_col: Optional[str] = None
    cv_text_for_ce: Optional[str] = None

# ---------- endpoints ----------    explanation: Optional[dict] = None

@app.get("/health")
def health():
    # Build a default engine just to verify everything loads (columns arbitrary here)
    eng = get_engine(jd_col="jd_summary", cv_col="cv_summary", extra_cv_cols={"summary":"cv_summary","clean":"clean_cv"})
    return {"ok": True, "built_jd_col": eng.built_jd_col, "built_cv_col": eng.built_cv_col}

@app.post("/retrieve", response_model=List[RetrieveRes])
def retrieve(req: RetrieveReq):
    # build engine on EXACT columns passed by the user
    eng = get_engine(jd_col=req.jd_col, cv_col=req.cv_col, extra_cv_cols=req.extra_cv_cols)

    # resolve JD to another column value (optional)
    jd_query = _resolve_to_other_col(eng, req.jd_text, req.resolve_jd_to_col)

    cands = eng.retrieve(
        jd_text=jd_query,
        k=req.topk,
        pool=req.pool,
        rrf_k=req.rrf_k,
        threshold=req.threshold,
        cosine_floor=req.cosine_floor,
    )

    out: List[RetrieveRes] = []
    for c in cands:
        out.append(RetrieveRes(
            cv_uid=c["cv_uid"],
            hybrid_score=c["hybrid_score"],
            hybrid_score_0_100=c["hybrid_score_0_100"],
            cv_text=c.get("cv_text"),
            cv_summary=c.get("cv_summary"),
            clean_cv_full=c.get("clean_cv_full"),
            cv_id=c.get("cv_id"),
            built_jd_col=eng.built_jd_col,
            built_cv_col=eng.built_cv_col,
            used_jd_text=jd_query,
            resolved_to_col=req.resolve_jd_to_col,
        ))
    return out

@app.post("/match", response_model=List[MatchRes])
def match(req: MatchReq):
    # engine built on user-chosen columns
    eng = get_engine(jd_col=req.jd_col, cv_col=req.cv_col, extra_cv_cols=req.extra_cv_cols)

    # JD string used for BOTH retrieval and CE (after optional resolution)
    jd_query = _resolve_to_other_col(eng, req.jd_text, req.resolve_jd_to_col)
    all_k = eng.N_UNIQ
    # 1) retrieve a large pool
    cands = eng.retrieve(
        jd_text=jd_query,
        k=req.candidate_topk,
        pool=all_k,
        rrf_k=req.rrf_k,
        threshold=req.threshold,
        cosine_floor=req.cosine_floor,
    )
    if not cands:
        return []



    # 2) CE text for CV
    cv_texts = [_pick_cv_text(c, req.cv_text_for_ce) for c in cands]
    priors   = [float(c.get("hybrid_score_0_100", 0.0)) / 100.0 for c in cands]
    pairs    = [(jd_query, t) for t in cv_texts]
     # <-- exact text fed to CE for this candidate
    # 3) run CE (use multi-GPU if available)
    if torch.cuda.is_available() and torch.cuda.device_count() > 1:
        devices = [f"cuda:{i}" for i in range(torch.cuda.device_count())]
        scores = rerank_pairs_multi(pairs, batch_size=req.batch_size, devices=devices)
    else:
        scores = rerank_pairs(pairs, batch_size=req.batch_size)

    # 4) blend CE with prior
    lo, hi = float(scores.min()), float(scores.max())
    ce_norm = (scores - lo) / (hi - lo) if hi > lo else (scores * 0 + 1.0)
    pri     = np.clip(np.asarray(priors, dtype=float), 0.0, 1.0)
    final   = req.alpha * ce_norm + (1.0 - req.alpha) * pri

    order = np.argsort(-final)[:req.topk]

    out: List[MatchRes] = []
    for rnk, i in enumerate(order, start=1):
        item = cands[i]
        ce_cv_text = cv_texts[i] 
        out.append(MatchRes(
            rank=rnk,
            final_score=float(final[i]),
            ce_score=float(scores[i]),
            hybrid_score_0_100=float(item.get("hybrid_score_0_100", 0.0)),
            cv_uid=int(item["cv_uid"]),
            cv_id=item.get("cv_id"),
            cv_text=ce_cv_text,
            cv_summary=item.get("cv_summary"),
            clean_cv_full=item.get("clean_cv_full"),
        ))

    if AUTO_EXPLAIN:
        # Convert to dicts so we can enrich with LLM reasons
        ranked_dicts = [o.model_dump() for o in out]

        # Minimal shim carrying only what the explainer needs (no MatchReq changes)
        shim = SimpleNamespace(
            jd_text=req.jd_text,
            llm_model=LLM_MODEL_DEFAULT,
            max_reasons=EXPLAIN_MAX_REASONS,
            per_cv_char_budget=EXPLAIN_CHAR_BUDGET,
        )

        enriched = explain_matches(shim, ranked_dicts)
        return enriched  # returns same list, but each item may include `explanation`

    return out