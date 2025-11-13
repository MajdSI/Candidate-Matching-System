# app/reranker_mp.py (example skeleton)
import torch
from sentence_transformers import CrossEncoder
from typing import List, Tuple
import numpy as np
import multiprocessing as mp

def _worker(device: str, pairs: List[Tuple[str,str]], model_id: str, batch_size: int, out_queue: mp.Queue, idx_range: Tuple[int,int]):
    torch.cuda.set_device(device)
    model = CrossEncoder(model_id, device=device)
    lo, hi = idx_range
    chunk = pairs[lo:hi]
    scores = model.predict(chunk, batch_size=batch_size, convert_to_numpy=True, show_progress_bar=False)
    out_queue.put((lo, hi, scores))

def rerank_pairs_multi(pairs, model_id: str, batch_size: int, devices: list):
    n = len(pairs)
    if n == 0:
        return np.zeros((0,), dtype=np.float32)

    # split pairs across devices
    splits = np.array_split(np.arange(n), len(devices))
    q = mp.Queue()
    procs = []
    for dev, idxs in zip(devices, splits):
        if len(idxs) == 0: 
            continue
        p = mp.Process(target=_worker, args=(dev, pairs, model_id, batch_size, q, (int(idxs[0]), int(idxs[-1])+1)))
        p.start()
        procs.append(p)

    out = np.zeros((n,), dtype=np.float32)
    done = 0
    while done < len(procs):
        lo, hi, scores = q.get()
        out[lo:hi] = scores
        done += 1
    for p in procs:
        p.join()
    return out
