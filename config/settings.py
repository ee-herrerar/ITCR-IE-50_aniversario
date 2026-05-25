from pathlib import Path

# Rutas
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
VIDEOS_DIR = ASSETS_DIR / "videos"
IMAGES_DIR = ASSETS_DIR / "images"
ICONS_DIR = ASSETS_DIR / "icons"
DATA_DIR = ROOT_DIR / "data"

# Ventana / pantalla
WINDOW_NAME = "50 Aniversario - Ingenieria Electronica - TEC"
FULLSCREEN = True
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
CAMERA_WIDTH = 352
CAMERA_HEIGHT = 288
CAMERA_INDEX = 0

# Resolución a la que se procesa MediaPipe (Calidad VGA: 640x480, Calidad CIF: 352x288)
PROCESSING_WIDTH = 352
PROCESSING_HEIGHT = 288

# Backend de captura. En Windows, CAP_DSHOW suele ser bastante más rápido
import platform as _platform
import cv2 as _cv2

if _platform.system() == "Windows":
    CAMERA_BACKEND = _cv2.CAP_DSHOW
else:
    CAMERA_BACKEND = _cv2.CAP_ANY

# Fondo: blanco plano por defecto. Si SHOW_CAMERA_BACKGROUND=True, se mezcla
SHOW_CAMERA_BACKGROUND = True
CAMERA_BACKGROUND_OPACITY = 1  # 0 = solo fondo, 1 = solo cámara

MIRROR_CAMERA = True

# Paleta TEC (BGR) — Manual de Identidad Institucional
TEC_AZUL = (114, 63, 0)        # #003F72  PANTONE 295C
TEC_ROJO = (64, 51, 239)       # #EF3340  PANTONE 032C
TEC_GRIS = (90, 88, 84)        # #54585A
TEC_BLANCO = (255, 255, 255)
TEC_NEGRO = (0, 0, 0)

# Variantes derivadas
TEC_AZUL_CLARO = (180, 120, 50)    # tono más suave para hover
TEC_AZUL_PALIDO = (240, 220, 200)  # azulado muy claro, nodos en reposo
TEC_GRIS_CLARO = (235, 235, 240)   # superficies neutras

# Mapeo a roles de UI
COLOR_BG = TEC_BLANCO                    # fondo
COLOR_CENTER_NODE = TEC_AZUL             # nodo central
COLOR_AREA_NODE = TEC_AZUL_PALIDO        # nodos en reposo
COLOR_AREA_NODE_HOVER = TEC_AZUL_CLARO   # nodos en hover
COLOR_ACCENT = TEC_ROJO                  # anillo de dwell, énfasis
COLOR_TEXT = TEC_AZUL                    # texto principal
COLOR_TEXT_ON_DARK = TEC_BLANCO          # texto sobre nodos oscuros
COLOR_CURSOR = TEC_ROJO                  # cursor

# Detección de manos (MediaPipe)
MAX_NUM_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.5
# Presencia: que tan seguro debe estar de que la mano SIGUE ahi entre frames.
MIN_PRESENCE_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.75

CURSOR_SMOOTHING = 0.5

# Interacción (hover + dwell)
DWELL_TIME_SECONDS = 1.2
CURSOR_RADIUS = 20
CURSOR_COLOR = COLOR_CURSOR

# Menú radial
CENTER_NODE_RADIUS = 100
NODE_RADIUS_MAIN = 100
NODE_RADIUS_SUB = 100
ORBIT_RADIUS_MAIN = 350
ORBIT_RADIUS_SUB = 350
MENU_ROTATION_SPEED = 0.0

# Reproducción de video
BACK_DWELL_TIME = 1.0
BACK_BUTTON_POS = (100, 100)
BACK_BUTTON_RADIUS = 75

# Estados / Idle
IDLE_TIMEOUT_SECONDS = 5.0

# Debug flags
SHOW_FPS = True
SHOW_HAND_LANDMARKS = False
SHOW_EXTENDED_FINGERS_DEBUG = False
SHOW_TIMING_PROFILE = True