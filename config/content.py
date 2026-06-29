"""
Definición del contenido de la experiencia basado en los lineamientos del TEC.
"""

# ---------------------------------------------------------------------------
# Menú principal
# ---------------------------------------------------------------------------
# NOTA: "objeto_estudio" fue reemplazado por "demos" para la sección interactiva.
MAIN_MENU_OPTIONS = [
    {
        "id": "demos",
        "label": "Demos IA",
        "icon": "01_demos.png",
        "action": "open_demo_menu",
    },
    {
        "id": "enfasis",
        "label": "Areas Tematicas",
        "icon": "02_areas.png",
        "action": "open_submenu",
    },
    {
        "id": "aplicaciones",
        "label": "Aplicaciones",
        "icon": "03_aplicaciones.png",
        "action": "play_video",
        "video": "09_aplicaciones.mp4",
    },
    {
        "id": "creditos",
        "label": "Info",
        "icon": "04_info.png",
        "action": "play_video",
        "video": "10_info.mp4",
    },
]

# ---------------------------------------------------------------------------
# Demos de IA
# Cada entrada se convierte en un botón táctil en DemoMenuState.
# 'script' es la ruta relativa al script de la demo (desde la raíz del proyecto).
# 'description' se muestra como subtítulo dentro del botón.
# ---------------------------------------------------------------------------
DEMO_OPTIONS = [
    {
        "id": "demo_1",
        "label": "Demo 1",
        "description": "Clasificacion de Imagenes",
        "script": "demos/demo_1.py",
        "color": (180, 80, 60),       # BGR: azulado-oscuro
    },
    {
        "id": "demo_2",
        "label": "Demo 2",
        "description": "Deteccion de Objetos",
        "script": "demos/demo_2.py",
        "color": (60, 140, 200),       # BGR: naranja suave
    },
    {
        "id": "demo_3",
        "label": "Demo 3",
        "description": "Reconocimiento de Voz",
        "script": "demos/demo_3.py",
        "color": (60, 180, 100),       # BGR: verde
    },
    {
        "id": "demo_4",
        "label": "Demo 4",
        "description": "Segmentacion Semantica",
        "script": "demos/demo_4.py",
        "color": (180, 60, 160),       # BGR: violeta
    },
    {
        "id": "demo_5",
        "label": "Demo 5",
        "description": "Estimacion de Pose",
        "script": "demos/demo_5.py",
        "color": (40, 180, 200),       # BGR: amarillo-dorado
    },
    {
        "id": "demo_6",
        "label": "Demo 6",
        "description": "Generacion de Texto",
        "script": "demos/demo_6.py",
        "color": (100, 80, 200),       # BGR: salmon
    },
]

# ---------------------------------------------------------------------------
# Submenú de Áreas Temáticas
# ---------------------------------------------------------------------------
SUB_MENU_AREAS = [
    {"id": "sistemas_digitales",      "label": "Sist. Digitales",    "icon": "1.png", "action": "play_video", "video": "01_digitales.mp4",      "vertiente": "dispositivos"},
    {"id": "circuitos_analogicos",    "label": "Circ. Analogicos",   "icon": "2.png", "action": "play_video", "video": "02_analogicos.mp4",      "vertiente": "dispositivos"},
    {"id": "arquitectura_comp",       "label": "Arq. Computadoras",  "icon": "3.png", "action": "play_video", "video": "03_computadoras.mp4",    "vertiente": "dispositivos"},
    {"id": "proc_senales",            "label": "Proc. de Senales",   "icon": "4.png", "action": "play_video", "video": "04_senales.mp4",         "vertiente": "informacion"},
    {"id": "comunicaciones",          "label": "Comunicaciones",     "icon": "5.png", "action": "play_video", "video": "05_comunicaciones.mp4",  "vertiente": "informacion"},
    {"id": "alta_frecuencia",         "label": "Alta Frecuencia",    "icon": "6.png", "action": "play_video", "video": "06_alta_frecuencia.mp4", "vertiente": "informacion"},
    {"id": "control_automatizacion",  "label": "Control y Auto.",    "icon": "7.png", "action": "play_video", "video": "07_control.mp4",         "vertiente": "control_potencia"},
    {"id": "electronica_potencia",    "label": "Elec. de Potencia",  "icon": "8.png", "action": "play_video", "video": "08_potencia.mp4",        "vertiente": "control_potencia"},
]

SUBMENUS = {"enfasis": SUB_MENU_AREAS}

VERTIENTES = {
    "dispositivos":    {"nombre": "Dispositivos, Circuitos y Sistemas", "color": (200, 130, 60)},
    "informacion":     {"nombre": "Tratamiento y Transmision",          "color": (100, 180, 100)},
    "control_potencia":{"nombre": "Control y Potencia",                 "color": (80,  100, 180)},
}
