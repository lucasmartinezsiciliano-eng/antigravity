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
  openrouter → deepseek/deepseek-chat-v3-0324       (~$0.28/M — fast, best quality/price)
  openrouter → moonshotai/kimi-k2-thinking          (~$0.60/$2.50/M — best reasoning)
  openrouter → deepseek/deepseek-r1                 (~$0.80/M — strong reasoning)
  openrouter → google/gemini-2.0-flash-001          (~$0.10/M — cheapest)
  deepseek   → deepseek-chat                        (V3 direct)
  gemini     → gemini-2.0-flash
  anthropic  → claude-haiku-4-5-20251001
"""

import logging
import re
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

# Models that return <think>…</think> blocks — strip before returning
_THINKING_MODEL_PREFIXES = (
    "moonshotai/kimi-k2-thinking",
    "moonshotai/kimi-k2.5-thinking",
    "moonshotai/kimi-k2.6-thinking",
    "deepseek/deepseek-r1",
    "deepseek-reasoner",
)

# Models that don't support response_format=json_object or system role
_NO_JSON_FORMAT_PREFIXES = _THINKING_MODEL_PREFIXES


def _is_thinking_model(model: str) -> bool:
    return any(model.startswith(p) for p in _THINKING_MODEL_PREFIXES)


def _strip_thinking(text: str) -> str:
    """Remove <think>…</think> blocks emitted by reasoning models."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


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

    logger.info("LLM call: provider=%s model=%s", provider, model)

    if provider == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, model, max_tokens)
    elif provider in ("openrouter", "deepseek", "gemini"):
        return _call_openai_compat(provider, system_prompt, user_prompt, model, max_tokens)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Use: openrouter | anthropic | deepseek | gemini")


def _call_anthropic(system_prompt: str, user_prompt: str, model: str, max_tokens: int) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=120.0)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
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

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)

    thinking = _is_thinking_model(model)

    if thinking:
        # Thinking/reasoner models: no response_format, merge system into user message
        kwargs: dict = dict(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{system_prompt}\n\n"
                        "IMPORTANTE: responde SOLO con el JSON pedido, sin texto adicional.\n\n"
                        f"---\n\n{user_prompt}"
                    ),
                }
            ],
        )
    else:
        kwargs = dict(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

    response = client.chat.completions.create(**kwargs)
    raw = (response.choices[0].message.content or "").strip()

    if thinking:
        raw = _strip_thinking(raw)
        logger.debug("LLM thinking model — stripped think blocks, remaining length=%d", len(raw))

    return raw
