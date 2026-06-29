"""
run.py — Punto de entrada del menú / experiencia interactiva.

Al finalizar, InteractiveApp debe escribir state.json con:
    {"launch_target": "ruta/a/demo.py"}
Si el usuario cierra normalmente sin seleccionar demo, no escribe nada
(o escribe sin 'launch_target') y el watchdog simplemente reinicia el menú.
"""

import sys
import traceback
from pathlib import Path


def _ensure_project_on_path() -> None:
    """Agrega la raíz del proyecto al sys.path si aún no está."""
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> int:
    _ensure_project_on_path()

    from src.app import InteractiveApp

    app = InteractiveApp()
    try:
        app.run()
    except KeyboardInterrupt:
        # Ctrl+C se trata como cierre limpio
        print("\n[run] Experiencia finalizada por el usuario.")
    except Exception as exc:                          # noqa: BLE001
        print(f"\n[run] Error inesperado: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1   # Señal de crash al watchdog

    return 0


if __name__ == "__main__":
    sys.exit(main())
