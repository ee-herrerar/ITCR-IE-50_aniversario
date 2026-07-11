import os
import urllib.request
import zipfile
from typing import NamedTuple

# formato y rutas de carpetas y archivos
class ProjectFolders(NamedTuple):
    config: str
    demos:  str
    src:    str
    data:   str
    icons:  str
    images: str
    videos: str

class ProjectUrl(NamedTuple):
    HandLandmarker: str
    IconsZip:       str
    ImagesZip:      str
    VideosZip:      str
    
folders = ProjectFolders(
    config  = "./config",
    demos   = "./demos",
    src     = "./src",
    data    = "./data",
    icons   = "./assets/icons",
    images  = "./assets/images",
    videos  = "./assets/videos"
)

url = ProjectUrl(
    HandLandmarker  = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
    IconsZip        = "https://drive.google.com/file/d/1btoMBZbNRAL1cxsZOSo7aDmUaNoN_qm4/view?usp=sharing",
    ImagesZip       = "https://drive.google.com/file/d/11LHZsJVwWtfM4Fl_m_dH1rXOSXKSWq0d/view?usp=sharing",
    VideosZip       = "https://drive.google.com/file/d/15pKbRqnA16RItrcv5UEeLLUqJxztItLd/view?usp=sharing"
)

# Crear carpetas (Principal por si falta carpeta para assets)
for folder_path in folders:
    if not os.path.exists(folder_path):
        print(f"La carpeta '{folder_path}' no existe, creándola...")
        os.makedirs(folder_path)

# Instalar para HandLandMarker
try:
    print("\nDescargando Hand Landmarker...")
    urllib.request.urlretrieve(
        url.HandLandmarker, 
        os.path.join(folders.data, "hand_landmarker.task")
    )
    print("Hand Landmarker descargado con éxito.")
except Exception as e:
    print(f"No se pudo descargar 'hand_landmarker.task': {e}")
    print("Tiene que descargarlo manualmente y colocarlo en la carpeta 'data' con el mismo nombre dado.")

def convert_to_direct_link(drive_url: str) -> str:
    """Convierte un enlace de vista de Google Drive a un enlace de descarga directa."""
    if "drive.google.com" in drive_url and "/file/d/" in drive_url:
        start = drive_url.find("/file/d/") + 8
        end = drive_url.find("/", start)
        if end == -1:
            end = drive_url.find("?", start)
        file_id = drive_url[start:end] if end != -1 else drive_url[start:]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return drive_url

media_downloads = [
    ("Íconos", url.IconsZip, folders.icons),
    ("Imágenes", url.ImagesZip, folders.images),
    ("Videos", url.VideosZip, folders.videos)
]

for nombre, link_zip, destino in media_downloads:
    if not link_zip:
        continue
        
    direct_url = convert_to_direct_link(link_zip)
    zip_temp_path = os.path.join(folders.data, f"temp_{nombre.lower()}.zip")
    
    try:
        print(f"\nProcesando {nombre}...")
        
        # Simular un navegador para que Drive no bloquee la descarga automatizada
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        
        # 1. Descargar el archivo comprimido
        print(f"  -> Descargando {nombre} desde Google Drive...")
        urllib.request.urlretrieve(direct_url, zip_temp_path)
        
        # 2. Descomprimir en la carpeta correspondiente
        print(f"  -> Descomprimiendo en {destino}...")
        with zipfile.ZipFile(zip_temp_path, 'r') as zip_ref:
            zip_ref.extractall(destino)
            
        # 3. Eliminar el zip temporal para no dejar basura
        print(f"  -> ¡Listo! Eliminando archivo temporal...")
        os.remove(zip_temp_path)
        
    except Exception as e:
        print(f"  -> Error al procesar {nombre}: {e}")
        # Si ocurre un error, intentamos borrar el archivo temporal a medio descargar
        if os.path.exists(zip_temp_path):
            os.remove(zip_temp_path)

print("\n¡Proceso de preparación de descargas finalizado!")