import os, sys, re, unicodedata
import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer

# Import your config
from .config import (
    JD_PATH, JD_FMT, JD_TEXT_COL, JD_ID_COL,
    ENCODER_ID, USE_CUDA
)

def _expanduser_path(p: str) -> str:
    return os.path.abspath(os.path.expanduser(p))

def _load(path: str, fmt: str) -> pd.DataFrame:
    path = _expanduser_path(path)
    if fmt.lower() == "csv":
        return pd.read_csv(path)
    elif fmt.lower() == "parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported JD_FMT: {fmt}")

def build_jd_unique(jd: pd.DataFrame) -> pd.DataFrame:
    # If you have a stable JD id column, keep one row per id; else dedupe on text.
    if JD_ID_COL in jd.columns:
        uniq = (jd[[JD_TEXT_COL, JD_ID_COL]]
                .drop_duplicates(subset=[JD_ID_COL])
                .reset_index(drop=True))
    else:
        uniq = (jd[[JD_TEXT_COL]]
                .drop_duplicates()
                .reset_index(drop=True))
    uniq["jd_uid"] = np.arange(len(uniq), dtype=np.int32)
    uniq = uniq.set_index("jd_uid", drop=False)
    # Keep a friendly text column name in the index file
    uniq = uniq.rename(columns={JD_TEXT_COL: "jd_text"})
    return uniq

def encode_texts(texts, model: SentenceTransformer, batch: int, device: str) -> np.ndarray:
    vecs = []
    with torch.inference_mode():
        for i in range(0, len(texts), batch):
            chunk = [str(t) for t in texts[i:i+batch]]
            # autocast helps memory on CUDA; harmless on CPU when disabled
            with torch.amp.autocast("cuda", enabled=(device=="cuda")):
                embs = model.encode(
                    chunk,
                    batch_size=len(chunk),
                    convert_to_numpy=True,
                    normalize_embeddings=True,   # cosine-ready unit vectors
                    show_progress_bar=False
                )
            vecs.append(embs.astype("float32"))
            if device == "cuda":
                torch.cuda.empty_cache()
    return np.vstack(vecs) if vecs else np.zeros((0, 0), dtype="float32")

def main(out_dir: str = "./embeddings_out", batch: int = None):
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    # device selection
    device = (
        "cuda" if (USE_CUDA == "cuda" or (USE_CUDA == "auto" and torch.cuda.is_available()))
        else "cpu"
    )

    # sensible default batch
    if batch is None:
        batch = 8 if device == "cuda" else 64

    # 1) Load and make unique JD table
    jd_df = _load(JD_PATH, JD_FMT)
    assert JD_TEXT_COL in jd_df.columns, f"Missing JD text column '{JD_TEXT_COL}'"
    jd_unique = build_jd_unique(jd_df)

    # 2) Load encoder
    print(f"[info] Using device={device} | encoder={ENCODER_ID}")
    model = SentenceTransformer(ENCODER_ID, device=device)
    model.max_seq_length = 256

    # 3) Encode all JDs
    texts = jd_unique["jd_text"].astype(str).tolist()
    print(f"[info] Encoding {len(texts)} unique JDs in batches of {batch} ...")
    jd_vecs = encode_texts(texts, model, batch=batch, device=device)
    print(f"[info] jd_vecs shape = {jd_vecs.shape} (dtype={jd_vecs.dtype})")

    # 4) Save outputs
    out_dir = _expanduser_path(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    emb_path = os.path.join(out_dir, "jd_embeddings.npy")
    idx_path = os.path.join(out_dir, "jd_index.parquet")

    np.save(emb_path, jd_vecs)
    # Keep only useful mapping columns
    idx_cols = ["jd_uid", "jd_text"] + ([JD_ID_COL] if JD_ID_COL in jd_unique.columns else [])
    jd_unique[idx_cols].to_parquet(idx_path, index=False)

    print(f"[done] Saved embeddings → {emb_path}")
    print(f"[done] Saved index map → {idx_path}")

if __name__ == "__main__":
    # Optional CLI args:
    #   python -m app.save_jd_embeddings [out_dir] [batch]
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "./embeddings_out"
    batch = int(sys.argv[2]) if len(sys.argv) > 2 else None
    main(out_dir=out_dir, batch=batch)
