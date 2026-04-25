from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import motor_v072


def _as_float_list(values: list[Any], expected_len: int, label: str) -> list[float]:
    if not isinstance(values, list) or len(values) != expected_len:
        raise ValueError(f"{label} deve ter {expected_len} valores")
    return [float(v) for v in values]


def _region_name(region: dict[str, Any], page_index: int, idx: int) -> str:
    return (
        region.get("output_name")
        or region.get("region_id")
        or f"page{page_index}_region{idx}"
    )


def process_manifest(manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    project_id = manifest.get("project_id", "project")
    project_name = manifest.get("project_name", project_id)
    processing_version = manifest.get("processing_version", "v072-manifest")

    output_root = Path(manifest.get("output_root", "output"))
    output_root.mkdir(parents=True, exist_ok=True)

    runs: list[dict[str, Any]] = []

    for doc in manifest.get("documents", []):
        pdf = Path(doc["source_pdf"])
        default_outdir = Path(doc.get("output_dir", output_root))
        default_outdir.mkdir(parents=True, exist_ok=True)

        clean_cfg = doc.get("clean", {})
        coord_tol = float(clean_cfg.get("coord_tol", 0.25))
        gap_tol = float(clean_cfg.get("gap_tol", 0.15))

        for page_cfg in doc.get("pages", []):
            page_index = int(page_cfg["page_index"])
            for idx, region in enumerate(page_cfg.get("regions", []), start=1):
                view = _as_float_list(region["bbox"], 4, "bbox")
                origin = _as_float_list(region["origin"], 2, "origin")
                outdir = Path(region.get("output_dir", default_outdir))
                outdir.mkdir(parents=True, exist_ok=True)
                name = _region_name(region, page_index, idx)

                raw = motor_v072.extract(str(pdf), page_index, view, origin)
                cleaned, unique_count = motor_v072.clean(raw, coord_tol=coord_tol, gap_tol=gap_tol)

                dxf = outdir / f"{name}.dxf"
                svg = outdir / f"{name}.svg"
                motor_v072.write_dxf(dxf, cleaned)
                motor_v072.write_svg(svg, cleaned)

                report = {
                    "motor": "V07.2 Clean Native Export",
                    "raw_lines": len(raw),
                    "unique_input_lines": unique_count,
                    "final_lines": len(cleaned),
                    "removed_or_merged_before_export": len(raw) - len(cleaned),
                    "layers": {
                        "A-WALL": sum(1 for *_, l in cleaned if l == "A-WALL"),
                        "A-REF": sum(1 for *_, l in cleaned if l == "A-REF"),
                    },
                    "dxf": str(dxf),
                    "svg": str(svg),
                    "dxf_format": "R12 / AC1009",
                    "target": "AutoCAD 2026",
                    "manifest": {
                        "project_id": project_id,
                        "project_name": project_name,
                        "processing_version": processing_version,
                        "source_pdf": str(pdf),
                        "page_index": page_index,
                        "region_id": region.get("region_id"),
                        "region_type": region.get("region_type"),
                        "bbox": view,
                        "origin": origin,
                        "scale": region.get("scale"),
                        "notes": region.get("notes"),
                        "clean": {"coord_tol": coord_tol, "gap_tol": gap_tol},
                    },
                }
                (outdir / f"{name}_relatorio.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
                )

                runs.append(
                    {
                        "source_pdf": str(pdf),
                        "page_index": page_index,
                        "region_id": region.get("region_id"),
                        "output_name": name,
                        "outdir": str(outdir),
                        "final_lines": report["final_lines"],
                        "layers": report["layers"],
                    }
                )

    summary = {
        "project_id": project_id,
        "project_name": project_name,
        "processing_version": processing_version,
        "manifest_path": str(manifest_path),
        "runs": runs,
    }
    summary_path = output_root / f"{project_id}_manifest_run.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="Executa motor V07.2 a partir de input_manifest")
    ap.add_argument("--manifest", required=True, help="Caminho do arquivo JSON de manifesto")
    args = ap.parse_args()

    summary = process_manifest(Path(args.manifest))
    print("Concluído.")
    print("Project:", summary["project_id"])
    print("Runs:", len(summary["runs"]))


if __name__ == "__main__":
    main()
