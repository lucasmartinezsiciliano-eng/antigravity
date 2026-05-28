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
import threading
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
# MediaPipe FaceLandmarker.detect() is NOT thread-safe. The executor pool uses
# multiple workers, so every call must be serialized through this lock.
_landmarker_lock = threading.Lock()

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

    # Facial thirds (Hallawell visagism)
    "glabella":         9,     # Between eyebrows center (upper→middle third boundary)
    "subnasale":      164,     # Under nose center (middle→lower third boundary)

    # Nose width (alar)
    "left_alar":       48,     # Left nostril wing
    "right_alar":     278,     # Right nostril wing
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

    # Facial thirds (Hallawell)
    upper_third: float = 0.0
    middle_third: float = 0.0
    lower_third: float = 0.0
    thirds_balance: str = ""

    # Eye spacing
    eye_spacing_ratio: float = 0.0
    eye_spacing: str = ""

    # Nose proportions
    nose_width_ratio: float = 0.0
    nose_length_ratio: float = 0.0


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

    # Advanced visagism — Hallawell method
    upper_third: float = 0.0          # Ratio of upper facial third (hairline→brows)
    middle_third: float = 0.0         # Ratio of middle facial third (brows→nose base)
    lower_third: float = 0.0          # Ratio of lower facial third (nose base→chin)
    thirds_balance: str = "balanced"   # balanced | upper_dominant | middle_dominant | lower_dominant
    eye_spacing_ratio: float = 0.0     # Intercanthal / bizygomatic
    eye_spacing: str = "normal"        # close_set | normal | wide_set
    nose_width_ratio: float = 0.0      # Alar width / IOD
    nose_length_ratio: float = 0.0     # Glabella→tip / IOD
    cheekbone_prominence: str = "moderate"  # prominent | moderate | subtle
    golden_ratio_score: float = 0.0    # 0.0–1.0 proximity to φ proportions
    profile_type: Optional[str] = None # convex | straight | concave (from 90° profile)


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


def _calculate_facial_thirds(landmarks, w: int, h: int) -> tuple[float, float, float, str]:
    """
    Rule of thirds (Hallawell): divide face into upper/middle/lower zones.
    Upper: hairline (forehead) → brow line (glabella)
    Middle: brow line → nose base (subnasale)
    Lower: nose base → chin (menton)

    Returns (upper_ratio, middle_ratio, lower_ratio, balance_classification).
    Ideal face: each ≈ 0.333. The hairstyle compensates deviations.
    """
    forehead_y = _lm_point(landmarks, LM["forehead"], w, h)[1]
    # Brow line: average of inner brow + glabella for robustness
    glabella_y = _lm_point(landmarks, LM["glabella"], w, h)[1]
    brow_left_y = _lm_point(landmarks, LM["left_brow_inner"], w, h)[1]
    brow_right_y = _lm_point(landmarks, LM["right_brow_inner"], w, h)[1]
    brow_y = (glabella_y + brow_left_y + brow_right_y) / 3
    subnasale_y = _lm_point(landmarks, LM["subnasale"], w, h)[1]
    chin_y = _lm_point(landmarks, LM["chin"], w, h)[1]

    total = chin_y - forehead_y
    if total <= 0:
        return 0.333, 0.333, 0.334, "balanced"

    upper = (brow_y - forehead_y) / total
    middle = (subnasale_y - brow_y) / total
    lower = (chin_y - subnasale_y) / total

    thirds = [upper, middle, lower]
    deviation = max(thirds) - min(thirds)

    if deviation < 0.06:
        balance = "balanced"
    else:
        max_idx = thirds.index(max(thirds))
        balance = ["upper_dominant", "middle_dominant", "lower_dominant"][max_idx]

    return round(upper, 3), round(middle, 3), round(lower, 3), balance


def _calculate_eye_spacing(landmarks, w: int, h: int, face_width_px: float) -> tuple[float, str]:
    """
    Eye spacing: intercanthal distance relative to bizygomatic width.
    Normal: ~0.28–0.35. Close-set: <0.25. Wide-set: >0.38.
    Affects parting strategy and fringe recommendations.
    """
    inner_left = _lm_point(landmarks, LM["left_eye_inner"], w, h)
    inner_right = _lm_point(landmarks, LM["right_eye_inner"], w, h)
    intercanthal = _euclidean(inner_left, inner_right)
    ratio = intercanthal / max(face_width_px, 1.0)

    if ratio < 0.25:
        classification = "close_set"
    elif ratio > 0.38:
        classification = "wide_set"
    else:
        classification = "normal"

    return round(ratio, 3), classification


