from __future__ import annotations

import argparse
import json
from pathlib import Path

from .batch import evaluate
from .datasets import convert_bitext
from .engine import load_workflow, run_workflow, save_workflow
from .reports import markdown
from .templates import customer_hive


def _write_json(path: str | Path, data: dict) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="alkhaliya", description="خلية النحل: أتمتة محلية dry-run.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    init = sub.add_parser("init")
    init.add_argument("--out", default="workflows/customer_hive.json")
    run = sub.add_parser("run")
    run.add_argument("--workflow", default="workflows/customer_hive.json")
    run.add_argument("--text", required=True)
    convert = sub.add_parser("convert-bitext")
    convert.add_argument("--input", default="C:/Projects/almandoub/data/external/bitext_customer_support_12000.jsonl")
    convert.add_argument("--out", default="data/benchmarks/alkhaliya_bitext_events.jsonl")
    convert.add_argument("--limit", type=int, default=12000)
    batch = sub.add_parser("batch")
    batch.add_argument("--workflow", default="workflows/customer_hive.json")
    batch.add_argument("--events", default="data/benchmarks/alkhaliya_bitext_events.jsonl")
    batch.add_argument("--json-out", default="reports/alkhaliya_benchmark.json")
    batch.add_argument("--report", default="reports/alkhaliya_benchmark.md")
    stress = sub.add_parser("stress")
    stress.add_argument("--workflow", default="workflows/customer_hive.json")
    stress.add_argument("--events", default="data/benchmarks/alkhaliya_bitext_events.jsonl")
    stress.add_argument("--repeat", type=int, default=3)
    stress.add_argument("--json-out", default="reports/alkhaliya_stress.json")
    stress.add_argument("--report", default="reports/alkhaliya_stress.md")
    serve = sub.add_parser("serve")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    sub.add_parser("version")
    args = parser.parse_args(argv)
    if args.cmd == "serve":
        from .service import run_server

        run_server(host=args.host, port=args.port)
        return 0
    if args.cmd == "version":
        from .version import __version__

        print(json.dumps({"service": "alkhaliya", "version": __version__}, ensure_ascii=False))
        return 0
    if args.cmd == "init":
        workflow = customer_hive()
        save_workflow(args.out, workflow)
        print(json.dumps({"out": str(Path(args.out).resolve()), "nodes": len(workflow["nodes"])}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "run":
        print(json.dumps(run_workflow(load_workflow(args.workflow), {"text": args.text}, dry_run=True), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "convert-bitext":
        print(json.dumps(convert_bitext(args.input, args.out, limit=args.limit), ensure_ascii=False, indent=2))
        return 0
    if args.cmd in {"batch", "stress"}:
        summary = evaluate(load_workflow(args.workflow), args.events, repeat=getattr(args, "repeat", 1))
        _write_json(args.json_out, summary)
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(markdown(summary, "تقرير ضغط خلية النحل" if args.cmd == "stress" else "تقرير خلية النحل"), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["collapse_check"]["passed"] else 2
    raise ValueError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())

