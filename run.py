import sys
import traceback
from pathlib import Path

def _ensure_project_on_path():
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
        print("\n[run] Experiencia finalizada.")
        return 0
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n[run] Fallo: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)