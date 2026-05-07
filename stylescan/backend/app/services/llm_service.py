"""
StyleScan — LLM Provider Abstraction

Switches between providers based on LLM_PROVIDER env var.
All providers receive the same system prompt + user prompt and return raw text.

Usage (set in .env):
  LLM_PROVIDER=openrouter        # recommended — one key, any model
  OPENROUTER_API_KEY=sk-or-v1-...

  LLM_PROVIDER=deepseek          # direct DeepSeek API
  DEEPSEEK_API_KEY=sk-...

  LLM_PROVIDER=gemini            # direct Google Gemini API
  GEMINI_API_KEY=AIza...

  LLM_PROVIDER=anthropic         # original Claude (keep as fallback)
  ANTHROPIC_API_KEY=sk-ant-...

Default models per provider (override with LLM_MODEL in .env):
  openrouter → deepseek/deepseek-chat-v3-0324   (~$0.28/M — fast, best quality/price)
  openrouter → deepseek/deepseek-r1             (~$0.80/M — reasoning, best analysis)
  openrouter → google/gemini-2.0-flash-001      (~$0.10/M — cheapest)
  deepseek   → deepseek-chat                    (V3 direct)
  gemini     → gemini-2.0-flash
  anthropic  → claude-haiku-4-5-20251001
"""

import logging
from typing import Literal

from app.core.config import settings

logger = logging.getLogger(__name__)

Provider = Literal["openrouter", "anthropic", "deepseek", "gemini"]

_DEFAULT_MODELS: dict[str, str] = {
    "openrouter": "deepseek/deepseek-chat-v3-0324",
    "anthropic":  "claude-haiku-4-5-20251001",
    "deepseek":   "deepseek-chat",
    "gemini":     "gemini-2.0-flash",
}

_BASE_URLS: dict[str, str] = {
    "openrouter": "https://openrouter.ai/api/v1",
    "deepseek":   "https://api.deepseek.com",
    "gemini":     "https://generativelanguage.googleapis.com/v1beta/openai/",
}


def _get_model() -> str:
    return settings.LLM_MODEL or _DEFAULT_MODELS.get(settings.LLM_PROVIDER, "deepseek-chat")


def call(system_prompt: str, user_prompt: str) -> str:
    """
    Send a system + user prompt to the configured LLM provider.
    Returns raw text response (caller handles JSON parsing).
    Raises on HTTP or auth errors.
    """
    provider: Provider = settings.LLM_PROVIDER  # type: ignore
    model = _get_model()
    max_tokens = settings.LLM_MAX_TOKENS

    logger.debug("LLM call: provider=%s model=%s", provider, model)

    if provider == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, model, max_tokens)
    elif provider in ("openrouter", "deepseek", "gemini"):
        return _call_openai_compat(provider, system_prompt, user_prompt, model, max_tokens)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Use: openrouter | anthropic | deepseek | gemini")


def _call_anthropic(system_prompt: str, user_prompt: str, model: str, max_tokens: int) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},  # prompt caching
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text.strip()


def _call_openai_compat(
    provider: str,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_tokens: int,
) -> str:
    from openai import OpenAI

    api_key = {
        "openrouter": settings.OPENROUTER_API_KEY,
        "deepseek":   settings.DEEPSEEK_API_KEY,
        "gemini":     settings.GEMINI_API_KEY,
    }[provider]
    base_url = _BASE_URLS[provider]

    client = OpenAI(api_key=api_key, base_url=base_url)

    kwargs: dict = dict(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # Ask for JSON output when the model supports it
        # DeepSeek V3 and Gemini both honour response_format
        response_format={"type": "json_object"},
    )

    # DeepSeek R1 (reasoner) doesn't support response_format or system role
    if model == "deepseek-reasoner":
        kwargs.pop("response_format")
        # Merge system into first user message for R1
        kwargs["messages"] = [
            {
                "role": "user",
                "content": f"{system_prompt}\n\n---\n\n{user_prompt}",
            }
        ]

    response = client.chat.completions.create(**kwargs)
    return (response.choices[0].message.content or "").strip()
