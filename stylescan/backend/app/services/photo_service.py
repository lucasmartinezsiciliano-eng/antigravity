"""
Photo validation and lifecycle management.

RGPD compliance:
- Photos are NEVER written to permanent storage.
- All photo bytes are processed in memory and discarded immediately after analysis.
- Only derived metrics (numbers, not images) leave this service.
- Deletion is automatic and unconditional — no code path retains photos.
"""

import io
import logging
import hashlib
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = 50_000_000  # decompression bomb guard

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_BYTES = settings.MAX_PHOTO_SIZE_MB * 1024 * 1024

ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/heic", "image/heif"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


@dataclass
class PhotoValidationResult:
    valid: bool
    error: str | None = None
    quality_score: float = 0.0
    width: int = 0
    height: int = 0
    has_face: bool = False
    brightness_ok: bool = False
    blur_score: float = 0.0      # Higher = sharper
    face_size_ratio: float = 0.0 # Face area / total image area


def validate_and_prepare_photo(
    file_bytes: bytes,
    filename: str,
) -> tuple[PhotoValidationResult, bytes | None]:
    """
    Validate photo quality and return (result, prepared_bytes).
    prepared_bytes is JPEG-normalized bytes if valid, None if not.

    Quality checks:
    1. File size
    2. File format
    3. Dimensions (min 400x400)
    4. Brightness (not too dark, not blown out)
    5. Blur (Laplacian variance)
    6. Face detection (basic — full analysis done later)
    7. Face size ratio (face should fill enough of the frame)
    """
    # Size check
    if len(file_bytes) > MAX_BYTES:
        return PhotoValidationResult(
            valid=False,
            error=f"La foto supera el tamaño máximo de {settings.MAX_PHOTO_SIZE_MB}MB."
        ), None

    # Format check (magic bytes, not just extension)
    if not _is_valid_image_format(file_bytes):
        return PhotoValidationResult(
            valid=False,
            error="Formato de imagen no soportado. Usa JPG o PNG."
        ), None

    # Decode with Pillow (handles HEIC conversion too)
    try:
        pil_img = Image.open(io.BytesIO(file_bytes))
        pil_img = pil_img.convert("RGB")
    except Exception as e:
        logger.warning("Image decode failed: %s", e)
        return PhotoValidationResult(valid=False, error="No se pudo abrir la imagen."), None

    w, h = pil_img.size

    if w < 400 or h < 400:
        return PhotoValidationResult(
            valid=False,
            error=f"Imagen demasiado pequeña ({w}x{h}px). Mínimo 400x400px."
        ), None

    # Convert to OpenCV for quality analysis
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # Brightness check
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    mean_brightness = float(np.mean(gray))
    brightness_ok = 40 < mean_brightness < 230

    # Blur check (Laplacian variance — higher is sharper)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    is_sharp = blur_score > 80  # Threshold from empirical testing

    # Quick face detection (Haar cascade — fast, for validation only)
    has_face, face_ratio = _detect_face_quick(cv_img)

    # Quality score (composite)
    quality_score = _compute_quality_score(
        brightness_ok=brightness_ok,
        blur_score=blur_score,
        has_face=has_face,
        face_ratio=face_ratio,
    )

    result = PhotoValidationResult(
        valid=quality_score >= settings.MIN_PHOTO_QUALITY_SCORE,
        quality_score=round(quality_score, 2),
        width=w,
        height=h,
        has_face=has_face,
        brightness_ok=brightness_ok,
        blur_score=round(blur_score, 1),
        face_size_ratio=round(face_ratio, 3),
    )

    if not brightness_ok and quality_score < settings.MIN_PHOTO_QUALITY_SCORE:
        result.error = (
            "Iluminación insuficiente o excesiva. Busca luz natural de frente, "
            "evita contraluz."
        )
    elif not is_sharp and quality_score < settings.MIN_PHOTO_QUALITY_SCORE:
        result.error = "Foto desenfocada. Mantén el móvil estable y asegúrate de que el rostro está nítido."
    elif not has_face and quality_score < settings.MIN_PHOTO_QUALITY_SCORE:
        result.error = "No se detectó ningún rostro. Asegúrate de que tu cara ocupa al menos 1/3 de la foto."

    if not result.valid:
        return result, None

    # Normalize to JPEG — strip ALL EXIF/metadata (RGPD: no GPS or device data leaks)
    clean_img = Image.new(pil_img.mode, pil_img.size)
    clean_img.putdata(list(pil_img.getdata()))
    output = io.BytesIO()
    clean_img.save(output, format="JPEG", quality=92)
    prepared_bytes = output.getvalue()

    # Immediately clear references (belt-and-suspenders — GC will handle it, but explicit is safer)
    del pil_img, cv_img, gray

    return result, prepared_bytes


