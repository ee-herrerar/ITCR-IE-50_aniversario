#README

### Instalación de entorno
---
Por seguridad, se recomienda utilizar el entorno de Python vía **pyenv** y un entorno virtual (puesto que Micromamba suele tener problemas al instalar `mediapipe`).

### Pasos para la configuración:

1. **Inicializar el entorno virtual** en la carpeta del proyecto de preferencia:
```bash
python -m venv venv

```

2. **Activar el entorno virtual** según tu sistema operativo:
* **Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1

```

* **Windows (CMD):**
```cmd
.\venv\Scripts\activate.bat

```

* **Mac / Linux:**
```bash
source venv/bin/activate

```

3. **Instalar los paquetes respectivos** una vez que el entorno esté activo:
```bash
pip install mediapipe opencv-python watchdog

```

---
