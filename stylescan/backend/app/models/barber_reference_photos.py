from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from app.core.database import Base


class HaircutType(str, Enum):
    """Haircut types that barbero can upload references for. Updated 2026."""
    # Fades
    SKIN_FADE = "skin_fade"
    LOW_FADE = "low_fade"
    MID_FADE = "mid_fade"
    HIGH_FADE = "high_fade"
    DROP_FADE = "drop_fade"
    BURST_FADE = "burst_fade"
    BLOWOUT_FADE = "blowout_fade"    # Nuevo 2026: textura hacia afuera, mucho volumen
    # Tapers & crops
    TAPER = "taper"
    FRENCH_CROP = "french_crop"
    TEXTURED_CROP = "textured_crop"
    EDGAR_CUT = "edgar_cut"          # Nuevo 2026: corte recto + fade, viral 18-24
    CAESAR = "caesar"
    BUZZ_CUT = "buzz_cut"
    CREW_CUT = "crew_cut"
    # Styled tops
    QUIFF = "quiff"
    POMPADOUR = "pompadour"
    SLICK_BACK = "slick_back"
    UNDERCUT = "undercut"
    CURTAINS = "curtains"
    WOLF_CUT = "wolf_cut"
    MODERN_MULLET = "modern_mullet"
    MOHAWK = "mohawk"
    AFRO_TAPER = "afro_taper"
    BRO_FLOW = "bro_flow"            # Nuevo 2026: pelo largo con movimiento, sport/surf


class PhotoAngle(str, Enum):
    """
    Photo angle for barber reference photos.

    FRONTAL : Front-facing photo of the haircut — shows the top, fringe, and
              overall shape. Face visible. Primary reference for Flux Kontext.
    LATERAL : 90-degree side profile — shows the fade/taper graduation, side
              length, and skull shape. Face partially visible.
    """
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

    Angle requirements per haircut type:
      - frontal (MANDATORY): front-facing shot showing the full cut shape.
      - lateral (MANDATORY): 90-degree side profile showing the graduation.

    Photos are NEVER exposed to clients. Used internally as reference_image_url
    for Flux Kontext LoRA Inpaint — the model copies the cut style onto the
    client's head. Only the generated output (client face + new hair) is returned.
    Identity isolation is handled via the mask + prompt, not by avoiding faces.
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
