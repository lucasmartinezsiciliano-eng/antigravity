from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, model_validator

_MAX_QUIZ_STR = 500   # max chars per free-text quiz field
_MAX_QUIZ_KEYS = 30   # max number of quiz keys


class AnalysisInitiateRequest(BaseModel):
    barber_code: str | None = Field(None, description="Código de barbería colaboradora")
    phone_hash: str | None = Field(None, description="SHA-256 del número de teléfono (para anti-fraude)")
    quiz_answers: dict[str, Any] | None = Field(None, description="Respuestas del quiz previo")

    @model_validator(mode="after")
    def _sanitize_quiz(self) -> "AnalysisInitiateRequest":
        if not self.quiz_answers:
            return self
        if len(self.quiz_answers) > _MAX_QUIZ_KEYS:
            raise ValueError(f"quiz_answers: máximo {_MAX_QUIZ_KEYS} campos.")
        sanitized: dict[str, Any] = {}
        for k, v in self.quiz_answers.items():
            if isinstance(v, str) and len(v) > _MAX_QUIZ_STR:
                raise ValueError(f"quiz_answers[{k!r}]: máximo {_MAX_QUIZ_STR} caracteres.")
            sanitized[k] = v
        self.quiz_answers = sanitized
        return self
    include_colorimetry: bool = False
    include_products_guide: bool = False
    marketing_consent: bool = Field(False, description="RGPD: consentimiento explícito para comunicaciones comerciales por email")


class AnalysisInitiateResponse(BaseModel):
    analysis_id: str
    checkout_url: str
    amount_euros: float
    discount_applied: bool


class ConsentRequest(BaseModel):
    consented_biometric_processing: bool
    consented_special_category_data: bool
    consented_retention_90_days: bool
    consented_immediate_photo_deletion: bool
    consented_age_verification: bool
    consent_text_hash: str = Field(..., description="SHA-256 del texto de consentimiento mostrado")
    device_fingerprint_hash: str | None = None


class UpsellRequest(BaseModel):
    upsell_type: str = Field(..., description="'colorimetry' | 'products' | 'pack'")


class UpsellResponse(BaseModel):
    checkout_url: str
    analysis_id: str
    upsell_type: str
    amount_euros: float


class AnalysisResult(BaseModel):
    analysis_id: str
    face_shape: str
    cranial_proportion: str
    asymmetry_score: float
    confidence: float
    photos_analyzed: int
    report: dict[str, Any]
    includes_colorimetry: bool
    colorimetry_report: dict | None
    includes_products_guide: bool
    products_guide: dict | None
    includes_seasonal: bool = False
    seasonal_report: dict | None = None
    created_at: datetime
    expires_at: datetime
