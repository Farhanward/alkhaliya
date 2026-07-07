from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_'-]{1,}|[\u0600-\u06ff]{2,}", re.I)


def _render(template: str, state: dict[str, Any]) -> str:
    def repl(match: re.Match[str]) -> str:
        path = match.group(1).split(".")
        value: Any = state
        for part in path:
            if isinstance(value, dict):
                value = value.get(part, "")
            else:
                value = ""
        return str(value)

    return re.sub(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}", repl, template)


def _classify(text: str) -> str:
    low = text.casefold()
    if any(word in low for word in ("refund", "cancel", "complaint", "angry", "مشكلة", "استرجاع")):
        return "support_escalation"
    if any(word in low for word in ("order", "buy", "price", "quote", "طلب", "سعر")):
        return "sales_or_order"
    if any(word in low for word in ("invoice", "payment", "billing", "فاتورة", "دفع")):
        return "billing"
    return "general"


def run_workflow(workflow: dict[str, Any], event: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
    started = time.perf_counter()
    state: dict[str, Any] = {"event": event, "dry_run": dry_run}
    trace = []
    for node in workflow.get("nodes", []):
        node_id = str(node.get("id") or len(trace))
        kind = str(node.get("type") or "")
        try:
            if kind == "set":
                for key, value in dict(node.get("values") or {}).items():
                    state[key] = _render(str(value), state)
            elif kind == "classify":
                source = _render(str(node.get("text") or "{{event.text}}"), state)
                state[str(node.get("out") or "category")] = _classify(source)
            elif kind == "route":
                key = _render(str(node.get("key") or "{{category}}"), state)
                routes = dict(node.get("routes") or {})
                state[str(node.get("out") or "route")] = routes.get(key, routes.get("*", "default"))
            elif kind == "template":
                state[str(node.get("out") or "message")] = _render(str(node.get("template") or ""), state)
            elif kind == "webhook":
                payload = {k: _render(str(v), state) for k, v in dict(node.get("payload") or {}).items()}
                state.setdefault("webhooks", []).append({"url": node.get("url"), "payload": payload, "dry_run": dry_run})
            elif kind == "assert":
                key = str(node.get("key") or "")
                if not state.get(key):
                    raise ValueError(f"missing state key: {key}")
            else:
                raise ValueError(f"unsupported node type: {kind}")
            trace.append({"node": node_id, "type": kind, "status": "ok"})
        except Exception as exc:
            trace.append({"node": node_id, "type": kind, "status": "error", "error": repr(exc)})
            return {"ok": False, "state": state, "trace": trace, "elapsed_ms": (time.perf_counter() - started) * 1000}
    return {"ok": True, "state": state, "trace": trace, "elapsed_ms": (time.perf_counter() - started) * 1000}


def load_workflow(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_workflow(path: str | Path, workflow: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(workflow, ensure_ascii=False, indent=2), encoding="utf-8")

