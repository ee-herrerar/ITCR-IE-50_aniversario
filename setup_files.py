# Naguará (?
import os
import urllib.request
from typing import NamedTuple

# Definir ubicación respecto a folder raiz del proyecto de las otras carpetas
class ProjectFolders(NamedTuple):
    config: str
    demos:  str
    src:    str
    data:   str

class ProjectUrl(NamedTuple):
    HandLandmarker: str

folders = ProjectFolders(
    config="./config",
    demos="./demos",
    src="./src",
    data="./data"
)

url = ProjectUrl(
        HandLandmarker="https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)


class ProjectMediaIcons(NamedTuple):
    a:str

class ProjectMediaVideos(NamedTuple):
    a:str

class ProjectMediaImages(NamedTuple):
    a:str
    
'''
for path_location in folders:
    if not os.path.exists(path_location):
        print(f"{path_location} no existe, creando carpeta...")
        os.makedirs(path_location)
        if path_location == "config":
            with open("__init__.py", "w"):
            pass
        else if path_location == "src":
            with open("__init__.py", "w"):
            pass   
    else:
        print(f"{path_location} existe.")

print("\n")
'''

if not os.path.exists(folders.data):
    print(f"{folders.data} no existe, creando carpeta...")
    os.makedirs(folders.data)

# Instalar para HandLandMarker
try:
    print("Descargando Hand Landmarker...")
    urllib.request.urlretrieve(
        url.HandLandmarker, 
        f"{folders.data}/hand_landmarker.task"
    )
except:
    print("No se pudo descargar 'hand_landmarker.task', tiene que descargarlo manualmente y colocarlo en la carpeta 'data' con el mismo nombre dado.")


