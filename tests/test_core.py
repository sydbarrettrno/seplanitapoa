import unittest

from backend.final_entry import dashboard, health, query_from_params
from backend.final_data import load_rows


class CoreTests(unittest.TestCase):
    def test_data_audit(self):
        h = health()
        self.assertEqual(h["status"], "ok")
        self.assertEqual(h["audit"]["rows"], 6975)
        self.assertEqual(h["audit"]["unique_protocols"], 6975)
        self.assertEqual(h["audit"]["stock"], 2208)
        self.assertEqual(h["audit"]["internal_queue"], 1548)
        self.assertEqual(h["audit"]["external_wait"], 627)
        self.assertEqual(h["audit"]["suspended"], 33)

    def test_default_metrics(self):
        d = dashboard(query_from_params({}))
        m = d["metrics"]
        self.assertEqual(m["received"], 2810)
        self.assertEqual(m["concluded"], 2181)
        self.assertEqual(m["concluded_formal"], 1876)
        self.assertEqual(m["stock"], 2208)
        self.assertEqual(m["internal_queue"], 1548)
        self.assertEqual(m["external_wait"], 627)
        self.assertEqual(m["suspended"], 33)
        self.assertEqual(m["stopped"]["count"], 1089)
        self.assertEqual(round(m["stopped"]["percent"], 1), 70.3)
        self.assertEqual(m["turnaround"]["median_days"], 54.0)
        self.assertEqual(m["turnaround"]["p90_days"], 229.0)

    def test_reconciliation(self):
        m = dashboard(query_from_params({}))["metrics"]
        self.assertEqual(m["stock"], m["internal_queue"] + m["external_wait"] + m["suspended"])
        self.assertEqual(m["stock"], 2208)

    def test_same_period_comparison(self):
        cmp = dashboard(query_from_params({}))["management"]["comparison"]
        self.assertEqual(cmp["current"]["received"], 2810)
        self.assertEqual(cmp["previous"]["received"], 2753)
        self.assertEqual(cmp["received_change_percent"], 2.1)
        self.assertEqual(cmp["current"]["cohort_concluded_formal"], 1302)
        self.assertEqual(cmp["previous"]["cohort_concluded_formal"], 1202)
        self.assertEqual(cmp["cohort_formal_change_percent"], 8.3)
        self.assertEqual(cmp["current"]["passive_absorbed"], 621)

    def test_period_does_not_reconstruct_stock(self):
        a = dashboard(query_from_params({"from": "2025-01-01", "to": "2025-12-31"}))["metrics"]
        b = dashboard(query_from_params({"from": "2026-01-01", "to": "2026-08-22"}))["metrics"]
        self.assertEqual(a["stock"], b["stock"])
        self.assertNotEqual(a["received"], b["received"])

    def test_category_filter(self):
        d = dashboard(query_from_params({"category": "Habite-se"}))
        self.assertGreater(d["meta"]["scope_rows"], 0)
        self.assertTrue(all(x["category"] == "Habite-se" for x in d["records"]["items"]))

    def test_pii_not_in_dataset_schema(self):
        forbidden = {"RequerenteNomeRazao", "RequerenteCPFCNPJ", "ObservacaoAbertura", "UltimoTramiteObservacao", "ResponsavelGargalo", "Inscricao"}
        self.assertFalse(forbidden.intersection(load_rows()[0].keys()))

    def test_recordsets_and_thresholds(self):
        base = dashboard(query_from_params({"limit": "500"}))
        for name, expected in (("received", 2810), ("concluded", 2181), ("stock", 2208), ("stopped", 1089)):
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

    def test_indicator_coverage_is_explicit(self):
        coverage = {x["id"]: x for x in dashboard(query_from_params({}))["indicator_coverage"]}
        for kpi in ("KPI06", "KPI07", "KPI10"):
            self.assertNotEqual(coverage[kpi]["status"], "DISPONÍVEL")
        self.assertEqual(coverage["KPI08"]["status"], "PARCIAL")
        self.assertEqual(coverage["KPI09"]["status"], "PARCIAL")
        self.assertEqual(coverage["KPI11"]["status"], "DISPONÍVEL")

    def test_owner_is_categorical(self):
        allowed = {"Interno", "Requerente", "RT", "Terceiro / Setor", "Indefinido", "Nenhum"}
        d = dashboard(query_from_params({}))
        self.assertTrue(set(d["options"]["owners"]).issubset(allowed))
        self.assertTrue(all("Inscricao" not in r and "ResponsavelGargalo" not in r for r in load_rows()))

    def test_operational_vs_formal_is_preserved(self):
        d = dashboard(query_from_params({}))
        self.assertEqual(d["management"]["data_quality"]["operational_closed_without_formal_date"], 735)
        self.assertGreater(d["metrics"]["concluded"], d["metrics"]["concluded_formal"])


if __name__ == "__main__":
    unittest.main()
