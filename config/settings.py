from pathlib import Path

# Rutas
ROOT_DIR  = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
VIDEOS_DIR = ASSETS_DIR / "videos"
IMAGES_DIR = ASSETS_DIR / "images"
ICONS_DIR  = ASSETS_DIR / "icons"
DATA_DIR   = ROOT_DIR / "data"
DEMOS_DIR  = ROOT_DIR / "demos"          # carpeta con demo_1.py … demo_N.py

# Registro de accesos a demos (una línea JSON por acceso)
ACCESS_LOG_PATH = ROOT_DIR / "access_log.jsonl"

# Ventana / pantalla
WINDOW_NAME   = "50 Aniversario - Ingenieria Electronica - TEC"
FULLSCREEN    = True
WINDOW_WIDTH  = 1920
WINDOW_HEIGHT = 1080
CAMERA_WIDTH  = 352
CAMERA_HEIGHT = 288
CAMERA_INDEX  = 0

# Resolución a la que se procesa MediaPipe
PROCESSING_WIDTH  = 352
PROCESSING_HEIGHT = 288

# Backend de captura
import platform as _platform
import cv2 as _cv2
CAMERA_BACKEND = _cv2.CAP_DSHOW if _platform.system() == "Windows" else _cv2.CAP_ANY

# Fondo de cámara
SHOW_CAMERA_BACKGROUND    = False
CAMERA_BACKGROUND_OPACITY = 0       # 0 = solo fondo, 1 = solo cámara

MIRROR_CAMERA = True

# ── Paleta TEC (BGR) ─────────────────────────────────────────────────────────
TEC_AZUL   = (114, 63, 0)       # #003F72  PANTONE 295C
TEC_ROJO   = (64,  51, 239)     # #EF3340  PANTONE 032C
TEC_GRIS   = (90,  88, 84)      # #54585A
TEC_BLANCO = (255, 255, 255)
TEC_NEGRO  = (0,   0,   0)

TEC_AZUL_CLARO  = (180, 120, 50)
TEC_AZUL_PALIDO = (240, 220, 200)
TEC_GRIS_CLARO  = (235, 235, 240)

# Roles UI
COLOR_BG               = TEC_BLANCO
COLOR_CENTER_NODE      = TEC_AZUL
COLOR_AREA_NODE        = TEC_AZUL_PALIDO
COLOR_AREA_NODE_HOVER  = TEC_AZUL_CLARO
COLOR_ACCENT           = TEC_ROJO
COLOR_TEXT             = TEC_AZUL
COLOR_TEXT_ON_DARK     = TEC_BLANCO
COLOR_CURSOR           = TEC_ROJO

# ── MediaPipe ────────────────────────────────────────────────────────────────
MAX_NUM_HANDS             = 1
MIN_DETECTION_CONFIDENCE  = 0.5
MIN_PRESENCE_CONFIDENCE   = 0.5
MIN_TRACKING_CONFIDENCE   = 0.75

CURSOR_SMOOTHING = 0.5

# ── Interacción ───────────────────────────────────────────────────────────────
DWELL_TIME_SECONDS  = 1.2
CURSOR_RADIUS       = 10
CURSOR_COLOR        = COLOR_CURSOR

# ── Menú radial (áreas temáticas) ────────────────────────────────────────────
CENTER_NODE_RADIUS  = 100
NODE_RADIUS_MAIN    = 100
NODE_RADIUS_SUB     = 100
ORBIT_RADIUS_MAIN   = 350
ORBIT_RADIUS_SUB    = 350
MENU_ROTATION_SPEED = 0.0

# ── Menú de demos (grid táctil) ───────────────────────────────────────────────
# Número de columnas del grid; las filas se calculan automáticamente.
DEMO_GRID_COLS      = 3
# Tamaño de cada botón de demo en píxeles
DEMO_BUTTON_W       = 480
DEMO_BUTTON_H       = 220
# Espacio entre botones
DEMO_BUTTON_GAP     = 40
# Margen superior del grid (deja espacio para el título y el botón Volver)
DEMO_GRID_TOP       = 180

# ── Reproducción de video ─────────────────────────────────────────────────────
BACK_DWELL_TIME    = 1.0
BACK_BUTTON_POS    = (100, 100)
BACK_BUTTON_RADIUS = 75

# ── Idle ──────────────────────────────────────────────────────────────────────
IDLE_TIMEOUT_SECONDS = 5.0

# ── Debug ─────────────────────────────────────────────────────────────────────
SHOW_FPS                    = True
SHOW_HAND_LANDMARKS         = False
SHOW_EXTENDED_FINGERS_DEBUG = False
SHOW_TIMING_PROFILE         = True
