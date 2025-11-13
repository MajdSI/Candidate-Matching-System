import pandas as pd
import numpy as np
from pathlib import Path


files = sorted(Path(".").glob("**/eval_all_jds_grid_partial*.csv"))  # adjust pattern
df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)



TOPK = int(df['topk'].iloc[0])  # e.g., 10

summary = (
    df.groupby(["mode","alpha","pool"], as_index=False)
      .agg({f"MRR@{TOPK}":"mean", f"nDCG@{TOPK}":"mean", f"Recall@{TOPK}":"mean"})
      .rename(columns={f"MRR@{TOPK}":"MRR_mean",
                       f"nDCG@{TOPK}":"nDCG_mean",
                       f"Recall@{TOPK}":"Recall_mean"})
)

# Rank: prioritize MRR, then nDCG, then Recall
summary = summary.sort_values(["MRR_mean","nDCG_mean","Recall_mean"], ascending=False)
print(summary.head(10))
