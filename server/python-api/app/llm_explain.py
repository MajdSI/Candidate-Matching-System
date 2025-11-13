# server/python-api/app/llm_explain.py
from __future__ import annotations
import os, json
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# --- Azure OpenAI config ---
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEFAULT_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

# Create client per thread to avoid contention (thread-local storage would be better but this works)
def _client() -> AzureOpenAI:
    """Create a new Azure OpenAI client (one per thread for better parallelism)."""
    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY:
        raise RuntimeError("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
    return AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=API_VERSION,
        timeout=60.0,  # Increased timeout to handle slow responses (60 seconds)
    )

def _deployment_name(req_like: Any) -> str:
    """Use req_like.llm_model if present, else fallback to DEFAULT_DEPLOYMENT."""
    return getattr(req_like, "llm_model", None) or DEFAULT_DEPLOYMENT

# --- Prompt templates ---
SYSTEM_MSG = (
    "You are a precise job-matching assistant. "
    "Given a Job Description (JD) and a Candidate CV text, produce JSON with:\n"
    "Rules:\n"
    "- Return ONLY valid JSON with the exact key name 'reasons' (not 'matches', 'match_reasons', or any other key).\n"
    "- The JSON must have this exact structure: {{\"reasons\": [\"point1\", \"point2\", \"point3\"]}}\n"
    "- Include 3–6 concise bullet points (each ≤ 20 words).\n"
    "- Focus only on *positive matches* (why this CV fits the JD).\n"
    "- Be specific and factual — cite concrete overlaps (skills, tools, degrees, years, experience, or achievements).\n"
    "- Do not include risks, mismatches, or general summaries.\n"
    "- Return ONLY JSON. No prose, no explanations, no markdown formatting."
)

USER_TEMPLATE = (
    "JD:\n"
    "```\n"
    "{jd}\n"
    "```\n\n"
    "CV:\n"
    "```\n"
    "{cv}\n"
    "```\n\n"
    "Return JSON with the key 'reasons' containing an array of 3-4 match points.\n"
    "Required format: {{\"reasons\": [\"match point 1\", \"match point 2\", \"match point 3\"]}}\n"
    "- Keep total response <= 700 tokens.\n"
    "- Reasons should cite concrete overlaps (skills, tools, years/education).\n"
)

def explain_one(
    req_like: Any,
    jd_text: str,
    cv_text: str,
    cv_uid: Optional[int] = None,
    max_reasons: int = 4,
    per_cv_char_budget: int = 4000,
) -> Dict[str, Any]:
    """Ask the LLM for a compact JSON rationale for a single (JD, CV) pair.
    
    Optimized for speed:
    - Reduced input size (2500 chars) for faster processing
    - Separate client per thread to avoid contention
    """
    # Reduce input size for faster tokenization and processing
    optimized_budget = min(per_cv_char_budget, 2500)
    jd_trim = jd_text[:optimized_budget]
    cv_trim = cv_text[:optimized_budget]

    messages = [
        {"role": "system", "content": SYSTEM_MSG},
        {"role": "user", "content": USER_TEMPLATE.format(jd=jd_trim, cv=cv_trim)},
    ]

    client = _client()
    resp = client.chat.completions.create(
        model=_deployment_name(req_like),
        messages=messages,
    )

    txt = resp.choices[0].message.content or ""
    try:
        data = json.loads(txt)
        # The LLM should always return "reasons" key based on our prompt
        # But we'll validate and limit the reasons list
        if isinstance(data, dict) and "reasons" in data and isinstance(data["reasons"], list):
            data["reasons"] = data["reasons"][:max_reasons]
        return data
    except Exception:
        return {"raw": txt}

def explain_matches(req_like: Any, ranked: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add an 'explanation' field for each item in ranked results.
    
    Uses parallel processing to generate explanations concurrently for better performance.
    
    IMPORTANT: The 'ranked' parameter MUST be the top 5 candidates in rank order (1, 2, 3, 4, 5).
    The function preserves the exact order - explanations are generated for candidates in the
    same order they are received, and returned in the same order.
    """
    jd_text = getattr(req_like, "jd_text", "")
    max_reasons = getattr(req_like, "max_reasons", 4)
    per_cv_char_budget = getattr(req_like, "per_cv_char_budget", 4000)
    
    # Log to verify we're processing the correct candidates
    if ranked:
        ranks = [item.get("rank") for item in ranked if item.get("rank")]
        cv_uids = [item.get("cv_uid") for item in ranked if item.get("cv_uid")]
        print(f"[EXPLAIN_MATCHES] Processing {len(ranked)} candidates")
        print(f"[EXPLAIN_MATCHES] Ranks: {ranks}")
        print(f"[EXPLAIN_MATCHES] CV UIDs: {cv_uids}")
    
    # Prepare all items with their CV text
    # idx preserves the original order (0, 1, 2, 3, 4 for top 5)
    items_with_cv: List[Tuple[int, Dict[str, Any], str]] = []
    for idx, item in enumerate(ranked):
        cv_text = item.get("cv_text") or item.get("cv_summary") or item.get("clean_cv_full") or ""
        items_with_cv.append((idx, item, cv_text))
    
    # Function to explain a single item (for parallel execution)
    def explain_item_wrapper(args: Tuple[int, Dict[str, Any], str]) -> Tuple[int, Dict[str, Any]]:
        idx, item, cv_text = args
        try:
            exp = explain_one(
                req_like=req_like,
                jd_text=jd_text,
                cv_text=cv_text,
                cv_uid=item.get("cv_uid"),
                max_reasons=max_reasons,
                per_cv_char_budget=per_cv_char_budget,
            )
        except Exception as e:
            exp = {"error": str(e)}
        enriched = dict(item)
        enriched["explanation"] = exp
        return (idx, enriched)
    
    # Execute all explanations in parallel
    # Use ThreadPoolExecutor for I/O-bound operations (HTTP requests)
    # Increased max_workers for better parallelism (Azure OpenAI can handle many concurrent requests)
    explanations: Dict[int, Dict[str, Any]] = {}
    # Use more workers - Azure OpenAI can handle many concurrent requests
    max_workers = min(len(ranked), 20)  # Increased to 20 for maximum parallelism
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_idx = {executor.submit(explain_item_wrapper, args): args[0] for args in items_with_cv}
        
        # Collect results as they complete
        for future in as_completed(future_to_idx):
            try:
                idx, enriched = future.result()
                explanations[idx] = enriched
            except Exception as e:
                # If a task fails, use the original item with an error explanation
                idx = future_to_idx[future]
                original_item = ranked[idx]
                enriched = dict(original_item)
                enriched["explanation"] = {"error": f"Failed to generate explanation: {str(e)}"}
                explanations[idx] = enriched
    
    # Reconstruct output in original order - CRITICAL: This preserves the rank order
    # explanations dict uses idx (0,1,2,3,4) as keys, so we reconstruct in that order
    out: List[Dict[str, Any]] = [explanations[i] for i in range(len(ranked))]
    
    # Verify order is preserved
    if out:
        output_ranks = [item.get("rank") for item in out if item.get("rank")]
        print(f"[EXPLAIN_MATCHES] Output order verified - Ranks: {output_ranks}")
    
    return out
