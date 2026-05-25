"""
Wrapper sobre MediaPipe Hands (API tasks) con detección de gestos.

Reglas de gesto (activación de cursor):
    - DEBE haber exactamente UNA mano en el frame.
    - El dedo ÍNDICE debe estar extendido.
    - El pulgar puede asomar libremente (es natural y reduce cansancio).
    - Ningún otro dedo (medio, anular, meñique) debe estar extendido.

Si la condición se cumple, cursor_point = punta del índice (landmark 8).
Caso contrario, cursor_point = None y la interacción queda inhibida.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple
import urllib.request

import cv2
import mediapipe as mp

_TASKS_MODEL_FILENAME = "hand_landmarker.task"
_TASKS_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)

# Landmarks de cada dedo: (MCP, PIP, DIP, TIP). Para pulgar: (CMC, MCP, IP, TIP).
_FINGER_LANDMARKS = {
    0: (1, 2, 3, 4),     # Pulgar
    1: (5, 6, 7, 8),     # Índice
    2: (9, 10, 11, 12),  # Medio
    3: (13, 14, 15, 16), # Anular
    4: (17, 18, 19, 20), # Meñique
}

FINGER_NAMES = {0: "Pulgar", 1: "Indice", 2: "Medio", 3: "Anular", 4: "Menique"}


@dataclass
class HandInfo:
    landmarks_px: List[Tuple[int, int]]
    extended_fingers: List[int] = field(default_factory=list)
    cursor_point: Optional[Tuple[int, int]] = None
    handedness: str = "Right"


def _dist_sq(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _is_finger_extended(landmarks_px, finger_idx, handedness="Right"):
    """Determina si un dedo está extendido.

    Para dedos 1-4 (índice, medio, anular, meñique):
        Combinamos DOS criterios para robustez:
        (a) la TIP debe estar más lejos del MCP que el PIP (criterio geométrico)
        (b) la TIP debe estar por ENCIMA del PIP en Y (criterio orientativo,
            asumiendo mano apuntando hacia arriba — típico al interactuar)
        Esto evita falsos positivos del puño cerrado: cuando el dedo está
        doblado, (a) puede cumplirse según el ángulo, pero (b) no.
    """
    mcp, pip, _dip, tip = _FINGER_LANDMARKS[finger_idx]
    mcp_pt = landmarks_px[mcp]
    pip_pt = landmarks_px[pip]
    tip_pt = landmarks_px[tip]

    if finger_idx == 0:
        # Pulgar
        ref = landmarks_px[5]  # MCP del índice como referencia estable
        return _dist_sq(tip_pt, ref) > _dist_sq(mcp_pt, ref) * 1.05

    # Dedos 1-4
    base_dist = _dist_sq(pip_pt, mcp_pt)
    tip_dist = _dist_sq(tip_pt, mcp_pt)
    geom_ok = tip_dist > base_dist * 1.10  # claramente más lejos

    y_ok = tip_pt[1] < pip_pt[1] - 5

    return geom_ok and y_ok


class HandTracker:
    INDEX_TIP_LANDMARK = 8

    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.5,
        min_presence_confidence: float = None,
    ):
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import (
            HandLandmarker, HandLandmarkerOptions, RunningMode,
        )

        model_path = self._ensure_model()
        # Si no se pasa presence explicito, usar el de deteccion (compat. atras).
        if min_presence_confidence is None:
            min_presence_confidence = min_detection_confidence
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._mp = mp
        self._frame_idx = 0
        print("[hand_tracker] API tasks inicializada.")

    def _ensure_model(self) -> Path:
        model_dir = Path(__file__).resolve().parent.parent / "data"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / _TASKS_MODEL_FILENAME
        if not model_path.exists():
            print(f"[hand_tracker] Descargando modelo MediaPipe a {model_path}...")
            urllib.request.urlretrieve(_TASKS_MODEL_URL, str(model_path))
            print("[hand_tracker] Modelo descargado.")
        return model_path

    def process(self, frame_bgr) -> List[HandInfo]:
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)

        self._frame_idx += 1
        timestamp_ms = self._frame_idx * 33
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        hands: List[HandInfo] = []
        if not result.hand_landmarks:
            return hands

        for i, hand_lm in enumerate(result.hand_landmarks):
            landmarks_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lm]

            label = "Right"
            if result.handedness and i < len(result.handedness):
                label = result.handedness[i][0].category_name

            extended = [
                f for f in range(5)
                if _is_finger_extended(landmarks_px, f, handedness=label)
            ]

            info = HandInfo(
                landmarks_px=landmarks_px,
                extended_fingers=extended,
                handedness=label,
            )

            # REGLA DE ACTIVACIÓN: índice extendido
            non_thumb = [d for d in extended if d != 0]
            if non_thumb == [1]:
                info.cursor_point = landmarks_px[self.INDEX_TIP_LANDMARK]
            else:
                info.cursor_point = None

            hands.append(info)
        return hands

    def close(self):
        if hasattr(self, "_landmarker") and self._landmarker is not None:
            self._landmarker.close()
