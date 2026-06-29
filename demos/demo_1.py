"""
demo_1.py — Stub de la Demo 1.

Reemplaza el contenido de este archivo con la lógica real de la demo.
Al terminar (ESC, cierre de ventana o fin de experiencia), simplemente sal
del script; el watchdog detectará la salida y volverá al menú principal.
"""
import sys

def main():
    print(f"[demo_1] Iniciando demo 1...")
    # ── Tu código va aquí ─────────────────────────────────────────────────
    # Ejemplo mínimo: esperar que el usuario presione Enter en consola.
    try:
        input("[demo_1] Presiona Enter para volver al menú...")
    except (KeyboardInterrupt, EOFError):
        pass
    print(f"[demo_1] Demo 1 finalizada.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
