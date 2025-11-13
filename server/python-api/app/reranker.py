# app/reranker.py
import os
import numpy as np
from sentence_transformers import CrossEncoder
import torch

# pick your model
# app/reranker.py
DEFAULT_RERANKER =  os.environ.get("CE_MODEL_ID", "BAAI/bge-reranker-base")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_CE = None

def _get_ce():
    global _CE
    if _CE is None:
        _CE = CrossEncoder(DEFAULT_RERANKER, device=DEVICE)
    return _CE

def rerank_pairs(pairs, batch_size=16):
    """pairs: list[(query, doc)] -> np.array of scores"""
    ce = _get_ce()
    with torch.inference_mode():
        scores = ce.predict(pairs, batch_size=batch_size)
    return np.asarray(scores, dtype=float)



