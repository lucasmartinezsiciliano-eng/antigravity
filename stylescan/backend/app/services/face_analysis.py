"""
StyleScan — Face Analysis Service
Uses Google MediaPipe FaceMesh (468 landmarks) to extract facial metrics.

Photo protocol (5 photos):
  1. Frontal (0°)         — Primary measurement. Face shape, proportions, asymmetry.
  2. Left 45°             — Reinforces proportions, depth estimate.
  3. Right 45°            — Bilateral symmetry validation.
  4. Slight overhead      — Camera ~15° above. Head width, hairline.
  5. Chin down (~15°)     — Jaw and chin detail for degradado recommendations.

Why these angles: MediaPipe fails on 90° profiles (>45° confidence collapse).
True cephalic index requires 3D scanning. We deliver estimated cranial proportions,
not medical skull classification — stated clearly in the report.
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
    """Metrics extracted from a single photo."""
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
    cranial_proportion: str       # balanced, elongated, wide
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
    analysis_notes: list[str]     # Notes for Claude (e.g., limited confidence reasons)


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


def _cranial_proportion(lwr: float, fr: float = 0.0) -> str:  # noqa: ARG001
    """
    Estimate cranial proportion tendency from frontal photo ratios.
    DISCLAIMER: True cephalic index requires 3D measurement (CT/photogrammetry).
    This is an approximation from frontal geometry.
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
# Single-photo analysis
# ---------------------------------------------------------------------------
def analyze_single_photo(image_bytes: bytes) -> PhotoAnalysis:
    """
    Extract facial metrics from one image (bytes) using MediaPipe Tasks API.
    Returns PhotoAnalysis with face_detected=False if no face is found.
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

    # Tasks API returns NormalizedLandmark objects directly (x, y, z in [0,1])
    # Wrap them to be compatible with our _lm_point / _estimate_head_pose helpers
    raw_lms = result.face_landmarks[0]

    class _LM:
        def __init__(self, lm):
            self.x = lm.x
            self.y = lm.y
            self.z = lm.z

    lms = [_LM(lm) for lm in raw_lms]

    # Extract yaw/pitch from facial transformation matrix if available
    yaw, pitch = _estimate_head_pose(lms, w, h)
    if result.facial_transformation_matrixes:
        import math as _math
        mat = result.facial_transformation_matrixes[0].data
        # Rotation matrix row 0 and 2 give yaw; row 1 gives pitch
        try:
            yaw = _math.degrees(_math.atan2(mat[2][0], mat[0][0]))
            pitch = _math.degrees(_math.atan2(-mat[1][2], mat[1][1]))
        except Exception:
            pass  # Fall back to geometry-based estimate

    # Interocular distance as normalization baseline
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

    # Confidence: penalize extreme yaw (off-angle reduces reliability)
    yaw_penalty = max(0.0, abs(yaw) - 20) / 70  # Starts penalizing after 20°
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
# Multi-photo aggregation
# ---------------------------------------------------------------------------
def analyze_photos(photos: list[bytes]) -> Optional[FaceMetrics]:
    """
    Analyze 1–5 photos and aggregate into definitive FaceMetrics.

    Strategy:
    - Frontal (lowest |yaw|) = primary source for all measurements.
    - 45° photos = reinforce length/width ratio via weighted average.
    - Overhead photo = refines forehead width estimate.
    - Chin-down photo = refines jaw width estimate.
    - Asymmetry = averaged across all valid photos.

    Returns None if no photo yields a valid face detection.
    """
    results: list[PhotoAnalysis] = []
    for photo_bytes in photos:
        pa = analyze_single_photo(photo_bytes)
        if pa.face_detected and pa.confidence >= 0.50:
            results.append(pa)
        else:
            logger.warning(
                "Photo rejected: detected=%s confidence=%.2f",
                pa.face_detected, pa.confidence
            )

    if not results:
        return None

    notes: list[str] = []

    # Primary = most frontal (smallest |yaw|)
    primary = min(results, key=lambda r: abs(r.head_pose_yaw))

    if len(results) == 1:
        notes.append("Solo se procesó 1 foto válida. La precisión es menor que con el protocolo completo de 5 fotos.")

    # --- Face width: from the most frontal photo (yaw closest to 0°)
    face_width = primary.face_width

    # --- Face length: weighted average by confidence × (1 - yaw_penalty)
    weights = [r.confidence * max(0.1, 1 - abs(r.head_pose_yaw) / 90) for r in results]
    total_w = sum(weights)
    avg_lwr = sum(r.length_width_ratio * w for r, w in zip(results, weights)) / max(total_w, 1e-9)

    # --- Forehead: prefer overhead photo (pitch > 5°), fallback to primary
    overhead_candidates = [r for r in results if r.head_pose_pitch > 5]
    forehead_width = (
        overhead_candidates[0].forehead_width if overhead_candidates else primary.forehead_width
    )

    # --- Jaw: prefer chin-down photo (pitch < -5°), fallback to primary
    chindown_candidates = [r for r in results if r.head_pose_pitch < -5]
    jaw_width = (
        chindown_candidates[0].jaw_width if chindown_candidates else primary.jaw_width
    )

    face_length = avg_lwr * face_width

    fr = forehead_width / max(face_width, 0.01)
    jr = jaw_width / max(face_width, 0.01)

    # --- Asymmetry: mean across all valid photos
    avg_asymmetry = float(np.mean([r.asymmetry_score for r in results]))

    # --- Face shape and cranial proportion
    face_shape = _classify_face_shape(avg_lwr, fr, jr)
    cranial    = _cranial_proportion(avg_lwr, fr)

    # --- Overall confidence
    avg_confidence = float(np.mean([r.confidence for r in results]))
    if avg_confidence < 0.70:
        notes.append(
            f"Confianza media del análisis: {avg_confidence:.0%}. "
            "Para mejores resultados, asegúrate de buena iluminación y cara sin obstrucciones."
        )

    return FaceMetrics(
        face_shape=face_shape,
        cranial_proportion=cranial,
        face_length=round(face_length, 3),
        face_width=round(face_width, 3),
        forehead_width=round(forehead_width, 3),
        jaw_width=round(jaw_width, 3),
        length_width_ratio=round(avg_lwr, 3),
        forehead_to_face_ratio=round(fr, 3),
        jaw_to_face_ratio=round(jr, 3),
        asymmetry_score=round(avg_asymmetry, 3),
        asymmetry_description=_asymmetry_description(avg_asymmetry),
        photos_used=len(results),
        confidence=round(avg_confidence, 2),
        analysis_notes=notes,
    )
