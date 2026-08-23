"""Camada executiva do dashboard SEPLAN.

Regras:
- protocolos aptos/aguardando retirada não compõem estoque operacional;
- produção formal continua exigindo DataEncerramento;
- métricas de gestão explicitam pressão de fluxo, envelhecimento, visibilidade
  do processo e lacunas de registro sem inventar metas ou causas.
"""
from backend import core

READY_STATUS = "APTO / AGUARDANDO RETIRADA"
GENERIC_TRANSIT_STATUS = "EM TRAMITAÇÃO"
EXTERNAL_STATUS = "EXIGÊNCIA / PENDÊNCIA"

core.TERMINAL_STATUSES = {
    *core.TERMINAL_STATUSES,
    READY_STATUS,
}

health = core.health
query_from_params = core.query_from_params


def _pct(num: int, den: int) -> float | None:
    return round(num / den * 100.0, 1) if den else None


def dashboard(query):
    payload = core.dashboard(query)
    rows = core.load_rows()
    scoped = [r for r in rows if core._matches_scope(r, query)]

    received = [r for r in scoped if core._in_period(r.get("DataAbertura"), query.start, query.end)]
    concluded = [r for r in scoped if core._clean(r.get("DataEncerramento")) and core._in_period(r.get("DataEncerramento"), query.start, query.end)]
    stock = [r for r in scoped if core._is_stock(r)]

    ready_without_close = [
        r for r in scoped
        if core._clean(r.get("StatusOperacional")).upper() == READY_STATUS
        and not core._clean(r.get("DataEncerramento"))
    ]
    ready_opened_in_period = [
        r for r in ready_without_close
        if core._in_period(r.get("DataAbertura"), query.start, query.end)
    ]

    old_120 = [r for r in stock if int(r.get("DiasSemMovimento", -1)) > 120]
    generic_transit = [
        r for r in stock
        if core._clean(r.get("StatusOperacional")).upper() == GENERIC_TRANSIT_STATUS
    ]
    external_wait = [
        r for r in stock
        if core._clean(r.get("StatusOperacional")).upper() == EXTERNAL_STATUS
    ]

    formal_absorption = _pct(len(concluded), len(received))
    minimum_operational_output = len(concluded) + len(ready_opened_in_period)
    minimum_operational_absorption = _pct(minimum_operational_output, len(received))

    payload["management"] = {
        "flow": {
            "received": len(received),
            "formal_concluded": len(concluded),
            "formal_absorption_percent": formal_absorption,
            "formal_gap": len(received) - len(concluded),
            "ready_without_formal_close_opened_in_period": len(ready_opened_in_period),
            "minimum_operational_output": minimum_operational_output,
            "minimum_operational_absorption_percent": minimum_operational_absorption,
            "minimum_operational_gap": len(received) - minimum_operational_output,
        },
        "backlog": {
            "stock": len(stock),
            "over_120_days": len(old_120),
            "over_120_percent": _pct(len(old_120), len(stock)),
        },
        "visibility": {
            "generic_transit": len(generic_transit),
            "generic_transit_percent": _pct(len(generic_transit), len(stock)),
        },
        "external": {
            "waiting_external": len(external_wait),
            "waiting_external_percent": _pct(len(external_wait), len(stock)),
        },
        "data_quality": {
            "ready_without_formal_close_total": len(ready_without_close),
            "ready_without_formal_close_opened_in_period": len(ready_opened_in_period),
        },
    }
    return payload
