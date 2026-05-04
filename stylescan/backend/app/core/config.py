from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "StyleScan API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./stylescan.db"

    # Anthropic
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-haiku-4-5-20251001"
    CLAUDE_MAX_TOKENS: int = 4096

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_BASE_COUPON_ID: str = ""  # Created once, all barber codes reference it

    # Pricing (in cents)
    PRICE_BASE_ANALYSIS: int = 599       # €5.99
    PRICE_COLORIMETRY: int = 249         # €2.49
    PRICE_PRODUCTS_GUIDE: int = 199      # €1.99
    PRICE_PACK_COMPLETE: int = 349       # €3.49
    BARBER_COMMISSION_CENTS: int = 100   # €1.00

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

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
