"""Alkhaliya workflow engine as a local HTTP service.

``POST /api/run`` accepts ``{"text": "...", "workflow": "optional path"}`` and
executes the workflow **dry-run only** over the event, returning the trace,
queue routing and webhook payloads without any external side effect. The
default workflow loads once at startup (``ALKHALIYA_WORKFLOW``, default
``<project>/workflows/customer_hive.json``; falls back to the built-in
customer hive template when the file is absent).
"""

from __future__ import annotations

import os
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .engine import load_workflow, run_workflow
from .http_base import BaseServiceHandler, build_server
from .templates import customer_hive

_WORKFLOW: dict[str, Any] | None = None


def workflow_path() -> Path:
    raw = os.environ.get("ALKHALIYA_WORKFLOW", "").strip()
    return Path(raw) if raw else PROJECT_ROOT / "workflows" / "customer_hive.json"


def _run_route(data: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    text = str(data.get("text") or "").strip()
    if not text:
        return 400, {"ok": False, "error": "missing 'text'"}
    workflow = _WORKFLOW
    raw_path = str(data.get("workflow") or "").strip()
    if raw_path:
        candidate = Path(raw_path)
        if not candidate.exists():
            return 404, {"ok": False, "error": f"workflow not found: {candidate}"}
        workflow = load_workflow(candidate)
    if workflow is None:
        return 503, {"ok": False, "error": "no workflow loaded"}
    result = run_workflow(workflow, {"text": text}, dry_run=True)
    return 200, {"ok": bool(result.get("ok", True)), **result}


class Handler(BaseServiceHandler):
    post_routes = {"/api/run": staticmethod(_run_route)}


def create_server(host: str | None = None, port: int | None = None) -> ThreadingHTTPServer:
    global _WORKFLOW
    path = workflow_path()
    _WORKFLOW = load_workflow(path) if path.exists() else customer_hive()
    return build_server(Handler, host=host, port=port)


def run_server(host: str | None = None, port: int | None = None) -> None:
    from .version import __version__

    server = create_server(host=host, port=port)
    print(f"alkhaliya service v{__version__}: http://{server.server_address[0]}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
