from __future__ import annotations


def markdown(summary: dict, title: str = "تقرير خلية النحل") -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- الأحداث: `{summary.get('processed', 0)}`",
            f"- النجاح: `{summary.get('success_rate', 0):.2%}`",
            f"- الأخطاء: `{summary.get('errors', 0)}`",
            f"- الطوابير: `{summary.get('queues', {})}`",
            f"- p99: `{summary.get('latency_ms', {}).get('p99', 0):.4f}ms`",
            f"- peak memory: `{summary.get('memory_mb', {}).get('peak', 0):.2f}MB`",
            "",
        ]
    )

