#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# pick an idle GPU
# pick a free GPU (e.g., 1)
export CUDA_VISIBLE_DEVICES=1
# now "cuda" inside Python means that specific GPU
uvicorn app.api:app --host 0.0.0.0 --port 8001 --reload

