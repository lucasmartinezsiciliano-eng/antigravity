from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from app.core.database import Base


class HaircutType(str, Enum):
    """Haircut types that barbero can upload references for."""
    FADE = "fade"
    SKIN_FADE = "skin_fade"
    ZERO_FADE = "zero_fade"
    LOW_FADE = "low_fade"
    MID_FADE = "mid_fade"
    HIGH_FADE = "high_fade"
    DROP_FADE = "drop_fade"
    TAPER = "taper"
    FRENCH_CROP = "french_crop"
    QUIFF = "quiff"
    POMPADOUR = "pompadour"
    SLICK_BACK = "slick_back"
    UNDERCUT = "undercut"
    MODERN_MULLET = "modern_mullet"
    MOHAWK = "mohawk"
    CAESAR = "caesar"
    BUZZ_CUT = "buzz_cut"
    CREW_CUT = "crew_cut"


class PhotoAngle(str, Enum):
    """Photo angle perspective."""
    FRONTAL = "frontal"
    LATERAL = "lateral"


class PhotoValidationStatus(str, Enum):
    """Validation status of reference photo."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class BarberReferencePhoto(Base):
    """
    Reference photos uploaded by barbero for each haircut type.
    Each haircut requires 1 frontal + 1 lateral photo.
    Photos are analyzed with MediaPipe to extract cut parameters,
    then used as reference data for image generation (not shown to clients).
    """
    __tablename__ = "barber_reference_photos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Foreign key
    barber_partner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("barber_partners.id"), index=True
    )

    # Photo metadata
    haircut_type: Mapped[str] = mapped_column(SQLEnum(HaircutType))
    photo_angle: Mapped[str] = mapped_column(SQLEnum(PhotoAngle))

    # Storage
    cloudinary_url: Mapped[str] = mapped_column(String(500))
    cloudinary_public_id: Mapped[str] = mapped_column(String(255), nullable=True)

    # Extracted parameters from MediaPipe analysis
    extracted_parameters: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    # Stored as JSON string: {transition_line_mm, blend_angle_degrees, top_length_mm, side_length_mm, volume_percentage, line_sharpness, weight_distribution}

    face_shape_in_photo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # oval, round, square, oblong, heart, diamond, triangle - detected from photo

    cephalic_type_in_photo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # dolicocéfalo, mesocéfalo, braquicéfalo - detected from profile

    quality_score: Mapped[float | None] = mapped_column(nullable=True)
    # 0.0-1.0, confidence of MediaPipe extraction

    # Validation
    validation_status: Mapped[str] = mapped_column(
        SQLEnum(PhotoValidationStatus),
        default=PhotoValidationStatus.PENDING
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Rejection handling
    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Bad angle, Poor lighting, Not a real haircut, Quality too low, etc.

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationship
    barber_partner: Mapped["BarberPartner"] = relationship(back_populates="reference_photos")  # noqa: F821
