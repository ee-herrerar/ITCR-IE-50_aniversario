"""
demo_6.py — Stub de la Demo 6.

Reemplaza el contenido de este archivo con la lógica real de la demo.
Al terminar (ESC, cierre de ventana o fin de experiencia), simplemente sal
del script; el watchdog detectará la salida y volverá al menú principal.
"""
import sys

def main():
    print(f"[demo_6] Iniciando demo 6...")
    # ── Tu código va aquí ─────────────────────────────────────────────────
    # Ejemplo mínimo: esperar que el usuario presione Enter en consola.
    try:
        input("[demo_6] Presiona Enter para volver al menú...")
    except (KeyboardInterrupt, EOFError):
        pass
    print(f"[demo_6] Demo 6 finalizada.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
