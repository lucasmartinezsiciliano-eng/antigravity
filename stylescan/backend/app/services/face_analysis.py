"""
VISAI — Face Analysis Service
Uses Google MediaPipe FaceMesh (468 landmarks) to extract facial metrics.

Photo protocol (3 photos):
  1. Frontal (0°)          — Primary. Face shape, proportions, asymmetry, jaw analysis.
  2. Left profile (90°)    — OpenCV silhouette. Cranial depth (AP diameter estimation).
  3. Right profile (90°)   — OpenCV silhouette. Bilateral cranial depth validation.

Why 90° profiles via OpenCV (not MediaPipe):
  MediaPipe FaceMesh accuracy collapses above 45° yaw.
  At 90°, confidence → 0.0 (formula: max(0, 0.90 - (|yaw|-20)/70)).
  Profile photos go through an independent OpenCV pipeline (skin detection +
  largest-contour bounding box) to extract the AP (antero-posterior) diameter.
  Combined with frontal temple width, this gives a cephalic index approximation:
    dolicocéfalo (<75) / mesocéfalo (75-80) / braquicéfalo (>80).
"""

import math
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MediaPipe Tasks API setup (mediapipe >= 0.10)
# ---------------------------------------------------------------------------
_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "face_landmarker.task"
)

def _build_landmarker() -> mp_vision.FaceLandmarker:
    base_options = mp_python.BaseOptions(model_asset_path=os.path.abspath(_MODEL_PATH))
    options = mp_vision.FaceLandmarkerOptions(
        base_options=base_options,
        num_faces=1,
        min_face_detection_confidence=0.60,
        min_face_presence_confidence=0.60,
        min_tracking_confidence=0.50,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=True,
    )
    return mp_vision.FaceLandmarker.create_from_options(options)

# Lazy singleton — created on first use
_landmarker: Optional[mp_vision.FaceLandmarker] = None

def _get_landmarker() -> mp_vision.FaceLandmarker:
    global _landmarker
    if _landmarker is None:
        _landmarker = _build_landmarker()
    return _landmarker

# ---------------------------------------------------------------------------
# Landmark indices — anthropometric reference points
# Reference: MediaPipe FaceMesh 468-point topology
# ---------------------------------------------------------------------------
LM = {
    # Vertical axis
    "forehead":        10,
    "chin":           152,
    "nose_tip":         4,

    # Horizontal (bizygomatic) — cheekbone width
    "left_cheek":     234,
    "right_cheek":    454,

    # Temporal / head width (as close as FaceMesh gets to biparietal)
    "left_temple":    162,
    "right_temple":   389,

    # Mandibular width (jaw angle)
    "left_jaw":       172,
    "right_jaw":      397,

    # Eyes (for IOD normalization and asymmetry)
    "left_eye_outer":  33,
    "right_eye_outer": 263,
    "left_eye_inner":  133,
    "right_eye_inner": 362,

    # Eyebrows (asymmetry)
    "left_brow_outer":  70,
    "right_brow_outer": 300,
    "left_brow_inner":  105,
    "right_brow_inner": 334,

    # Mouth (asymmetry)
    "left_mouth":  61,
    "right_mouth": 291,
    "upper_lip":    0,
    "lower_lip":   17,
}

