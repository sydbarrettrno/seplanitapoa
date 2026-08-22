from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.core import dashboard, health, query_from_params  # noqa: E402

EXPECTED = {
    "rows": 6957,
    "received_default": 2792,
    "concluded_default": 1873,
    "stock": 2856,
    "stopped_30": 2114,
    "turnaround_median": 54.0,
    "turnaround_p90": 237.0,
}

h = health()
assert h["status"] == "ok", h
assert h["audit"]["rows"] == EXPECTED["rows"], h
assert h["audit"]["duplicates"] == 0, h
assert h["audit"]["forbidden_fields_present"] == [], h

d = dashboard(query_from_params({}))
m = d["metrics"]
assert m["received"] == EXPECTED["received_default"], m
assert m["concluded"] == EXPECTED["concluded_default"], m
assert m["stock"] == EXPECTED["stock"], m
assert m["stopped"]["count"] == EXPECTED["stopped_30"], m
assert m["turnaround"]["median_days"] == EXPECTED["turnaround_median"], m
assert m["turnaround"]["p90_days"] == EXPECTED["turnaround_p90"], m
assert len(d["charts"]["flow"]) == 8, d["charts"]["flow"]
assert len(d["records"]["items"]) <= 200
assert any(x["id"] == "KPI06" and x["status"] != "DISPONÍVEL" for x in d["indicator_coverage"])

print(json.dumps({
    "status": "VALIDADO",
    "health": h,
    "default_metrics": m,
}, ensure_ascii=False, indent=2))
