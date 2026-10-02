import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Circuit breaker flag to prevent repeated 30s hangs on rate-limited or invalid keys
_CIRCUIT_BROKEN = False
_CIRCUIT_ERROR_REASON = ""

def reset_circuit():
    global _CIRCUIT_BROKEN, _CIRCUIT_ERROR_REASON
    _CIRCUIT_BROKEN = False
    _CIRCUIT_ERROR_REASON = ""

def mark_circuit_broken(reason: str):
    global _CIRCUIT_BROKEN, _CIRCUIT_ERROR_REASON
    _CIRCUIT_BROKEN = True
    _CIRCUIT_ERROR_REASON = reason
    print(f"[LLM Circuit Breaker] Real-time fallback engaged: {reason}")

def is_mock_enabled() -> bool:
    load_dotenv(override=True)
    if _CIRCUIT_BROKEN:
        return True
    mock_val = os.getenv("USE_MOCK", "false").strip().lower()
    return mock_val in ("true", "1", "yes")

def get_llm():
    """
    Initializes and returns the ChatLLM client based on configured environment variables.
    Supports Groq (default) and Google Gemini (fallback).
    Fails fast with max_retries=0 and short timeouts so quota limits/connection errors
    instantly fall back to the built-in local QMS intelligence engine without hanging.
    """
    if is_mock_enabled():
        reason = _CIRCUIT_ERROR_REASON or "USE_MOCK is enabled"
        raise ValueError(f"{reason}. Using built-in local QMS intelligence engine.")

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if groq_key:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                temperature=0,
                model="llama-3.3-70b-versatile",
                groq_api_key=groq_key,
                max_retries=1,
                request_timeout=6
            )
        except Exception as e:
            mark_circuit_broken(f"Groq initialization failed: {e}")
            raise

    elif gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            # Use max_retries=0 and fast timeout so 429 quota exhaustion won't stall the UI
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0,
                google_api_key=gemini_key,
                max_retries=0,
                request_timeout=5
            )
        except Exception as e:
            mark_circuit_broken(f"Gemini initialization failed: {e}")
            raise
    else:
        raise ValueError("Missing API Keys! Running with built-in QMS intelligence engine.")

