"""
watchdog.py — Supervisor del proceso principal (run.py) y apps demo.

Flujo:
  1. Lanza run.py (menú principal).
  2. Al cerrarse, lee state.json para saber si hay una demo que lanzar.
  3. Lanza la demo, espera a que termine y regresa al menú.
  4. Repite indefinidamente hasta Ctrl+C o error crítico.
"""

import subprocess
import sys
import time
import os
import json
import signal
import logging
from pathlib import Path

# ── Configuración ────────────────────────────────────────────────────────────

# Anclar siempre a la carpeta donde vive watchdog.py, no al CWD del proceso.
_ROOT = Path(__file__).resolve().parent
STATE_FILE  = _ROOT / "state.json"
MAX_CRASHES = 5          # Reintentos consecutivos antes de abortar
CRASH_RESET = 60.0       # Segundos sin crash para resetear el contador
RESTART_DELAY = 1.5      # Pausa entre reinicios tras un crash

# Usa el mismo intérprete con el que se lanzó el watchdog (evita python vs python3)
PYTHON = sys.executable

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[WD %(asctime)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("watchdog")

# ── Estado compartido (para el handler de señales) ───────────────────────────

_current_process: subprocess.Popen | None = None
_running = True


def _signal_handler(sig, frame):
    """Captura Ctrl+C / SIGTERM y cierra el hijo limpiamente."""
    global _running
    _running = False
    log.info("Señal de cierre recibida (%s). Terminando hijo…", signal.Signals(sig).name)
    if _current_process and _current_process.poll() is None:
        _current_process.terminate()
        try:
            _current_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _current_process.kill()
    log.info("Watchdog detenido.")
    sys.exit(0)


signal.signal(signal.SIGINT,  _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# ── Helpers ───────────────────────────────────────────────────────────────────

def reset_state() -> None:
    """Elimina state.json si existe."""
    STATE_FILE.unlink(missing_ok=True)


def read_target() -> str | None:
    """
    Lee 'launch_target' de state.json.
    Acepta rutas absolutas y relativas (relativas se resuelven desde _ROOT).
    Devuelve la ruta como string, o None si el archivo no existe / es inválido.
    """
    if not STATE_FILE.exists():
        return None
    try:
        data   = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        target = data.get("launch_target")
        if not target:
            log.warning("state.json no contiene 'launch_target'.")
            return None

        path = Path(target)
        if not path.is_absolute():
            path = (_ROOT / path).resolve()

        if path.exists():
            return str(path)
        else:
            log.warning("launch_target '%s' no existe en disco, ignorando.", path)
            return None
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("No se pudo leer state.json: %s", exc)
    return None


def run_process(script: str, label: str) -> int:
    """
    Lanza `script` con el intérprete actual, espera a que termine
    y devuelve su código de salida.
    El script puede ser absoluto o relativo a la raíz del proyecto.
    """
    global _current_process
    path = Path(script)
    if not path.is_absolute():
        path = (_ROOT / path).resolve()
    log.info("Iniciando %s → %s", label, path)
    _current_process = subprocess.Popen([PYTHON, str(path)], cwd=str(_ROOT))
    returncode = _current_process.wait()
    _current_process = None
    log.info("%s finalizado (exit=%d).", label, returncode)
    return returncode


# ── Bucle principal ───────────────────────────────────────────────────────────

def watchdog_main() -> None:
    global _running

    crash_count = 0
    last_start  = time.monotonic()

    log.info("Watchdog activo. Intérprete: %s", PYTHON)

    while _running:
        reset_state()

        # ── Menú principal ────────────────────────────────────────────────
        now = time.monotonic()
        # Si pasó suficiente tiempo desde el último crash, reseteamos contador
        if crash_count > 0 and (now - last_start) > CRASH_RESET:
            log.info("Sin crashes durante %.0fs, reseteando contador.", CRASH_RESET)
            crash_count = 0

        last_start = time.monotonic()
        exit_code  = run_process("run.py", "Menú")

        if not _running:
            break

        if exit_code not in (0, -signal.SIGTERM):
            crash_count += 1
            log.error(
                "run.py terminó con error (exit=%d). Crash %d/%d.",
                exit_code, crash_count, MAX_CRASHES,
            )
            if crash_count >= MAX_CRASHES:
                log.critical(
                    "Demasiados crashes consecutivos (%d). Abortando watchdog.", crash_count
                )
                break
            log.info("Reintentando en %.1fs…", RESTART_DELAY)
            time.sleep(RESTART_DELAY)
            continue
        else:
            crash_count = 0  # salida limpia → resetear

        # ── Demo / app objetivo ───────────────────────────────────────────
        target = read_target()
        reset_state()

        if target:
            log.info("Lanzando demo: %s", target)
            demo_code = run_process(target, "Demo")
            if demo_code != 0:
                log.warning("Demo finalizó con error (exit=%d).", demo_code)
            log.info("Regresando al menú…")
        else:
            log.info("Sin demo registrada. Reiniciando menú en %.1fs…", RESTART_DELAY)
            time.sleep(RESTART_DELAY)

    log.info("Watchdog terminado.")


if __name__ == "__main__":
    watchdog_main()
