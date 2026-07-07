from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from alkhaliya.batch import evaluate
from alkhaliya.datasets import convert_bitext
from alkhaliya.engine import run_workflow
from alkhaliya.templates import customer_hive


class AlKhaliyaTests(unittest.TestCase):
    def test_customer_hive_routes_order(self):
        result = run_workflow(customer_hive(), {"text": "where is my order ORD-1234"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["state"]["queue"], "sales_ops")
        self.assertIn("reply", result["state"])

    def test_convert_and_batch_fixture(self):
        with tempfile.TemporaryDirectory(dir="C:/Projects") as tmp:
            source = Path(tmp) / "bitext.jsonl"
            events = Path(tmp) / "events.jsonl"
            rows = [
                {"instruction": "refund my order", "intent": "refund", "category": "ORDER"},
                {"instruction": "how to contact support", "intent": "contact", "category": "CONTACT"},
            ]
            source.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            info = convert_bitext(source, events)
            self.assertEqual(info["rows"], 2)
            summary = evaluate(customer_hive(), events)
            self.assertEqual(summary["errors"], 0)
            self.assertEqual(summary["success_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()

