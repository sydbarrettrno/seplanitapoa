from __future__ import annotations

import base64
import gzip
import hashlib
import json
from datetime import date, timedelta
from functools import lru_cache

from backend import core

CHUNK_DIR = core.DATA_DIR / "final_chunks"
PARTS = [f"part-{i:03d}" for i in range(11)]
EXPECTED_BASE64_CHARS = 62420
EXPECTED_GZIP_BYTES = 46813
EXPECTED_SHA256 = "d28e0b7954d6cef59f66ce6c61e58a692906d99a4fb26cde6ca8de237e3ed9c8"
EXPECTED_ROWS = 6975
BASE_DATE = date(2025, 1, 1)
SOURCE_DATE = date(2026, 8, 22)


def _iso(offset):
    try:
        value = int(offset)
    except (TypeError, ValueError):
        return ""
    if value < 0:
        return ""
    return (BASE_DATE + timedelta(days=value)).isoformat()


def _read_compressed_payload() -> bytes:
    try:
        encoded = "".join((CHUNK_DIR / name).read_text(encoding="ascii") for name in PARTS)
    except Exception as exc:
        raise RuntimeError("Carga bloqueada: chunks da base reconciliada ausentes ou ilegíveis.") from exc
    if len(encoded) != EXPECTED_BASE64_CHARS:
        raise RuntimeError("Carga bloqueada: tamanho base64 da base reconciliada diverge.")
    try:
        compressed = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise RuntimeError("Carga bloqueada: base64 da base reconciliada inválido.") from exc
    if len(compressed) != EXPECTED_GZIP_BYTES:
        raise RuntimeError("Carga bloqueada: tamanho gzip da base reconciliada diverge.")
    if hashlib.sha256(compressed).hexdigest() != EXPECTED_SHA256:
        raise RuntimeError("Carga bloqueada: checksum da base reconciliada diverge.")
    return compressed


@lru_cache(maxsize=1)
def load_rows():
    compressed = _read_compressed_payload()
    try:
        payload = json.loads(gzip.decompress(compressed).decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("Carga bloqueada: payload reconciliado inválido.") from exc

    if payload.get("v") != 6:
        raise RuntimeError("Carga bloqueada: schema público v6 esperado.")
    dictionaries = payload.get("d", {})
    columns = payload.get("c", {})
    required = ("n", "y", "o", "m", "c", "x", "g", "t")
    count = len(columns.get("n", []))
    if count != EXPECTED_ROWS or any(len(columns.get(k, [])) != count for k in required):
        raise RuntimeError("Carga bloqueada: quantidade/colunas divergentes da base validada.")

    def dv(name, idx):
        values = dictionaries.get(name, [])
        try:
            return values[int(idx)]
        except (IndexError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Carga bloqueada: índice inválido em {name}.") from exc

    rows = []
    seen = set()
    for i in range(count):
        year = 2025 + int(columns["y"][i])
        number = int(columns["n"][i])
        pid = f"{year}-{number}"
        if pid in seen:
            raise RuntimeError(f"Carga bloqueada: protocolo duplicado {pid}.")
        seen.add(pid)

        opened = _iso(columns["o"][i])
        moved = _iso(columns["m"][i])
        closed = _iso(columns["c"][i])
        status = dv("StatusOperacional", columns["t"][i])
        category = dv("Categoria", columns["g"][i])
        macro = dv("Macroprocesso", columns["x"][i])
        moved_date = core._as_date(moved)
        days_without = max(0, (SOURCE_DATE - moved_date).days) if moved_date else -1

        rows.append({
            "ProtocoloID": pid,
            "NumeroAnoOriginal": f"{number}/{year}",
            "ProtocoloAno": year,
            "DataAbertura": opened,
            "UltimoTramiteDataHora": moved,
            "DataEncerramento": closed,
            "Macroprocesso": macro,
            "Categoria": category,
            "StatusOperacional": status,
            "GargaloOperacional": "",
            "DiasSemMovimento": days_without,
        })

    audit = core._audit_rows(rows)
    if not audit["ok"]:
        raise RuntimeError(f"Carga bloqueada pela auditoria: {audit}")
    return rows
