from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.final_entry import dashboard, health, query_from_params  # noqa: E402

EXPECTED = {
    "rows": 6975,
    "received_default": 2810,
    "concluded_operational": 2181,
    "concluded_formal": 1876,
    "stock": 2208,
    "internal_queue": 1548,
    "external_wait": 627,
    "suspended": 33,
    "stopped_30_internal": 1089,
    "turnaround_median": 54.0,
    "turnaround_p90": 229.0,
}

h = health()
assert h["status"] == "ok", h
assert h["audit"]["rows"] == EXPECTED["rows"], h
assert h["audit"]["unique_protocols"] == EXPECTED["rows"], h
assert h["audit"]["stock"] == EXPECTED["stock"], h
assert h["audit"]["internal_queue"] == EXPECTED["internal_queue"], h
assert h["audit"]["external_wait"] == EXPECTED["external_wait"], h
assert h["audit"]["suspended"] == EXPECTED["suspended"], h

d = dashboard(query_from_params({}))
m = d["metrics"]
assert m["received"] == EXPECTED["received_default"], m
assert m["concluded"] == EXPECTED["concluded_operational"], m
assert m["concluded_formal"] == EXPECTED["concluded_formal"], m
assert m["stock"] == EXPECTED["stock"], m
assert m["internal_queue"] == EXPECTED["internal_queue"], m
assert m["external_wait"] == EXPECTED["external_wait"], m
assert m["suspended"] == EXPECTED["suspended"], m
assert m["stopped"]["count"] == EXPECTED["stopped_30_internal"], m
assert round(m["stopped"]["percent"], 1) == 70.3, m
assert m["turnaround"]["median_days"] == EXPECTED["turnaround_median"], m
assert m["turnaround"]["p90_days"] == EXPECTED["turnaround_p90"], m
assert len(d["charts"]["flow"]) == 8, d["charts"]["flow"]
assert len(d["records"]["items"]) <= 200
assert any(x["id"] == "KPI06" and x["status"] != "DISPONÍVEL" for x in d["indicator_coverage"])

cmp = d["management"]["comparison"]
assert cmp["previous"]["received"] == 2753, cmp
assert cmp["current"]["cohort_concluded_formal"] == 1302, cmp
assert cmp["previous"]["cohort_concluded_formal"] == 1202, cmp
assert cmp["received_change_percent"] == 2.1, cmp
assert cmp["cohort_formal_change_percent"] == 8.3, cmp
assert d["management"]["data_quality"]["operational_closed_without_formal_date"] == 735

print(json.dumps({
    "status": "VALIDADO",
    "health": h,
    "default_metrics": m,
    "comparison": cmp,
}, ensure_ascii=False, indent=2))
