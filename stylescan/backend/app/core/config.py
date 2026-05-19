import logging
import os
import tempfile

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from functools import lru_cache

_logger = logging.getLogger(__name__)

_DEFAULT_PHOTO_TEMP_DIR = os.path.join(tempfile.gettempdir(), "stylescan")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )
    # App
    APP_NAME: str = "VISAI API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./knowledge_base/stylescan.db"

    # LLM Provider — switch without touching code
    # Values: anthropic | deepseek | gemini
    LLM_PROVIDER: str = "anthropic"
    LLM_MODEL: str = "claude-opus-4-7"   # override in .env to switch model
    LLM_MAX_TOKENS: int = 4096

    # API keys — only the key matching LLM_PROVIDER is required at runtime
    OPENROUTER_API_KEY: str = "" # required if LLM_PROVIDER=openrouter
    ANTHROPIC_API_KEY: str = ""  # required if LLM_PROVIDER=anthropic
    DEEPSEEK_API_KEY: str = ""   # required if LLM_PROVIDER=deepseek
    GEMINI_API_KEY: str = ""     # required if LLM_PROVIDER=gemini

    # Legacy aliases (kept for backwards compat)
    CLAUDE_MODEL: str = ""       # ignored if LLM_PROVIDER != anthropic
    CLAUDE_MAX_TOKENS: int = 4096  # ignored (LLM_MAX_TOKENS used instead)

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_BASE_COUPON_ID: str = ""  # Created once, all barber codes reference it

    # Pricing (in cents)
    PRICE_BASE_ANALYSIS: int = 1499      # €14.99
    PRICE_COLORIMETRY: int = 499         # €4.99
    PRICE_PRODUCTS_GUIDE: int = 299      # €2.99
    PRICE_PACK_COMPLETE: int = 599       # €5.99 (colorimetría + guía juntos, ahorra €2 vs separado)
    PRICE_SEASONAL: int = 499            # €4.99
    BARBER_COMMISSION_CENTS: int = 300   # €3.00 (~20% de €14.99)

    # Photo processing
    MAX_PHOTO_SIZE_MB: int = 10
    MIN_FACE_DETECTION_CONFIDENCE: float = 0.70
    MIN_PHOTO_QUALITY_SCORE: float = 0.60
    PHOTO_TEMP_DIR: str = _DEFAULT_PHOTO_TEMP_DIR

    # RGPD - data retention
    METRICS_RETENTION_DAYS: int = 90
    CONSENT_LOG_RETENTION_DAYS: int = 1825  # 5 years (legal requirement)

    # Anti-fraud
    MAX_ANALYSES_PER_PHONE_30D: int = 3
    MAX_BARBER_CODE_USES_PER_PHONE: int = 1

    # Image generation — provider selector
    IMAGE_GEN_PROVIDER: str = "falai"    # openai | falai
    OPENAI_API_KEY: str = ""             # required if IMAGE_GEN_PROVIDER=openai
    FAL_KEY: str = ""          # fal.ai API key — required for virtual try-on
    PEXELS_API_KEY: str = ""   # Pexels API key — free at pexels.com/api, used for barber reference images
    INSTAGRAM_USERNAME: str = ""  # Instagram account for barber reference scraping
    INSTAGRAM_PASSWORD: str = ""  # Instagram password
    # IMAGE_GEN_ENABLED auto-derives from FAL_KEY presence

    # Frontend URL — used to build Stripe success/cancel redirect URLs
    FRONTEND_URL: str = "http://localhost:3000"

    # Resend — transactional emails (payment confirmed, analysis ready, 24h reminder)
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "VISAI <noreply@visai.es>"

    # n8n — marketing sequence (welcome → 48h tip → day7 upsell check → day30 re-engagement)
    N8N_MARKETING_WEBHOOK_URL: str = ""
    # n8n — CRM upsert (crea/actualiza persona en Twenty tras análisis completado)
    N8N_CRM_WEBHOOK_URL: str = ""

    # Admin — Telegram bot for reference photo uploads
    ADMIN_TELEGRAM_BOT_TOKEN: str = ""
    ADMIN_TELEGRAM_ALLOWED_CHAT_IDS: str = ""  # comma-separated chat IDs

    # Barber Telegram bot — weekly reports, trend polls, gamification notifications
    BARBER_TELEGRAM_BOT_TOKEN: str = ""

    # Development bypass — skip Stripe entirely (never use in production)
    DEV_SKIP_PAYMENT: bool = False

    @model_validator(mode="after")
    def _guard_dev_skip_payment(self) -> "Settings":
        if self.DEV_SKIP_PAYMENT and not self.DEBUG:
            _logger.critical(
                "DEV_SKIP_PAYMENT=True in non-DEBUG mode — forcing to False to protect production."
            )
            self.DEV_SKIP_PAYMENT = False
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
