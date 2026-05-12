from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "VISAI API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./knowledge_base/stylescan.db"

    # LLM Provider — switch without touching code
    # Values: anthropic | deepseek | gemini
    LLM_PROVIDER: str = "deepseek"
    LLM_MODEL: str = ""          # empty = use provider default (deepseek-chat / gemini-2.0-flash / claude-haiku-4-5-20251001)
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
    PRICE_COLORIMETRY: int = 249         # €2.49
    PRICE_PRODUCTS_GUIDE: int = 199      # €1.99
    PRICE_PACK_COMPLETE: int = 2499      # €24.99 (completo: todo incluido)
    PRICE_SEASONAL: int = 499            # €4.99
    BARBER_COMMISSION_CENTS: int = 300   # €3.00

    # Photo processing
    MAX_PHOTO_SIZE_MB: int = 10
    MIN_FACE_DETECTION_CONFIDENCE: float = 0.70
    MIN_PHOTO_QUALITY_SCORE: float = 0.60
    PHOTO_TEMP_DIR: str = "/tmp/stylescan"

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

    # Development bypass — skip Stripe entirely (never use in production)
    DEV_SKIP_PAYMENT: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
