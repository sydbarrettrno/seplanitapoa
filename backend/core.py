from __future__ import annotations

import base64
import gzip
import hashlib
import io
import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
META_PATH = DATA_DIR / "metadata.json"

TERMINAL_SITUATIONS = {"ENCERRADO", "ARQUIVADO", "CANCELADO", "CONCLUÍDO", "CONCLUIDO"}
AGING_BANDS = (
    ("0–15", 0, 15),
    ("16–30", 16, 30),
    ("31–60", 31, 60),
    ("61–90", 61, 90),
    ("91–120", 91, 120),
    (">120", 121, None),
)

FORBIDDEN_KEYS = {
    "RequerenteNomeRazao",
    "RequerenteCPFCNPJ",
    "ResponsavelCPFCNPJ",
    "ObservacaoAbertura",
    "UltimoTramiteObservacao",
}

INDICATOR_COVERAGE = [
    {"id": "KPI01", "name": "Processos recebidos", "status": "DISPONÍVEL", "reason": "DataAbertura + ProtocoloID."},
    {"id": "KPI02", "name": "Processos concluídos — produção", "status": "DISPONÍVEL", "reason": "DataEncerramento formal no período."},
    {"id": "KPI03", "name": "Estoque pendente", "status": "DISPONÍVEL", "reason": "Sem DataEncerramento e Situação não terminal."},
    {"id": "KPI04", "name": "Tempo de tramitação", "status": "DISPONÍVEL", "reason": "Abertura → encerramento; mediana, média e P90."},
    {"id": "KPI05", "name": "% parados > X dias", "status": "DISPONÍVEL", "reason": "DiasSemMovimento do estoque atual."},
    {"id": "KPI06", "name": "% concluído dentro do prazo", "status": "FONTE NÃO INTEGRADA", "reason": "DIM_PRAZOS oficial e regras de suspensão ainda não disponíveis."},
    {"id": "KPI07", "name": "Diligências por processo", "status": "FONTE NÃO INTEGRADA", "reason": "Exige histórico completo de eventos; último trâmite não é suficiente."},
    {"id": "KPI08", "name": "Fiscalizações realizadas", "status": "FONTE NÃO INTEGRADA", "reason": "Status de fiscalização não comprova ato executado com data."},
    {"id": "KPI09", "name": "Denúncias recebidas/respondidas", "status": "TAXONOMIA PENDENTE", "reason": "A base ainda combina Denúncia / Fiscalização."},
    {"id": "KPI10", "name": "Projetos públicos por etapa", "status": "BASE COMPLEMENTAR", "reason": "Protocolo não representa carteira de projetos."},
    {"id": "KPI11", "name": "Pendências por responsável/setor", "status": "PARCIAL", "reason": "Disponível como gargalo operacional inferido; não equivale ao responsável formal."},
]


@dataclass(frozen=True)
class Query:
    start: date
    end: date
    threshold: int = 30
    category: str = ""
    status: str = ""
    owner: str = ""
    macro: str = ""
    search: str = ""
    limit: int = 200
    offset: int = 0
    recordset: str = "all"


def _as_date(value: str | None) -> date | None:
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _is_terminal(row: dict[str, Any]) -> bool:
    return _clean(row.get("SituacaoAtual")).upper() in TERMINAL_SITUATIONS


def _is_stock(row: dict[str, Any]) -> bool:
    return not _clean(row.get("DataEncerramento")) and not _is_terminal(row)


def _in_period(value: str | None, start: date, end: date) -> bool:
    d = _as_date(value)
    return d is not None and start <= d <= end


def _days_between(a: str | None, b: str | None) -> int | None:
    da, db = _as_date(a), _as_date(b)
    if da is None or db is None or db < da:
        return None
    return (db - da).days


