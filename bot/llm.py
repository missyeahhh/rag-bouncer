"""Which model answers and judges. Free in both cases.

With MISTRAL_API_KEY set (CI): Mistral's free tier. Without it (local): Ollama.
"""
import os

MISTRAL_MODEL = "ministral-14b-latest"  # mistral-small and mistral-medium return 429 on the free tier 
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:20b")


_LIMITER = None


def chat_model():
    global _LIMITER
    if os.environ.get("MISTRAL_API_KEY"):
        from langchain_core.rate_limiters import InMemoryRateLimiter
        if _LIMITER is None:
            # One limiter for the whole run, shared by the bot and the judge.
            _LIMITER = InMemoryRateLimiter(requests_per_second=0.4, check_every_n_seconds=0.1, max_bucket_size=1)
        from langchain_mistralai import ChatMistralAI
        # The free tier rejects bursts with 429: stay well under one request per second.
        return ChatMistralAI(model=MISTRAL_MODEL, temperature=0, max_retries=6, rate_limiter=_LIMITER)
    from langchain_ollama import ChatOllama
    return ChatOllama(model=OLLAMA_MODEL, temperature=0)


def model_name():
    return f"mistral:{MISTRAL_MODEL}" if os.environ.get("MISTRAL_API_KEY") else f"ollama:{OLLAMA_MODEL}"
