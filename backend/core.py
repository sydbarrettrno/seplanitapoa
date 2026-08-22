from __future__ import annotations

import base64
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
META_PATH = DATA_DIR / "metadata.json"

TERMINAL_STATUSES = {"ENCERRADO ADMINISTRATIVO", "ARQUIVADO", "CANCELADO"}
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
    "ResponsavelGargalo",
    "Inscricao",
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
    {"id": "KPI11", "name": "Pendências por setor/gargalo operacional", "status": "PARCIAL", "reason": "Derivado do status operacional; nomes de pessoas/empresas não são publicados."},
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
    return _clean(row.get("StatusOperacional")).upper() in TERMINAL_STATUSES


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
    parts = artifact.get("parts", [])
    directory = DATA_DIR / str(artifact.get("directory", "safe_chunks"))
    if not parts or not directory.is_dir():
        raise RuntimeError("Carga bloqueada: transporte sanitizado ausente.")
    try:
        encoded = "".join((directory / str(name)).read_text(encoding="ascii") for name in parts)
        compressed = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise RuntimeError("Carga bloqueada: transporte base64 inválido.") from exc

    expected_sha = str(artifact.get("gzip_sha256", "")).strip().lower()
    if expected_sha and hashlib.sha256(compressed).hexdigest() != expected_sha:
        raise RuntimeError("Carga bloqueada: checksum do transporte diverge dos metadados.")
    expected_bytes = int(artifact.get("gzip_bytes", len(compressed)))
    if len(compressed) != expected_bytes:
        raise RuntimeError("Carga bloqueada: tamanho do transporte diverge dos metadados.")

    try:
        raw = gzip.decompress(compressed)
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("Carga bloqueada: dataset compactado inválido.") from exc

    if payload.get("v") != 6 or not isinstance(payload.get("d"), dict) or not isinstance(payload.get("c"), dict):
        raise RuntimeError("Dataset inválido: transporte público v6 esperado.")
    d = payload["d"]
    columns = payload["c"]

    required = ("n", "y", "o", "m", "c", "x", "g", "t")
    count = len(columns.get("n", []))
    if count == 0 or any(len(columns.get(k, [])) != count for k in required):
        raise RuntimeError("Dataset inválido: colunas com comprimentos divergentes.")

    from datetime import timedelta
    base_date = date(2025, 1, 1)
    source_ref = _as_date(metadata().get("source_updated_at")) or date.today()

    def iso(v: Any) -> str:
        try:
            offset = int(v)
        except (TypeError, ValueError):
            return ""
        if offset < 0:
            return ""
        return (base_date + timedelta(days=offset)).isoformat()

    bottleneck_by_status = {
        "Em tramitação": "SEPLAN / Tramitação",
        "Fiscalização / vistoria": "SEPLAN / Fiscalização",
        "Em análise técnica": "SEPLAN / Análise técnica",
        "Exigência / pendência": "Exigência externa / Responsável técnico",
        "Apto / aguardando retirada": "Aguardando retirada",
        "Encerrado administrativo": "Não aplicável",
        "Aguardando pagamento": "Aguardando pagamento",
        "Paralisado / revisar": "SEPLAN / Revisão",
        "Cancelado": "Não aplicável",
        "Arquivado": "Não aplicável",
    }

    def dv(name: str, idx: int) -> str:
        values = d.get(name, [])
        try:
            return values[idx]
        except (IndexError, TypeError):
            raise RuntimeError(f"Dataset inválido: índice fora do dicionário {name}.")

    rows = []
    for j in range(count):
        year = 2025 + int(columns["y"][j])
        number = int(columns["n"][j])
        status = dv("StatusOperacional", int(columns["t"][j]))
        moved = int(columns["m"][j])
        rows.append({
            "ProtocoloID": f"{year}-{number}",
            "NumeroAnoOriginal": f"{number}/{year}",
            "ProtocoloAno": year,
            "DataAbertura": iso(columns["o"][j]),
            "UltimoTramiteDataHora": iso(moved),
            "DataEncerramento": iso(columns["c"][j]),
            "Macroprocesso": dv("Macroprocesso", int(columns["x"][j])),
            "Categoria": dv("Categoria", int(columns["g"][j])),
            "StatusOperacional": status,
            "GargaloOperacional": bottleneck_by_status.get(status, "SEPLAN / Tramitação"),
            "DiasSemMovimento": max(0, (source_ref - (base_date + timedelta(days=moved))).days) if moved >= 0 else -1,
        })

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
    if q.owner and _clean(row.get("GargaloOperacional")) != q.owner:
        return False
    if q.macro and _clean(row.get("Macroprocesso")) != q.macro:
        return False
    if q.search:
        hay = " | ".join(
            _clean(row.get(k)).casefold()
            for k in ("ProtocoloID", "NumeroAnoOriginal", "Categoria", "GargaloOperacional")
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
        "owner": row.get("GargaloOperacional"),
        "days_without_movement": row.get("DiasSemMovimento") if int(row.get("DiasSemMovimento", -1)) >= 0 else None,
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
        "owners": sorted({_clean(r.get("GargaloOperacional")) for r in all_rows if _clean(r.get("GargaloOperacional"))}, key=str.casefold),
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
            "owners": _top_counts(stock, "GargaloOperacional", 12),
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