def _percentile(values: list[int], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return float(xs[0])
    pos = (len(xs) - 1) * p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(xs[lo])
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def _median(values: list[int]) -> float | None:
    return _percentile(values, 0.5)


def _mean(values: list[int]) -> float | None:
    return sum(values) / len(values) if values else None


def _pct(num: int, den: int) -> float | None:
    return (num / den * 100.0) if den else None


def _top_counts(rows: Iterable[dict[str, Any]], key: str, limit: int = 12) -> list[dict[str, Any]]:
    counts = Counter(_clean(r.get(key)) or "Não identificado" for r in rows)
    return [{"name": name, "value": value} for name, value in counts.most_common(limit)]


def _month_keys(start: date, end: date) -> list[str]:
    y, m = start.year, start.month
    out: list[str] = []
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return out


def _audit_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ids = [_clean(r.get("ProtocoloID")) for r in rows]
    duplicates = len(ids) - len(set(ids))
    missing_ids = sum(1 for x in ids if not x)
    invalid_last = 0
    invalid_close = 0
    forbidden_present: set[str] = set()

    for r in rows:
        forbidden_present.update(FORBIDDEN_KEYS.intersection(r.keys()))
        opened = _as_date(r.get("DataAbertura"))
        moved = _as_date(r.get("UltimoTramiteDataHora"))
        closed = _as_date(r.get("DataEncerramento"))
        if opened and moved and moved < opened:
            invalid_last += 1
        if opened and closed and closed < opened:
            invalid_close += 1

    ok = duplicates == 0 and missing_ids == 0 and invalid_last == 0 and invalid_close == 0 and not forbidden_present
    return {
        "ok": ok,
        "rows": len(rows),
        "unique_protocols": len(set(ids)),
        "duplicates": duplicates,
        "missing_ids": missing_ids,
        "invalid_last_before_open": invalid_last,
        "invalid_close_before_open": invalid_close,
        "forbidden_fields_present": sorted(forbidden_present),
    }


@lru_cache(maxsize=1)
def metadata() -> dict[str, Any]:
    return json.loads(META_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_rows() -> list[dict[str, Any]]:
    artifact = metadata().get("artifact", {})
    part_names = artifact.get("parts") or []
    if not part_names:
        raise RuntimeError("Carga bloqueada: manifesto do dataset sem partes.")

    storage_dir = DATA_DIR / str(artifact.get("directory", "."))
    encoded = "".join((storage_dir / name).read_text(encoding="ascii").strip() for name in part_names)
    try:
        compressed = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise RuntimeError("Carga bloqueada: artefato Base64 inválido.") from exc

    expected_sha = str(artifact.get("gzip_sha256", "")).strip().lower()
    if expected_sha and hashlib.sha256(compressed).hexdigest() != expected_sha:
        raise RuntimeError("Carga bloqueada: checksum do dataset diverge dos metadados.")

    try:
        with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode="rb") as gz:
            payload = json.loads(gz.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("Carga bloqueada: dataset comprimido inválido.") from exc

    if artifact.get("format") == "columnar-v2":
        if not isinstance(payload, dict) or payload.get("v") != 2:
            raise RuntimeError("Dataset inválido: transporte columnar v2 esperado.")
        d, c = payload.get("d", {}), payload.get("c", {})
        count = len(c.get("n", []))
        required = ("n", "y", "o", "m", "c", "s", "x", "g", "t", "w", "p", "i", "r", "q")
        if any(len(c.get(k, [])) != count for k in required):
            raise RuntimeError("Dataset inválido: colunas com comprimentos divergentes.")

        def iso(v: Any) -> str:
            if not v:
                return ""
            s = str(int(v))
            if len(s) != 8:
                return ""
            return f"{s[:4]}-{s[4:6]}-{s[6:8]}"

        def dv(name: str, idx: int) -> str:
            values = d.get(name, [])
            try:
                return values[idx]
            except (IndexError, TypeError):
                raise RuntimeError(f"Dataset inválido: índice fora do dicionário {name}.")

        rows = []
        for j in range(count):
            year = 2025 + int(c["y"][j])
            number = int(c["n"][j])
            rows.append({
                "ProtocoloID": f"{year}-{number}",
                "NumeroAnoOriginal": f"{number}/{year}",
                "ProtocoloAno": year,
                "DataAbertura": iso(c["o"][j]),
                "UltimoTramiteDataHora": iso(c["m"][j]),
                "DataEncerramento": iso(c["c"][j]),
                "SituacaoAtual": dv("SituacaoAtual", int(c["s"][j])),
                "Macroprocesso": dv("Macroprocesso", int(c["x"][j])),
                "Categoria": dv("Categoria", int(c["g"][j])),
                "StatusOperacional": dv("StatusOperacional", int(c["t"][j])),
                "ResponsavelGargalo": dv("ResponsavelGargalo", int(c["w"][j])),
                "Prioridade": dv("Prioridade", int(c["p"][j])),
                "DiasSemMovimento": int(c["i"][j]),
                "FaixaInatividade": "",
                "Inscricao": c["r"][j] or "",
                "NecessitaRevisao": "SIM" if int(c["q"][j]) else "NÃO",
                "ConfiancaCategoria": None,
            })
    else:
        rows = payload

    if not isinstance(rows, list):
        raise RuntimeError("Dataset inválido: esperado array JSON.")
    audit = _audit_rows(rows)
    if not audit["ok"]:
        raise RuntimeError(f"Carga bloqueada pela auditoria: {audit}")
    if len(rows) != int(metadata().get("source_rows", -1)):
        raise RuntimeError("Carga bloqueada: total do dataset diverge dos metadados.")
    return rows


def health() -> dict[str, Any]:
    rows = load_rows()
    audit = _audit_rows(rows)
    return {
        "status": "ok" if audit["ok"] else "error",
        "service": "SEPLAN Gestão à Vista",
        "dataset": metadata().get("dataset"),
        "source_updated_at": metadata().get("source_updated_at"),
        "audit": audit,
    }


def query_from_params(params: dict[str, str]) -> Query:
    meta = metadata()
    default = meta["default_period"]
    start = _as_date(params.get("from")) or date.fromisoformat(default["from"])
    end = _as_date(params.get("to")) or date.fromisoformat(default["to"])
    if end < start:
        start, end = end, start

    try:
        threshold = max(1, min(3650, int(params.get("threshold", meta.get("default_threshold_days", 30)))))
    except (TypeError, ValueError):
        threshold = int(meta.get("default_threshold_days", 30))

    try:
        limit = max(1, min(500, int(params.get("limit", 200))))
    except (TypeError, ValueError):
        limit = 200
    try:
        offset = max(0, int(params.get("offset", 0)))
    except (TypeError, ValueError):
        offset = 0

    return Query(
        start=start,
        end=end,
        threshold=threshold,
        category=_clean(params.get("category")),
        status=_clean(params.get("status")),
        owner=_clean(params.get("owner")),
        macro=_clean(params.get("macro")),
        search=_clean(params.get("q")).casefold(),
        limit=limit,
        offset=offset,
        recordset=(params.get("recordset", "all") if params.get("recordset", "all") in {"all", "received", "concluded", "stock", "stopped"} else "all"),
    )


def _matches_scope(row: dict[str, Any], q: Query) -> bool:
    if q.category and _clean(row.get("Categoria")) != q.category:
        return False
    if q.status and _clean(row.get("StatusOperacional")) != q.status:
        return False
    if q.owner and _clean(row.get("ResponsavelGargalo")) != q.owner:
        return False
    if q.macro and _clean(row.get("Macroprocesso")) != q.macro:
        return False
    if q.search:
        hay = " | ".join(
            _clean(row.get(k)).casefold()
            for k in ("ProtocoloID", "NumeroAnoOriginal", "Inscricao", "Categoria", "ResponsavelGargalo")
        )
        if q.search not in hay:
            return False
    return True


def _record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocol": row.get("NumeroAnoOriginal") or row.get("ProtocoloID"),
        "protocol_id": row.get("ProtocoloID"),
        "opened": row.get("DataAbertura"),
        "last_movement": row.get("UltimoTramiteDataHora"),
        "closed": row.get("DataEncerramento") or None,
        "category": row.get("Categoria"),
        "macroprocess": row.get("Macroprocesso"),
        "status": row.get("StatusOperacional"),
        "situation": row.get("SituacaoAtual"),
        "owner": row.get("ResponsavelGargalo"),
        "priority": row.get("Prioridade"),
        "days_without_movement": row.get("DiasSemMovimento") if int(row.get("DiasSemMovimento", -1)) >= 0 else None,
        "inscription": row.get("Inscricao") or None,
        "needs_review": str(row.get("NecessitaRevisao", "NÃO")).upper() == "SIM",
        "category_confidence": row.get("ConfiancaCategoria"),
    }


def dashboard(query: Query) -> dict[str, Any]:
    rows = load_rows()
    scoped = [r for r in rows if _matches_scope(r, query)]
    received = [r for r in scoped if _in_period(r.get("DataAbertura"), query.start, query.end)]
    concluded = [r for r in scoped if _clean(r.get("DataEncerramento")) and _in_period(r.get("DataEncerramento"), query.start, query.end)]
    stock = [r for r in scoped if _is_stock(r)]

    eligible_stock = [r for r in stock if int(r.get("DiasSemMovimento", -1)) >= 0]
    stopped = [r for r in eligible_stock if int(r.get("DiasSemMovimento", -1)) > query.threshold]

    turnaround = [
        d for d in (_days_between(r.get("DataAbertura"), r.get("DataEncerramento")) for r in concluded) if d is not None
    ]

    flow = {m: {"month": m, "received": 0, "concluded": 0} for m in _month_keys(query.start, query.end)}
    for r in received:
        d = _as_date(r.get("DataAbertura"))
        if d:
            key = f"{d.year:04d}-{d.month:02d}"
            if key in flow:
                flow[key]["received"] += 1
    for r in concluded:
        d = _as_date(r.get("DataEncerramento"))
        if d:
            key = f"{d.year:04d}-{d.month:02d}"
            if key in flow:
                flow[key]["concluded"] += 1

    aging: list[dict[str, Any]] = []
    for name, low, high in AGING_BANDS:
        n = 0
        for r in eligible_stock:
            days = int(r.get("DiasSemMovimento", -1))
            if days >= low and (high is None or days <= high):
                n += 1
        aging.append({"name": name, "value": n})
    unknown_aging = len(stock) - len(eligible_stock)
    if unknown_aging:
        aging.append({"name": "Sem informação", "value": unknown_aging})

    record_source = {
        "all": scoped,
        "received": received,
        "concluded": concluded,
        "stock": stock,
        "stopped": stopped,
    }[query.recordset]
    sorted_records = sorted(
        record_source,
        key=lambda r: (_clean(r.get("UltimoTramiteDataHora")), _clean(r.get("ProtocoloID"))),
        reverse=True,
    )
    page = sorted_records[query.offset : query.offset + query.limit]

    all_rows = rows
    options = {
        "categories": sorted({_clean(r.get("Categoria")) for r in all_rows if _clean(r.get("Categoria"))}, key=str.casefold),
        "statuses": sorted({_clean(r.get("StatusOperacional")) for r in all_rows if _clean(r.get("StatusOperacional"))}, key=str.casefold),
        "owners": sorted({_clean(r.get("ResponsavelGargalo")) for r in all_rows if _clean(r.get("ResponsavelGargalo"))}, key=str.casefold),
        "macroprocesses": sorted({_clean(r.get("Macroprocesso")) for r in all_rows if _clean(r.get("Macroprocesso"))}, key=str.casefold),
    }

    metrics = {
        "received": len(received),
        "concluded": len(concluded),
        "stock": len(stock),
        "turnaround": {
            "eligible": len(turnaround),
            "median_days": round(_median(turnaround), 1) if turnaround else None,
            "mean_days": round(_mean(turnaround), 1) if turnaround else None,
            "p90_days": round(_percentile(turnaround, 0.9), 1) if turnaround else None,
        },
        "stopped": {
            "threshold_days": query.threshold,
            "count": len(stopped),
            "eligible_stock": len(eligible_stock),
            "percent": round(_pct(len(stopped), len(eligible_stock)), 1) if eligible_stock else None,
        },
        "period_balance": len(received) - len(concluded),
        "completion_rate": round(_pct(len(concluded), len(received)), 1) if received else None,
    }

    return {
        "ok": True,
        "meta": {
            "dataset": metadata().get("dataset"),
            "source_rows": metadata().get("source_rows"),
            "source_updated_at": metadata().get("source_updated_at"),
            "schema_version": metadata().get("schema_version"),
            "privacy_note": metadata().get("privacy", {}).get("note"),
            "scope_rows": len(scoped),
            "period": {"from": query.start.isoformat(), "to": query.end.isoformat()},
        },
        "metrics": metrics,
        "charts": {
            "flow": list(flow.values()),
            "aging": aging,
            "categories": _top_counts(stock, "Categoria", 12),
            "owners": _top_counts(stock, "ResponsavelGargalo", 12),
            "statuses": _top_counts(stock, "StatusOperacional", 12),
        },
        "records": {
            "total": len(record_source),
            "offset": query.offset,
            "limit": query.limit,
            "recordset": query.recordset,
            "items": [_record(r) for r in page],
        },
        "options": options,
        "indicator_coverage": INDICATOR_COVERAGE,
        "warnings": [
            "Estoque é posição atual; o filtro de período afeta recebidos, concluídos e tempo de tramitação, não reconstrói estoque histórico.",
            "Responsável exibido é o gargalo operacional disponível na base e pode não coincidir com o responsável formal.",
        ],
    }
