from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from classify.heuristics import classify_inventory
from ingest.inventory import build_inventory
from reports.inventory_report import write_csv_report, write_html_report


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_inventory(input_root: Path, output_root: Path) -> Path:
    started_at = utc_now_iso()
    run_id = make_run_id()
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    inventory = build_inventory(input_root=input_root, run_id=run_id, generated_at=started_at)
    classification = classify_inventory(inventory=inventory, generated_at=utc_now_iso())

    write_json(run_dir / "input_inventory.json", inventory)
    write_json(run_dir / "document_classification.json", classification)
    write_csv_report(run_dir / "inventory_report.csv", inventory, classification)
    write_html_report(run_dir / "inventory_report.html", inventory, classification)

    audit_log = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": utc_now_iso(),
        "input_root": str(input_root.resolve()),
        "output_root": str(output_root.resolve()),
        "mode": "inventory",
        "total_files": inventory["total_files"],
        "generated_files": [
            "input_inventory.json",
            "document_classification.json",
            "audit_log.json",
            "inventory_report.html",
            "inventory_report.csv",
        ],
        "scope_guard": {
            "original_files_moved": False,
            "original_files_deleted": False,
            "motor_cad_dependency": False,
        },
    }
    write_json(run_dir / "audit_log.json", audit_log)
    return run_dir


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SEPLAN IA — MVP 0 Inventário Documental")
    parser.add_argument("--input", required=True, help="Pasta de entrada a inventariar")
    parser.add_argument("--output", required=True, help="Pasta raiz das saídas")
    parser.add_argument("--mode", default="inventory", choices=["inventory"], help="Modo de execução")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_root = Path(args.input)
    output_root = Path(args.output)

    if not input_root.exists() or not input_root.is_dir():
        print(f"ERRO: pasta de entrada inválida: {input_root}", file=sys.stderr)
        return 2

    if args.mode != "inventory":
        print(f"ERRO: modo não suportado: {args.mode}", file=sys.stderr)
        return 2

    run_dir = run_inventory(input_root=input_root, output_root=output_root)
    print(f"SEPLAN Pipeline concluída: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
