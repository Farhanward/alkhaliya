from __future__ import annotations

import json
from pathlib import Path


def convert_bitext(input_path: str | Path, out_path: str | Path, *, limit: int = 0) -> dict:
    source = Path(input_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    with source.open("r", encoding="utf-8") as handle, out.open("w", encoding="utf-8") as output:
        for line in handle:
            if limit and rows >= limit:
                break
            if not line.strip():
                continue
            record = json.loads(line)
            text = str(record.get("instruction") or record.get("text") or "")
            event = {
                "id": rows + 1,
                "text": text,
                "source": "bitext_customer_support",
                "intent": record.get("intent"),
                "category": record.get("category"),
            }
            output.write(json.dumps(event, ensure_ascii=False) + "\n")
            rows += 1
    return {"source": str(source.resolve()), "out": str(out.resolve()), "rows": rows}

