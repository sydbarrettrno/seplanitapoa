from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1048576)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def detect_kind(extension: str) -> str:
    ext = extension.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}:
        return "imagem"
    if ext in {".xls", ".xlsx", ".csv", ".ods"}:
        return "planilha"
    if ext == ".dxf":
        return "dxf"
    if ext == ".svg":
        return "svg"
    if ext == ".json":
        return "json"
    if ext in {".txt", ".md", ".rtf"}:
        return "texto"
    return "arquivo"


def count_pdf_pages(path: Path) -> tuple[int | None, str | None]:
    try:
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception:
            from PyPDF2 import PdfReader  # type: ignore
        reader = PdfReader(str(path))
        return len(reader.pages), None
    except ImportError:
        return None, "biblioteca de leitura PDF não disponível"
    except Exception as exc:
        return None, f"falha ao contar páginas do PDF: {exc}"


def build_inventory(input_root: Path, run_id: str, generated_at: str) -> dict[str, Any]:
    root = input_root.resolve()
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        extension = path.suffix.lower()
        item: dict[str, Any] = {
            "file_name": path.name,
            "relative_path": path.relative_to(root).as_posix(),
            "extension": extension,
            "size_bytes": None,
            "sha256": None,
            "readable": False,
            "detected_kind": detect_kind(extension),
            "pdf_pages": None,
            "error": None,
        }
        try:
            item["size_bytes"] = path.stat().st_size
            item["sha256"] = sha256_file(path)
            item["readable"] = True
        except Exception as exc:
            item["error"] = f"falha ao ler arquivo: {exc}"
        if extension == ".pdf":
            pages, pdf_error = count_pdf_pages(path)
            item["pdf_pages"] = pages
            if pdf_error:
                item["error"] = pdf_error if item["error"] is None else f"{item['error']}; {pdf_error}"
        files.append(item)
    return {
        "run_id": run_id,
        "generated_at": generated_at,
        "input_root": str(root),
        "total_files": len(files),
        "files": files,
    }