def _calculate_nose_proportion(landmarks, w: int, h: int, iod: float) -> tuple[float, float]:
    """
    Nose proportions normalized by interocular distance.
    Returns (nose_width_ratio, nose_length_ratio).
    Width: alar width / IOD.  Length: glabella→nose_tip / IOD.
    """
    left_alar = _lm_point(landmarks, LM["left_alar"], w, h)
    right_alar = _lm_point(landmarks, LM["right_alar"], w, h)
    nose_tip = _lm_point(landmarks, LM["nose_tip"], w, h)
    glabella = _lm_point(landmarks, LM["glabella"], w, h)

    nose_width = _euclidean(left_alar, right_alar) / max(iod, 1.0)
    nose_length = _euclidean(glabella, nose_tip) / max(iod, 1.0)

    return round(nose_width, 3), round(nose_length, 3)


def _calculate_golden_ratio_score(
    lwr: float, upper_t: float, middle_t: float, lower_t: float, eye_ratio: float
) -> float:
    """
    How close this face is to φ (1.618) proportions — benchmark only.
    Returns 0.0 (far from golden) to 1.0 (near-perfect golden ratio).
    Used as context, NOT as a quality judgment.
    """
    PHI = 1.618
    # LWR vs golden ratio (ideal LWR ≈ 1.618)
    lwr_score = max(0.0, 1.0 - abs(lwr - PHI) / PHI)
    # Thirds balance (ideal = 0.333 each)
    thirds_dev = abs(upper_t - 0.333) + abs(middle_t - 0.333) + abs(lower_t - 0.333)
    thirds_score = max(0.0, 1.0 - thirds_dev * 3)
    # Eye spacing (ideal ≈ 0.30)
    eye_score = max(0.0, 1.0 - abs(eye_ratio - 0.30) / 0.30) if eye_ratio > 0 else 0.5

    return round(lwr_score * 0.4 + thirds_score * 0.4 + eye_score * 0.2, 3)


def _classify_cheekbone_prominence(fr: float, jr: float) -> str:
    """
    Cheekbone prominence: how much bizygomatic width exceeds forehead and jaw.
    If both forehead and jaw are notably narrower than cheekbones → prominent.
    """
    avg_narrowness = (fr + jr) / 2
    if avg_narrowness < 0.90:
        return "prominent"
    if avg_narrowness < 0.97:
        return "moderate"
    return "subtle"


