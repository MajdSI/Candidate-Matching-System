# Candidate Matching System

## Full Report
[**Click here to view the detailed project report (PDF)**](Candidate_Matching_System_Report.pdf)

## Overview
The Candidate Matching System improves automated recruitment by combining hybrid retrieval, cross-encoder reranking, and knowledge graph reasoning. The system moves beyond keyword matching by incorporating semantic understanding and structured candidate–job relationships, resulting in more accurate and interpretable candidate ranking.

## Key Features
- **Hybrid Retrieval:** Combines BM25S sparse search with BGE-M3 dense embeddings to balance lexical and semantic relevance.
- **Cross-Encoder Reranking:** Refines top retrieved candidates using a joint JD–CV encoding model for higher precision.
- **Knowledge Graph Reasoning:** Represents skills, tools, roles, and education as graph entities to improve contextual understanding.
- **Explainability:** Provides reasoning that clarifies why top candidates match a given job description.

## System Workflow
1. Data collection from public CV–JD datasets.
2. Preprocessing, normalization, and GPT-5–based standardization into structured formats.
3. Hybrid retrieval using Reciprocal Rank Fusion (RRF) to merge sparse and dense rankings.
4. Cross-encoder reranking of the top candidate pool.
5. Knowledge graph generation and reasoning.
6. Final ranked candidate list with interpretability outputs.

(See the full workflow diagram in the project report.)

## Evaluation Summary
Experiments were conducted on 452 job descriptions and 637 candidate CVs.
The best configuration used standardized data with α = 0.5 and a candidate pool of 200.

**Top Metrics:**
- gNDCG: **0.85**
- MAP: **0.53**
- Precision@10: **0.59**
- Mean semantic relevance score: **70.6**

