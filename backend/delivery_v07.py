from __future__ import annotations

from backend import core
from backend import delivery_core as base

query_from_params = base.query_from_params


def _period_rows(rows, field, query):
    return [r for r in rows if core._in_period(r.get(field), query.start, query.end)]


def dashboard(query):
    data = base.dashboard(query)

    rows = core.load_rows()
    scoped = [r for r in rows if core._matches_scope(r, query)]
    received = _period_rows(scoped, "DataAbertura", query)
    concluded = _period_rows(scoped, "DataConclusaoOperacional", query)
    stock = [r for r in scoped if base._is_stock(r)]

    inspections_received = [r for r in received if core._clean(r.get("Categoria")) == "Fiscalização"]
    inspections_concluded = [r for r in concluded if core._clean(r.get("Categoria")) == "Fiscalização"]
    inspections_stock = [r for r in stock if core._clean(r.get("Categoria")) == "Fiscalização"]

    project_rows = [r for r in scoped if core._clean(r.get("Macroprocesso")) == "Projetos e Obras Públicas"]
    project_received = _period_rows(project_rows, "DataAbertura", query)
    project_concluded = _period_rows(project_rows, "DataConclusaoOperacional", query)
    project_stock = [r for r in project_rows if base._is_stock(r)]

    data["meta"]["taxonomy_version"] = "V07"
    data["meta"]["category_count"] = len({core._clean(r.get("Categoria")) for r in rows})

    data["charts"]["received_categories"] = base._top(received, "Categoria", 12)
    data["charts"]["concluded_categories"] = base._top(concluded, "Categoria", 12)
    data["charts"]["public_projects_status"] = base._top(project_stock, "StatusOperacional", 8)

    data["management"]["inspections"] = {
        "protocols_received": len(inspections_received),
        "protocols_concluded_operational": len(inspections_concluded),
        "protocols_stock": len(inspections_stock),
        "note": "A categoria mede protocolos de fiscalização; não equivale ao total de vistorias/atos realizados."
    }
    data["management"]["public_projects"] = {
        "protocols_identified": len(project_rows),
        "protocols_received": len(project_received),
        "protocols_concluded_operational": len(project_concluded),
        "protocols_stock": len(project_stock),
        "note": "São protocolos relacionados a projetos e obras públicas; não representam quantidade de projetos únicos."
    }

    return data


def health():
    data = base.health()
    rows = core.load_rows()
    categories = {core._clean(r.get("Categoria")) for r in rows}
    data["taxonomy_version"] = "V07"
    data["category_count"] = len(categories)
    data["taxonomy_ok"] = len(rows) == 6975 and len(categories) == 42
    return data