def _analyze_profile_type(image_bytes: bytes) -> Optional[str]:
    """
    Classify facial profile as convex, straight, or concave from 90° photo.
    Analyzes the front-facing edge of the silhouette contour.

    Convex: nose projects notably forward of forehead-chin line.
    Concave: chin projects forward, forehead recedes.
    Straight: forehead-nose-chin roughly aligned.
    """
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    h, w = img.shape[:2]
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77], np.uint8), np.array([255, 173, 127], np.uint8))

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < h * w * 0.03:
        return None

    x, y, cw, ch = cv2.boundingRect(largest)
    if ch < 40 or cw < 20:
        return None

    pts = largest.reshape(-1, 2)
    third_h = ch / 3

    # Split contour points into vertical thirds
    upper_pts = pts[(pts[:, 1] >= y) & (pts[:, 1] < y + third_h)]
    middle_pts = pts[(pts[:, 1] >= y + third_h) & (pts[:, 1] < y + 2 * third_h)]
    lower_pts = pts[(pts[:, 1] >= y + 2 * third_h) & (pts[:, 1] <= y + ch)]

    if len(upper_pts) < 3 or len(middle_pts) < 3 or len(lower_pts) < 3:
        return None

    # Detect face direction: middle zone (nose) projects to one side
    avg_x = float(np.mean(pts[:, 0]))
    mid_min, mid_max = float(np.min(middle_pts[:, 0])), float(np.max(middle_pts[:, 0]))

    if abs(mid_min - avg_x) > abs(mid_max - avg_x):
        # Face points left (nose → min X)
        forehead_proj = float(np.min(upper_pts[:, 0]))
        nose_proj = mid_min
        chin_proj = float(np.min(lower_pts[:, 0]))
    else:
        # Face points right (nose → max X)
        forehead_proj = float(np.max(upper_pts[:, 0]))
        nose_proj = mid_max
        chin_proj = float(np.max(lower_pts[:, 0]))

    baseline = (forehead_proj + chin_proj) / 2
    projection = abs(nose_proj - baseline) / max(cw, 1)

    if projection > 0.15:
        return "convex"
    if projection < 0.05:
        return "concave" if abs(chin_proj - forehead_proj) / max(cw, 1) > 0.10 else "straight"
    return "straight"


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
    with _landmarker_lock:
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

    # --- Advanced visagism metrics ---
    upper_t, middle_t, lower_t, thirds_bal = _calculate_facial_thirds(lms, w, h)

    face_width_px = _euclidean(
        _lm_point(lms, LM["left_cheek"], w, h),
        _lm_point(lms, LM["right_cheek"], w, h),
    )
    eye_sp_ratio, eye_sp_class = _calculate_eye_spacing(lms, w, h, face_width_px)
    nose_w_ratio, nose_l_ratio = _calculate_nose_proportion(lms, w, h, iod)

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
        upper_third=upper_t,
        middle_third=middle_t,
        lower_third=lower_t,
        thirds_balance=thirds_bal,
        eye_spacing_ratio=eye_sp_ratio,
        eye_spacing=eye_sp_class,
        nose_width_ratio=nose_w_ratio,
        nose_length_ratio=nose_l_ratio,
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
    profile_photo_indices: list[int] = []  # Track which photos are profiles

    for i, photo_bytes in enumerate(photos):
        pa = analyze_single_photo(photo_bytes)

        if pa.face_detected and pa.confidence >= 0.50:
            mediapipe_results.append(pa)
        else:
            # Low/zero confidence → likely a 90° profile → try silhouette extraction
            ratio = _analyze_profile_silhouette(photo_bytes)
            if ratio is not None:
                profile_depth_ratios.append(ratio)
                profile_photo_indices.append(i)
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
    avg_lwr = sum(r.length_width_ratio * wt for r, wt in zip(mediapipe_results, weights)) / max(total_w, 1e-9)

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

    # --- Advanced visagism metrics from primary frontal photo ---
    upper_t = primary.upper_third
    middle_t = primary.middle_third
    lower_t = primary.lower_third
    thirds_bal = primary.thirds_balance
    eye_sp_ratio = primary.eye_spacing_ratio
    eye_sp = primary.eye_spacing
    nose_w = primary.nose_width_ratio
    nose_l = primary.nose_length_ratio
    cheek_prom = _classify_cheekbone_prominence(fr, jr)
    golden = _calculate_golden_ratio_score(avg_lwr, upper_t, middle_t, lower_t, eye_sp_ratio)

    # --- Profile analysis (type + cranial) ---
    cephalic_type: Optional[str] = None
    profile_type: Optional[str] = None

    if profile_depth_ratios:
        avg_depth = float(np.mean(profile_depth_ratios))
        cephalic_type = _classify_cephalic_type(avg_depth)
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

    # Profile type (convex/straight/concave) from 90° photos
    # Reuse profile indices from the initial loop (no re-analysis needed)
    profile_types: list[str] = []
    for idx in profile_photo_indices:
        pt = _analyze_profile_type(photos[idx])
        if pt is not None:
            profile_types.append(pt)
    if profile_types:
        from collections import Counter
        profile_type = Counter(profile_types).most_common(1)[0][0]
        logger.info("Profile type from %d photos: %s", len(profile_types), profile_type)

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
        upper_third=upper_t,
        middle_third=middle_t,
        lower_third=lower_t,
        thirds_balance=thirds_bal,
        eye_spacing_ratio=eye_sp_ratio,
        eye_spacing=eye_sp,
        nose_width_ratio=nose_w,
        nose_length_ratio=nose_l,
        cheekbone_prominence=cheek_prom,
        golden_ratio_score=golden,
        profile_type=profile_type,
    )
