import os

# data files (change paths if needed)
JD_PATH = os.getenv("JD_PATH", "~/CV_JD_Matching/Dataset/final_summarized_jd.csv")
CV_PATH = os.getenv("CV_PATH", "~/CV_JD_Matching/Dataset/final_summarized_cv.csv")
JD_FMT  = os.getenv("JD_FMT", "csv")
CV_FMT  = os.getenv("CV_FMT", "csv")

# columns (flip CV_TEXT_COL between "clean_cv" and "cv_summary" freely)
JD_TEXT_COL = os.getenv("JD_TEXT_COL", "clean_jd")
CV_TEXT_COL = os.getenv("CV_TEXT_COL", "cv_summary")


# optional columns to return if present
CV_SUMMARY_COL = "cv_summary"
JD_SUMMARY_COL="jd_summary"
CLEAN_CV_COL   = "clean_cv"
CV_ID_COL      = "cv_id"
JD_ID_COL      = "jd_id"

# retrieval knobs
RRF_K        = int(os.getenv("RRF_K", "60"))
POOL         = int(os.getenv("POOL", "200"))
FINAL_TOPK   = int(os.getenv("FINAL_TOPK", "5"))
THRESHOLD    = float(os.getenv("THRESHOLD", "0"))
COSINE_FLOOR = float(os.getenv("COSINE_FLOOR", "0.0"))

# models
ENCODER_ID   = os.getenv("ENCODER_ID", "BAAI/bge-m3")
CE_MODEL_ID  = os.getenv("CE_MODEL_ID", "BAAI/bge-reranker-base")

# device
USE_CUDA     = os.getenv("USE_CUDA", "auto")   # auto | cpu | cuda
