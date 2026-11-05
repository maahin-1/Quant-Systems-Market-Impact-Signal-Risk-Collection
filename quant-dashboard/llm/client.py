import time
import requests

from config import OPENROUTER_API_KEY, DEFAULT_MODEL

_URL = "https://openrouter.ai/api/v1/chat/completions"

# Fallback chain — tried in order. Free models often rate-limit upstream;
# if one provider is saturated we move to the next.
#
# The free tier changes often. Check https://openrouter.ai/models?q=free and
# update this list (or set OPENROUTER_MODEL in .env) if every call starts failing.
_FALLBACK_MODELS = [
    DEFAULT_MODEL,
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "xingchen-agi/xing4.0-29b-a4b:free",
    "nvidia/nemotron-3.5-lightning:free",
    "recursive/flint-v1.0:free",
]


def _post(model: str, prompt: str) -> requests.Response:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8050",
        "X-Title": "Quant Dashboard",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        # Reasoning models spend part of this budget thinking, so keep it generous
        # or the visible answer gets cut off mid-sentence.
        "max_tokens": 2000,
    }
    return requests.post(_URL, json=payload, headers=headers, timeout=30)


def query_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    models = [model] + [m for m in _FALLBACK_MODELS if m != model]
    last_err = None
    for m in models:
        try:
            resp = _post(m, prompt)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                if content:
                    return f"[via {m}]\n{content}"
                last_err = f"{m}: empty response"
                continue
            if resp.status_code in (429, 503):
                last_err = f"{m}: {resp.status_code}"
                time.sleep(0.5)
                continue
            last_err = f"{m}: {resp.status_code} {resp.text[:120]}"
        except Exception as exc:
            last_err = f"{m}: {exc}"
    raise RuntimeError(f"All free models failed. Last: {last_err}")
