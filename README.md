# (WIP) Experiencia Interactiva - 50 Aniversario Ingeniería Electrónica TEC

### NOTA: Ejecutado en python 3.11
Es una interfaz sencilla el cual con el usuario se moverá usando el dedo índice a través de interfaces. En resumen se compone de lo siguiente (No se me ocurren buenos nombres, así que son los provisionales):
* Objeto de Estudio: Video sobre dentro del edificio de electro (Zzz)
* Info: Video sobre la carrera (Zzz)
* Areas Temáticas: Más videos divididos por las áreas que trabajamos en la carrera (Zzz)
* Demos: Este espacio es para las demos con IA, en teoría debe de "cerrar" este programa principal para entrar a la demo.

## Requisitos
* Requiere de instalar vía pip o micromamba install (Recomendable la primera puesto que micromamba me generó problemas con algunos paquetes). Vía pip basta con el siguiente comando: _pip install mediapipe opencv-python numpy_. Puede que en linux ocupes instalar python3-tk o MacOS requiera de python-tk, por lo que revisen la documentación respectiva de acuerdo a la distro u OS.
* Una cámara web. Recomendable que esté a una distancia media de ti y en angulo donde pueda verse el mejor espacio posible. 

## Configuración e Instalación

### 1. Clonar o descargar el repositorio

Al descargar, se tendrá la siguiente estructura:

```bash
│   run.py
│   test_gesture.py
│
├───assets
│   ├───icons (PRÓXIMAMENTE)
│   ├───images (PRÓXIMAMENTE)
│   └───videos (PRÓXIMAMENTE)
├───config
│   │   content.py
│   │   settings.py
│   │   __init__.py
│   │
│   └───__pycache__ (Caché al ejecutar el programa, así que ignorar)
│
├───data
│       hand_landmarker.task (Descargarlo por aparte)
│
└───src
    │   app.py
    │   hand_tracker.py
    │   __init__.py
    │
    ├───states
    │   │   state_manager.py
    │   │   __init__.py
    │   │
    │   └───__pycache__(Caché al ejecutar el programa, así que ignorar)
    │
    └───__pycache__(Caché al ejecutar el programa, así que ignorar)
```
El contenido de imágenes y multimedia no debería de causar problemas en las ejecuciones que realicé (Fuente: De la Hispanidad), por lo que no se preocupen si aparece _"Video.mp4"_ o algo relacionado en ciertas sesiones. Tienen que descargar el paquete de hand_landmarker.task [en este enlace.](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task) 
### 2. Crear un entorno virtual (Recomendado)
Con pyenv:
```bash
# Crear el entorno virtual en la carpeta principal del proyecto
python -m venv venv

# Activar el entorno virtual
# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# En Linux/macOS:
source venv/bin/activate

```
Con Micromamba:
```bash
micromamba create -n nombre_entorno python=3.11

# Para activar
micromamba activate nombre_entorno
```
Recomiendo usar pip install una vez activado el entorno antes que usar micromamba install, debería ser válido si lo logran.

### 3. Instalar dependencias

Instala las librerías necesarias mediante `pip`. Este proyecto depende principalmente de OpenCV y MediaPipe:

```bash
pip install opencv-python mediapipe numpy

```
## Ejecución del Programa

### Probar la cámara y el gesto (Diagnóstico)

Para verificar que tu cámara funciona correctamente y que el sistema detecta bien tu dedo índice, ejecuta:

```bash
python test_gesture.py

```

* **Regla del gesto:** Levanta **únicamente el dedo índice**. Si la pantalla muestra el mensaje **"GESTO VÁLIDO"** en verde, la configuración de la cámara y de la IA es exitosa. Presiona `Q` o `ESC` para salir.

### Ejecutar la aplicación principal

Para lanzar la experiencia interactiva completa en pantalla completa, ejecuta:

```bash
python run.py

```

**Controles de teclado globales durante la ejecución:**

* `ESC` o `Q`: Cierra la aplicación de manera segura.
* `F`: Alterna entre pantalla completa y modo ventana.
* `M`: Activa o desactiva el modo espejo de la cámara en tiempo real (Aunque la cámara estará desactivada por defecto dada la baja calidad).

---

## Parámetros para "Probar" la app (`config/settings.py`)

Si necesitas adaptar el comportamiento a la computadora del evento, puedes editar `config/settings.py`:

* **`CAMERA_INDEX`**: Cambia este valor (0, 1, 2...) si tienes varias cámaras conectadas y el programa abre la incorrecta. Idealmente no hay problemas, si tienes más de una en la computadora, puede que requiera un ajuste en _settings.py_ al parámetro __CAMERA_INDEX = 0__ al valor 1 o 2 (0 es el por defecto, pero cambiarlo SOLAMENTE si tienes más de una cámara o dispositivo de grabación de video). Adicional a esto, hay un ajuste para mostrar la cámara de fondo, puesto que la salida de cámara es en resolución baja está oculta por defecto.
* **`FULLSCREEN`**: Cambiálo a `False` si prefieres que no inicie ocupando toda la pantalla de inmediato.
* **`DWELL_TIME_SECONDS`**: Ajusta el tiempo (en segundos) que el usuario debe mantener el cursor sobre un botón para hacer "click".