# Paired landmarks for asymmetry calculation (left_idx, right_idx)
ASYMMETRY_PAIRS = [
    (LM["left_eye_outer"],  LM["right_eye_outer"]),
    (LM["left_eye_inner"],  LM["right_eye_inner"]),
    (LM["left_brow_outer"], LM["right_brow_outer"]),
    (LM["left_brow_inner"], LM["right_brow_inner"]),
    (LM["left_cheek"],      LM["right_cheek"]),
    (LM["left_jaw"],        LM["right_jaw"]),
    (LM["left_temple"],     LM["right_temple"]),
    (LM["left_mouth"],      LM["right_mouth"]),
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class PhotoAnalysis:
    """Metrics extracted from a single frontal/semi-frontal photo via MediaPipe."""
    face_detected: bool
    confidence: float
    head_pose_yaw: float    # Rotation around Y axis (left/right tilt, degrees)
    head_pose_pitch: float  # Rotation around X axis (up/down tilt, degrees)

    # Raw normalized measurements (normalized by interocular distance)
    face_length: float = 0.0
    face_width: float = 0.0        # Bizygomatic (cheekbone to cheekbone)
    forehead_width: float = 0.0    # Temple to temple
    jaw_width: float = 0.0         # Jaw angle to jaw angle

    # Derived ratios
    length_width_ratio: float = 0.0
    forehead_to_face_ratio: float = 0.0
    jaw_to_face_ratio: float = 0.0

    # Asymmetry (0 = perfect symmetry, 1 = maximum)
    asymmetry_score: float = 0.0
    asymmetry_details: dict = field(default_factory=dict)


@dataclass
class FaceMetrics:
    """
    Aggregated, definitive facial metrics from all valid photos.
    This is what gets stored in the database and sent to Claude.
    """
    face_shape: str               # oval, round, square, oblong, heart, diamond, triangle
    cranial_proportion: str       # balanced, elongated, wide (drives illustration archetype)
    face_length: float
    face_width: float
    forehead_width: float
    jaw_width: float
    length_width_ratio: float
    forehead_to_face_ratio: float
    jaw_to_face_ratio: float
    asymmetry_score: float
    asymmetry_description: str    # Human-readable asymmetry assessment
    photos_used: int
    confidence: float             # Overall confidence 0.0–1.0
    analysis_notes: list[str] = field(default_factory=list)
    # Cephalic classification from 90° profile silhouettes (None if no profiles provided)
    cephalic_type: Optional[str] = None  # "dolicocéfalo" | "mesocéfalo" | "braquicéfalo"


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------
def _euclidean(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def _lm_point(landmark, idx: int, w: int, h: int) -> tuple[float, float]:
    lm = landmark[idx]
    return (lm.x * w, lm.y * h)


def _estimate_head_pose(landmarks, w: int, h: int) -> tuple[float, float]:
    """
    Estimate head yaw (left/right) and pitch (up/down) from facial landmark geometry.
    Returns (yaw_degrees, pitch_degrees).
    Positive yaw = face turned right. Positive pitch = chin up.
    """
    nose = _lm_point(landmarks, LM["nose_tip"], w, h)
    left_cheek = _lm_point(landmarks, LM["left_cheek"], w, h)
    right_cheek = _lm_point(landmarks, LM["right_cheek"], w, h)
    forehead = _lm_point(landmarks, LM["forehead"], w, h)
    chin = _lm_point(landmarks, LM["chin"], w, h)

    # Yaw: asymmetry between nose-to-left-cheek vs nose-to-right-cheek distances
    d_left = _euclidean(nose, left_cheek)
    d_right = _euclidean(nose, right_cheek)
    if d_left + d_right > 0:
        yaw_ratio = (d_right - d_left) / (d_left + d_right)
        yaw_deg = yaw_ratio * 90  # Approximate mapping
    else:
        yaw_deg = 0.0

    # Pitch: ratio of upper face height vs lower face height
    face_mid_y = (forehead[1] + chin[1]) / 2
    upper = abs(face_mid_y - forehead[1])
    lower = abs(chin[1] - face_mid_y)
    if upper + lower > 0:
        pitch_ratio = (lower - upper) / (upper + lower)
        pitch_deg = pitch_ratio * 45
    else:
        pitch_deg = 0.0

    return round(yaw_deg, 1), round(pitch_deg, 1)


def _calculate_asymmetry(landmarks, w: int, h: int) -> tuple[float, dict]:
    """
    Calculate facial asymmetry by comparing paired landmarks against the facial midline.
    Returns (overall_score, detail_dict).
    Score: 0.0 = perfect symmetry, 1.0 = extreme asymmetry.
    Most faces fall between 0.05 and 0.20.
    """
    midline_x = (
        _lm_point(landmarks, LM["left_eye_outer"], w, h)[0]
        + _lm_point(landmarks, LM["right_eye_outer"], w, h)[0]
    ) / 2

    scores = {}
    for left_idx, right_idx in ASYMMETRY_PAIRS:
        lp = _lm_point(landmarks, left_idx, w, h)
        rp = _lm_point(landmarks, right_idx, w, h)

        ld = abs(lp[0] - midline_x)
        rd = abs(rp[0] - midline_x)

        horizontal_asym = abs(ld - rd) / max((ld + rd) / 2, 1e-6)
        vertical_asym = abs(lp[1] - rp[1]) / max(_euclidean(lp, rp), 1e-6)

        pair_score = min((horizontal_asym * 0.7 + vertical_asym * 0.3), 1.0)
        pair_name = f"pair_{left_idx}_{right_idx}"
        scores[pair_name] = round(pair_score, 3)

    overall = float(np.mean(list(scores.values()))) if scores else 0.0
    return round(overall, 3), scores


def _classify_face_shape(lwr: float, fr: float, jr: float) -> str:
    """
    Classify face shape from three key ratios.

    lwr = face_length / face_width (cheekbone)
    fr  = forehead_width / face_width
    jr  = jaw_width / face_width

    Classification boundaries validated against published morphometric studies.
    """
    if lwr > 1.78:
        return "oblong"

    if lwr < 1.28:
        return "round"

    # Intermediate range (1.28 – 1.78)
    forehead_jaw_diff = fr - jr

    if 1.28 <= lwr < 1.50:
        if abs(fr - 1.0) < 0.10 and abs(jr - 1.0) < 0.10:
            return "square"
        if forehead_jaw_diff < -0.12:      # jaw notably wider than forehead
            return "triangle"
        if forehead_jaw_diff > 0.18:       # forehead notably wider than jaw
            return "heart"
        return "round"                     # soft proportions, short-ish

    # 1.50 – 1.78
    if abs(fr - jr) < 0.08 and abs(fr - 1.0) < 0.10:
        return "oval"
    if forehead_jaw_diff > 0.15:
        return "heart"
    if abs(fr - 1.0) < 0.08 and abs(jr - 1.0) < 0.08 and fr < 0.92:
        return "diamond"
    return "oval"


def _cranial_proportion_from_lwr(lwr: float) -> str:
    """
    Fallback cranial proportion estimate from frontal lwr (no profile photos).
    Returns 'elongated' / 'balanced' / 'wide'. Less accurate than profile silhouette.
    """
    if lwr > 1.65:
        return "elongated"
    if lwr < 1.30:
        return "wide"
    return "balanced"


def _asymmetry_description(score: float) -> str:
    if score < 0.06:
        return "Simetría facial excelente. Tu rostro presenta proporciones muy equilibradas entre ambos lados."
    if score < 0.12:
        return "Simetría facial buena con una ligera asimetría natural (prácticamente imperceptible)."
    if score < 0.20:
        return "Asimetría facial moderada y completamente normal. La gran mayoría de las personas la tienen."
    return "Asimetría facial notable. Esto se tendrá en cuenta en las recomendaciones de corte para crear equilibrio visual."


# ---------------------------------------------------------------------------
# Profile silhouette analysis (90° photos — OpenCV pipeline)
# ---------------------------------------------------------------------------
def _analyze_profile_silhouette(image_bytes: bytes) -> Optional[float]:
    """
    Extract the antero-posterior depth / cranial height ratio from a 90° profile photo.

    Method: YCrCb skin detection → morphological cleanup → largest contour bounding box.
    Returns (bounding_width / bounding_height) or None if extraction fails.

    Interpretation:
      High ratio → long AP diameter relative to height → dolicocéfalo tendency.
      Low ratio  → short AP diameter (round skull) → braquicéfalo tendency.
    """
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    h, w = img.shape[:2]

    # YCrCb skin detection — more robust than HSV across diverse skin tones and lighting
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    lower = np.array([0, 133, 77], dtype=np.uint8)
    upper = np.array([255, 173, 127], dtype=np.uint8)
    skin_mask = cv2.inRange(ycrcb, lower, upper)

    # Close small holes within skin region; remove isolated noise patches
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    # Require at least 3% of image area — filters noise but handles close-up portraits
    if cv2.contourArea(largest) < h * w * 0.03:
        return None

    x, y, cw, ch = cv2.boundingRect(largest)
    if ch < 20:
        return None

    return round(cw / ch, 3)


def _classify_cephalic_type(depth_height_ratio: float) -> str:
    """
    Classify cranial morphology from profile silhouette depth/height ratio.

    Standard cephalic index (CI) = (biparietal / AP-diameter) × 100.
    From profile photo, width ≈ AP diameter, height ≈ cranial height.
    Large AP relative to height → dolicocéfalo (CI < 75, narrow/long skull).
    Small AP relative to height → braquicéfalo (CI > 80, wide/round skull).

    Thresholds calibrated on average head proportions:
      AP ≈ 18-22 cm, cranial height ≈ 22-24 cm → typical ratio 0.75-0.90.
    """
    if depth_height_ratio > 0.86:
        return "dolicocéfalo"
    if depth_height_ratio < 0.72:
        return "braquicéfalo"
    return "mesocéfalo"


# ---------------------------------------------------------------------------
# Single-photo analysis (MediaPipe — frontal/semi-frontal)
# ---------------------------------------------------------------------------
def analyze_single_photo(image_bytes: bytes) -> PhotoAnalysis:
    """
    Extract facial metrics from one image using MediaPipe Tasks API.
    Returns PhotoAnalysis with face_detected=False if no face is found or yaw > 45°.
    For 90° profiles, call _analyze_profile_silhouette() instead.
    """
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return PhotoAnalysis(
            face_detected=False, confidence=0.0,
            head_pose_yaw=0.0, head_pose_pitch=0.0
        )

    h, w = img.shape[:2]
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    landmarker = _get_landmarker()
    result = landmarker.detect(mp_image)

    if not result.face_landmarks:
        return PhotoAnalysis(
            face_detected=False, confidence=0.0,
            head_pose_yaw=0.0, head_pose_pitch=0.0
        )

    raw_lms = result.face_landmarks[0]

    class _LM:
        def __init__(self, lm):
            self.x = lm.x
            self.y = lm.y
            self.z = lm.z

    lms = [_LM(lm) for lm in raw_lms]

    yaw, pitch = _estimate_head_pose(lms, w, h)
    if result.facial_transformation_matrixes:
        import math as _math
        mat = result.facial_transformation_matrixes[0].data
        try:
            yaw = _math.degrees(_math.atan2(mat[2][0], mat[0][0]))
            pitch = _math.degrees(_math.atan2(-mat[1][2], mat[1][1]))
        except Exception:
            pass  # Fall back to geometry-based estimate

    iod = _euclidean(
        _lm_point(lms, LM["left_eye_outer"], w, h),
        _lm_point(lms, LM["right_eye_outer"], w, h),
    )
    if iod < 1:
        return PhotoAnalysis(
            face_detected=False, confidence=0.0,
            head_pose_yaw=yaw, head_pose_pitch=pitch
        )

    face_length    = _euclidean(_lm_point(lms, LM["forehead"], w, h), _lm_point(lms, LM["chin"], w, h)) / iod
    face_width     = _euclidean(_lm_point(lms, LM["left_cheek"], w, h), _lm_point(lms, LM["right_cheek"], w, h)) / iod
    forehead_width = _euclidean(_lm_point(lms, LM["left_temple"], w, h), _lm_point(lms, LM["right_temple"], w, h)) / iod
    jaw_width      = _euclidean(_lm_point(lms, LM["left_jaw"], w, h), _lm_point(lms, LM["right_jaw"], w, h)) / iod

    lwr = face_length / max(face_width, 0.01)
    fr  = forehead_width / max(face_width, 0.01)
    jr  = jaw_width / max(face_width, 0.01)

    asym_score, asym_details = _calculate_asymmetry(lms, w, h)

    # Confidence: penalize yaw > 20° (landmarks become unreliable above that)
    yaw_penalty = max(0.0, abs(yaw) - 20) / 70
    confidence = max(0.0, min(1.0, 0.90 - yaw_penalty))

    return PhotoAnalysis(
        face_detected=True,
        confidence=round(confidence, 2),
        head_pose_yaw=yaw,
        head_pose_pitch=pitch,
        face_length=round(face_length, 4),
        face_width=round(face_width, 4),
        forehead_width=round(forehead_width, 4),
        jaw_width=round(jaw_width, 4),
        length_width_ratio=round(lwr, 4),
        forehead_to_face_ratio=round(fr, 4),
        jaw_to_face_ratio=round(jr, 4),
        asymmetry_score=asym_score,
        asymmetry_details=asym_details,
    )


# ---------------------------------------------------------------------------
# Multi-photo aggregation — 3-photo protocol
# ---------------------------------------------------------------------------
def analyze_photos(photos: list[bytes]) -> Optional["FaceMetrics"]:
    """
    Analyze photos using the 3-photo protocol and aggregate into FaceMetrics.

    Protocol:
      Photo 1: Frontal (0°)       → MediaPipe 468 landmarks.
      Photo 2: Left profile (90°) → OpenCV skin silhouette.
      Photo 3: Right profile (90°)→ OpenCV skin silhouette.

    Routing logic:
      - MediaPipe confidence ≥ 0.50 → frontal/semi-frontal path.
      - MediaPipe confidence < 0.50 → profile silhouette path.
      Both profiles contribute to cephalic_type classification.

    Returns None if no frontal photo is usable.
    """
    mediapipe_results: list[PhotoAnalysis] = []
    profile_depth_ratios: list[float] = []

    for i, photo_bytes in enumerate(photos):
        pa = analyze_single_photo(photo_bytes)

        if pa.face_detected and pa.confidence >= 0.50:
            mediapipe_results.append(pa)
        else:
            # Low/zero confidence → likely a 90° profile → try silhouette extraction
            ratio = _analyze_profile_silhouette(photo_bytes)
            if ratio is not None:
                profile_depth_ratios.append(ratio)
                logger.info("Photo %d: profile silhouette depth/height=%.3f", i + 1, ratio)
            else:
                logger.warning(
                    "Photo %d: MediaPipe rejected (detected=%s conf=%.2f) and silhouette failed",
                    i + 1, pa.face_detected, pa.confidence,
                )

    notes: list[str] = []

    if not mediapipe_results:
        logger.error("No usable frontal photo in %d submissions — cannot classify face shape", len(photos))
        return None

    # Primary source = most frontal photo (smallest |yaw|)
    primary = min(mediapipe_results, key=lambda r: abs(r.head_pose_yaw))

    # --- Face width: from the most frontal photo
    face_width = primary.face_width

    # --- LWR: weighted average across all valid frontal photos
    weights = [r.confidence * max(0.1, 1 - abs(r.head_pose_yaw) / 90) for r in mediapipe_results]
    total_w = sum(weights)
    avg_lwr = sum(r.length_width_ratio * w for r, w in zip(mediapipe_results, weights)) / max(total_w, 1e-9)

    # --- Forehead: prefer overhead pitch > 5°; fallback to primary
    overhead = [r for r in mediapipe_results if r.head_pose_pitch > 5]
    forehead_width = overhead[0].forehead_width if overhead else primary.forehead_width

    # --- Jaw: prefer chin-down pitch < -5°; fallback to primary
    chindown = [r for r in mediapipe_results if r.head_pose_pitch < -5]
    jaw_width = chindown[0].jaw_width if chindown else primary.jaw_width

    face_length = avg_lwr * face_width
    fr = forehead_width / max(face_width, 0.01)
    jr = jaw_width / max(face_width, 0.01)

    avg_asymmetry = float(np.mean([r.asymmetry_score for r in mediapipe_results]))

    face_shape = _classify_face_shape(avg_lwr, fr, jr)

    # --- Cranial classification
    cephalic_type: Optional[str] = None
    if profile_depth_ratios:
        avg_depth = float(np.mean(profile_depth_ratios))
        cephalic_type = _classify_cephalic_type(avg_depth)
        # Map to illustration archetype vocabulary
        cranial = {
            "dolicocéfalo": "elongated",
            "braquicéfalo": "wide",
        }.get(cephalic_type, "balanced")
        logger.info(
            "Cephalic type from %d profiles: %s (avg depth/height=%.3f) → cranial=%s",
            len(profile_depth_ratios), cephalic_type, avg_depth, cranial,
        )
    else:
        cranial = _cranial_proportion_from_lwr(avg_lwr)
        notes.append(
            "Proporciones craneales estimadas desde foto frontal (sin perfiles 90° utilizables). "
            "Incluye perfil izquierdo y derecho para clasificación precisa (dolicocéfalo/mesocéfalo/braquicéfalo)."
        )

    avg_confidence = float(np.mean([r.confidence for r in mediapipe_results]))
    if avg_confidence < 0.70:
        notes.append(
            f"Confianza del análisis: {avg_confidence:.0%}. "
            "Para mejores resultados, asegúrate de buena iluminación y cara sin obstrucciones."
        )

    return FaceMetrics(
        face_shape=face_shape,
        cranial_proportion=cranial,
        cephalic_type=cephalic_type,
        face_length=round(face_length, 3),
        face_width=round(face_width, 3),
        forehead_width=round(forehead_width, 3),
        jaw_width=round(jaw_width, 3),
        length_width_ratio=round(avg_lwr, 3),
        forehead_to_face_ratio=round(fr, 3),
        jaw_to_face_ratio=round(jr, 3),
        asymmetry_score=round(avg_asymmetry, 3),
        asymmetry_description=_asymmetry_description(avg_asymmetry),
        photos_used=len(mediapipe_results) + len(profile_depth_ratios),
        confidence=round(avg_confidence, 2),
        analysis_notes=notes,
    )
