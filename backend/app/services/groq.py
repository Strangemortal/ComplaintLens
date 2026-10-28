import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Circuit breaker flag to prevent repeated hangs on rate-limited or invalid keys
_CIRCUIT_BROKEN = False
_CIRCUIT_ERROR_REASON = ""
_ACTIVE_MODEL_INDEX = 0

CANDIDATE_GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b"
]

def reset_circuit():
    global _CIRCUIT_BROKEN, _CIRCUIT_ERROR_REASON, _ACTIVE_MODEL_INDEX
    _CIRCUIT_BROKEN = False
    _CIRCUIT_ERROR_REASON = ""
    _ACTIVE_MODEL_INDEX = 0

def mark_circuit_broken(reason: str):
    global _CIRCUIT_BROKEN, _CIRCUIT_ERROR_REASON
    _CIRCUIT_BROKEN = True
    _CIRCUIT_ERROR_REASON = reason
    print(f"[LLM Circuit Breaker] Real-time fallback engaged: {reason}")

def rotate_model():
    """Rotates to the next available Groq model when rate limit (429) occurs."""
    global _ACTIVE_MODEL_INDEX
    _ACTIVE_MODEL_INDEX = (_ACTIVE_MODEL_INDEX + 1) % len(CANDIDATE_GROQ_MODELS)
    print(f"[LLM Failover] Rotated active model to: {CANDIDATE_GROQ_MODELS[_ACTIVE_MODEL_INDEX]}")
    return CANDIDATE_GROQ_MODELS[_ACTIVE_MODEL_INDEX]

def get_current_model_name():
    groq_model_env = os.getenv("GROQ_MODEL", "").strip()
    if groq_model_env:
        return groq_model_env
    return CANDIDATE_GROQ_MODELS[_ACTIVE_MODEL_INDEX]

def is_mock_enabled() -> bool:
    load_dotenv(override=True)
    if _CIRCUIT_BROKEN:
        return True
    mock_val = os.getenv("USE_MOCK", "false").strip().lower()
    return mock_val in ("true", "1", "yes")

def get_llm():
    """
    Initializes and returns the ChatLLM client based on configured environment variables.
    Supports multi-model Groq failover and Google Gemini fallback.
    """
    if is_mock_enabled():
        reason = _CIRCUIT_ERROR_REASON or "USE_MOCK is enabled"
        raise ValueError(f"{reason}. Using built-in local QMS intelligence engine.")

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    active_model = get_current_model_name()

    if groq_key:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                temperature=0,
                model=active_model,
                groq_api_key=groq_key,
                max_retries=1,
                request_timeout=25
            )
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate_limit" in err_str:
                # Rotate to alternative model with separate quota
                new_model = rotate_model()
                try:
                    from langchain_groq import ChatGroq
                    return ChatGroq(
                        temperature=0,
                        model=new_model,
                        groq_api_key=groq_key,
                        max_retries=1,
                        request_timeout=25
                    )
                except Exception as ex2:
                    mark_circuit_broken(f"All Groq models exhausted: {ex2}")
                    raise
            mark_circuit_broken(f"Groq initialization failed: {e}")
            raise

    elif gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0,
                google_api_key=gemini_key,
                max_retries=1,
                request_timeout=20
            )
        except Exception as e:
            mark_circuit_broken(f"Gemini initialization failed: {e}")
            raise
    else:
        raise ValueError("Missing API Keys! Running with built-in QMS intelligence engine.")


def get_status() -> dict:
    """
    Returns the current LLM connectivity status for the health endpoint.
    """
    load_dotenv(override=True)
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    active_model = get_current_model_name()

    if _CIRCUIT_BROKEN:
        return {
            "llm_live": False,
            "mode": "local_mock",
            "provider": None,
            "reason": _CIRCUIT_ERROR_REASON or "Circuit breaker triggered."
        }

    mock_val = os.getenv("USE_MOCK", "false").strip().lower()
    if mock_val in ("true", "1", "yes"):
        return {"llm_live": False, "mode": "local_mock", "provider": None, "reason": "USE_MOCK is enabled."}

    if groq_key:
        return {"llm_live": True, "mode": "live", "provider": f"Groq ({active_model})", "reason": None}
    if gemini_key:
        return {"llm_live": True, "mode": "live", "provider": "Google Gemini (gemini-2.5-flash)", "reason": None}

    return {"llm_live": False, "mode": "local_mock", "provider": None, "reason": "No API keys configured."}
