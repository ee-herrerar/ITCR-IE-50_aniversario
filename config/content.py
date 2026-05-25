"""
Definición del contenido de la experiencia basado en los lineamientos del TEC.
"""
OBJETO_DE_ESTUDIO = {
    "id": "ingenieria_electronica",
    "label": "Ingenieria Electronica",
    "icon": "ingenieria_electronica.png",
    "video": "00_objeto_estudio.mp4",
}

MAIN_MENU_OPTIONS = [
    {"id": "objeto_estudio", "label": "Objeto de Estudio", "icon": "01_objeto.png", "action": "play_video", "video": "00_objeto_estudio.mp4"},
    {"id": "enfasis", "label": "Areas Tematicas", "icon": "02_areas.png", "action": "open_submenu"},
    {"id": "aplicaciones", "label": "Aplicaciones Practicas", "icon": "03_aplicaciones.png", "action": "play_video", "video": "09_aplicaciones.mp4"},
    {"id": "creditos", "label": "Info", "icon": "04_info.png", "action": "play_video", "video": "10_info.mp4"},
]

SUB_MENU_AREAS = [
    {"id": "sistemas_digitales", "label": "Sist. Digitales (VLSI/Embed)", "icon": "1.png", "action": "play_video", "video": "01_digitales.mp4", "vertiente": "dispositivos"},
    {"id": "circuitos_analogicos", "label": "Circuitos Analogicos / Mix", "icon": "2.png", "action": "play_video", "video": "02_analogicos.mp4", "vertiente": "dispositivos"},
    {"id": "arquitectura_computadoras", "label": "Arq. de Computadoras", "icon": "3.png", "action": "play_video", "video": "03_computadoras.mp4", "vertiente": "dispositivos"},
    {"id": "procesamiento_senales", "label": "Procesamiento de Senales", "icon": "4.png", "action": "play_video", "video": "04_senales.mp4", "vertiente": "informacion"},
    {"id": "comunicaciones", "label": "Comunicaciones", "icon": "5.png", "action": "play_video", "video": "05_comunicaciones.mp4", "vertiente": "informacion"},
    {"id": "alta_frecuencia", "label": "Sistemas de Alta Frecuencia", "icon": "6.png", "action": "play_video", "video": "06_alta_frecuencia.mp4", "vertiente": "informacion"},
    {"id": "control_automatizacion", "label": "Control y Automatizacion", "icon": "7.png", "action": "play_video", "video": "07_control.mp4", "vertiente": "control_potencia"},
    {"id": "electronica_potencia", "label": "Electronica de Potencia", "icon": "8.png", "action": "play_video", "video": "08_potencia.mp4", "vertiente": "control_potencia"},
]

SUBMENUS = {"enfasis": SUB_MENU_AREAS}

VERTIENTES = {
    "dispositivos": {"nombre": "Dispositivos, Circuitos y Sistemas", "color": (200, 130, 60)},
    "informacion": {"nombre": "Tratamiento y Transmision", "color": (100, 180, 100)},
    "control_potencia": {"nombre": "Control y Potencia", "color": (80, 100, 180)},
}