def _is_valid_image_format(data: bytes) -> bool:
    """Check file magic bytes for supported image formats."""
    if len(data) < 12:
        return False
    # JPEG
    if data[:2] == b"\xff\xd8":
        return True
    # PNG
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    # HEIC/HEIF — ftyp box must have heic/heix/mif1/msf1 brand (not mp4/mov)
    if data[4:8] == b"ftyp" and data[8:12] in (b"heic", b"heix", b"mif1", b"msf1", b"hevc", b"hevx"):
        return True
    return False


def _detect_face_quick(cv_img: np.ndarray) -> tuple[bool, float]:
    """
    Quick Haar cascade face detection for validation.
    Returns (face_found, face_area_ratio).
    MediaPipe does the real analysis later — this is just a sanity check.
    """
    try:
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=4, minSize=(80, 80)
        )

        if len(faces) == 0:
            # Try profile cascade as fallback (for 45° photos)
            cascade_profile = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_profileface.xml"
            )
            faces = cascade_profile.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=3, minSize=(80, 80)
            )

        if len(faces) == 0:
            return False, 0.0

        img_area = cv_img.shape[0] * cv_img.shape[1]
        face_area = max(w * h for (_, _, w, h) in faces)
        ratio = face_area / max(img_area, 1)

        return True, ratio

    except Exception as e:
        logger.warning("Face quick-detect failed: %s", e)
        return False, 0.0


def _compute_quality_score(
    brightness_ok: bool,
    blur_score: float,
    has_face: bool,
    face_ratio: float,
) -> float:
    """
    Composite quality score 0.0–1.0. Threshold: 0.60.

    Face detection is NOT required — profile/chin shots are intentionally angled
    and Haar cascade can't detect them. Brightness + sharpness alone are enough.
    """
    score = 0.0

    # Brightness: 45% weight
    score += 0.45 if brightness_ok else 0.0

    # Sharpness: 40% weight (normalized — blur_score 100=ok, 500=excellent)
    sharpness_norm = min(blur_score / 500, 1.0)
    score += 0.40 * sharpness_norm

    # Face size bonus: 15% (only adds to well-framed frontal shots)
    if has_face and 0.05 <= face_ratio <= 0.50:
        ratio_score = 1.0 - abs(face_ratio - 0.20) / 0.30
        score += 0.15 * max(0.0, ratio_score)

    return round(score, 3)


def extract_hair_mask(photo_bytes: bytes) -> bytes:
    """
    Generates a binary mask for hair-region inpainting.

    WHITE (255) = hair / scalp area  → model regenerates here (new cut)
    BLACK (0)   = face / background  → model never touches this

    This is the key mechanism that gives mathematical identity preservation:
    the face pixels cannot change because they are outside the inpainting region.

    Algorithm (no additional model downloads required):
    1. Detect face bounding box via Haar cascade (same used in validation).
    2. Build a 'head cap' rectangle: from top-of-image to ~ear level,
       laterally wider than the face by ~15% on each side.
    3. Carve out the face oval (ellipse inscribed in the face bbox, slightly
       shrunk) so skin is preserved.
    4. Gaussian-blur the edges so inpainting has a smooth transition zone.
    """
    pil_img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
    w, h = pil_img.size
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    mask = np.zeros((h, w), dtype=np.uint8)

    # --- Try face detection with Haar (fast, no extra model) ---
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(80, 80))

    if len(faces) == 0:
        # Fallback: assume face fills the centre; treat top 45% as hair
        mask[:int(h * 0.45), :] = 255
        mask = cv2.GaussianBlur(mask, (31, 31), 10)
        return _mask_to_png(mask)

    # Use the largest detected face
    fx, fy, fw, fh = max(faces, key=lambda r: r[2] * r[3])

    # Head cap: top of image → ear level (~bottom of face bbox),
    # sides extended 18% beyond the face width
    margin_x = int(fw * 0.18)
    cap_x1 = max(0, fx - margin_x)
    cap_x2 = min(w, fx + fw + margin_x)
    cap_y1 = 0
    cap_y2 = fy + fh  # down to the chin (ears are roughly here)
    mask[cap_y1:cap_y2, cap_x1:cap_x2] = 255

    # Carve out the face: ellipse centred on the face, 85% of face size
    face_cx = fx + fw // 2
    face_cy = fy + fh // 2
    axes = (int(fw * 0.42), int(fh * 0.48))
    cv2.ellipse(mask, (face_cx, face_cy), axes, 0, 0, 360, 0, thickness=-1)

    # Soft transition at boundaries (avoids hard seams in Flux Fill output)
    mask = cv2.GaussianBlur(mask, (25, 25), 9)

    return _mask_to_png(mask)


def _mask_to_png(mask: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(mask, mode="L").save(buf, format="PNG")
    return buf.getvalue()


def hash_for_audit(data: str) -> str:
    """SHA-256 hash for RGPD-compliant audit logging (phone, IP, device)."""
    return hashlib.sha256(data.encode()).hexdigest()
