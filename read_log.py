"""
read_log.py — Herramienta de consola para ver el registro de accesos a demos.

Uso:
    python read_log.py              # muestra todo el log
    python read_log.py --tail 20   # últimas N entradas
    python read_log.py --demo demo_3   # filtra por ID de demo
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter

LOG_PATH = Path(__file__).resolve().parent / "access_log.jsonl"


def load_records(path: Path):
    if not path.exists():
        print(f"[read_log] No existe el archivo de log: {path}")
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"  Línea {lineno} inválida: {exc}", file=sys.stderr)
    return records


def main():
    parser = argparse.ArgumentParser(description="Visor del log de accesos a demos.")
    parser.add_argument("--tail", type=int, default=0,
                        help="Muestra sólo las últimas N entradas (0 = todas).")
    parser.add_argument("--demo", type=str, default="",
                        help="Filtra por demo_id (ej: demo_3).")
    args = parser.parse_args()

    records = load_records(LOG_PATH)
    if not records:
        print("Sin registros.")
        return

    if args.demo:
        records = [r for r in records if r.get("demo_id") == args.demo]

    if args.tail > 0:
        records = records[-args.tail:]

    # ── Tabla ────────────────────────────────────────────────────────────────
    print(f"\n{'#':<5} {'Timestamp':<22} {'Demo ID':<12} {'Etiqueta':<16} Descripcion")
    print("─" * 80)
    for i, r in enumerate(records, 1):
        print(f"{i:<5} {r.get('timestamp','?'):<22} "
              f"{r.get('demo_id','?'):<12} {r.get('demo_label','?'):<16} "
              f"{r.get('script','?')}")

    # ── Resumen ───────────────────────────────────────────────────────────────
    print("\n── Resumen de accesos ──────────────────────────────────────────────")
    counter = Counter(r.get("demo_id", "?") for r in records)
    for demo_id, count in counter.most_common():
        bar = "█" * min(count, 40)
        print(f"  {demo_id:<12} {bar} ({count})")
    print(f"\n  Total de accesos registrados: {len(records)}")


if __name__ == "__main__":
    main()
