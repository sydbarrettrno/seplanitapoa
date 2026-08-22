import unittest

from backend.core import dashboard, health, load_rows, query_from_params


class CoreTests(unittest.TestCase):
    def test_data_audit(self):
        h = health()
        self.assertEqual(h["status"], "ok")
        self.assertEqual(h["audit"]["rows"], 6957)
        self.assertEqual(h["audit"]["unique_protocols"], 6957)
        self.assertEqual(h["audit"]["duplicates"], 0)
        self.assertEqual(h["audit"]["missing_ids"], 0)
        self.assertEqual(h["audit"]["invalid_last_before_open"], 0)
        self.assertEqual(h["audit"]["invalid_close_before_open"], 0)
        self.assertEqual(h["audit"]["forbidden_fields_present"], [])

    def test_default_metrics(self):
        m = dashboard(query_from_params({}))["metrics"]
        self.assertEqual(m["received"], 2792)
        self.assertEqual(m["concluded"], 1873)
        self.assertEqual(m["stock"], 2856)
        self.assertEqual(m["stopped"]["count"], 2114)
        self.assertEqual(m["stopped"]["percent"], 74.0)
        self.assertEqual(m["turnaround"]["median_days"], 54.0)
        self.assertEqual(m["turnaround"]["p90_days"], 237.0)

    def test_period_does_not_reconstruct_stock(self):
        a = dashboard(query_from_params({"from": "2025-01-01", "to": "2025-12-31"}))["metrics"]
        b = dashboard(query_from_params({"from": "2026-01-01", "to": "2026-08-20"}))["metrics"]
        self.assertEqual(a["stock"], b["stock"])
        self.assertNotEqual(a["received"], b["received"])

    def test_category_filter(self):
        d = dashboard(query_from_params({"category": "Habite-se"}))
        self.assertTrue(d["meta"]["scope_rows"] > 0)
        self.assertTrue(all(x["category"] == "Habite-se" for x in d["records"]["items"]))

    def test_pii_not_in_dataset_schema(self):
        forbidden = {"RequerenteNomeRazao", "RequerenteCPFCNPJ", "ObservacaoAbertura", "UltimoTramiteObservacao"}
        self.assertFalse(forbidden.intersection(load_rows()[0].keys()))

    def test_recordsets_and_thresholds(self):
        base = dashboard(query_from_params({"limit": "500"}))
        for name, expected in (("received", 2792), ("concluded", 1873), ("stock", 2856), ("stopped", 2114)):
            d = dashboard(query_from_params({"recordset": name, "limit": "500"}))
            self.assertEqual(d["records"]["recordset"], name)
            self.assertEqual(d["records"]["total"], expected)
        d60 = dashboard(query_from_params({"threshold": "60"}))
        self.assertLessEqual(d60["metrics"]["stopped"]["count"], base["metrics"]["stopped"]["count"])

    def test_search_and_pagination(self):
        rows = load_rows()
        target = rows[0]
        q = target["ProtocoloID"]
        d = dashboard(query_from_params({"q": q, "limit": "10"}))
        self.assertGreaterEqual(d["records"]["total"], 1)
        self.assertTrue(any(x["protocol_id"] == q for x in d["records"]["items"]))
        page = dashboard(query_from_params({"limit": "10", "offset": "10"}))
        self.assertEqual(page["records"]["offset"], 10)
        self.assertLessEqual(len(page["records"]["items"]), 10)

    def test_invalid_params_are_safely_normalized(self):
        q = query_from_params({"from": "2026-08-20", "to": "2026-01-01", "threshold": "x", "limit": "99999", "offset": "-8", "recordset": "bad"})
        self.assertLessEqual(q.start, q.end)
        self.assertEqual(q.threshold, 30)
        self.assertEqual(q.limit, 500)
        self.assertEqual(q.offset, 0)
        self.assertEqual(q.recordset, "all")

    def test_unavailable_indicators_are_explicit(self):
        coverage = {x["id"]: x for x in dashboard(query_from_params({}))["indicator_coverage"]}
        for kpi in ("KPI06", "KPI07", "KPI08", "KPI09", "KPI10"):
            self.assertNotEqual(coverage[kpi]["status"], "DISPONÍVEL")
        self.assertEqual(coverage["KPI11"]["status"], "PARCIAL")


if __name__ == "__main__":
    unittest.main()
