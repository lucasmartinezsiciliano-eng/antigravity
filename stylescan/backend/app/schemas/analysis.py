from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class AnalysisInitiateRequest(BaseModel):
    barber_code: str | None = Field(None, description="Código de barbería colaboradora")
    phone_hash: str | None = Field(None, description="SHA-256 del número de teléfono (para anti-fraude)")
    quiz_answers: dict[str, Any] | None = Field(None, description="Respuestas del quiz previo")
    include_colorimetry: bool = False
    include_products_guide: bool = False


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
    created_at: datetime
    expires_at: datetime
