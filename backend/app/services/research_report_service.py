from __future__ import annotations

import csv
import io
import json
from typing import Any


class ResearchReportService:
    def markdown(self, summary: dict[str, Any]) -> str:
        quality = summary.get("quality") or {}
        scanner = summary.get("scanner") or {}
        portfolio = list(summary.get("portfolio_matrix") or [])
        strategies = list(summary.get("strategy_comparison") or [])
        lines = [
            f"# {summary.get('run_label') or 'Research Pipeline'}",
            "",
            f"- Run ID: `{summary.get('run_id', '-')}`",
            f"- Status: `{summary.get('status', '-')}`",
            f"- Started: `{summary.get('started_at', '-')}`",
            f"- Finished: `{summary.get('finished_at', '-')}`",
            "",
            "## Data Quality",
            "",
            f"- Coverage: {quality.get('coverage_pct', 0)}%",
            "- Cached symbols: "
            f"{quality.get('covered_symbols', 0)} / {quality.get('member_count', 0)}",
            f"- SMA200 ready: {quality.get('sma_200_ready_symbols', 0)}",
            f"- 252D return ready: {quality.get('return_252d_ready_symbols', 0)}",
            "",
            "## Scanner",
            "",
            f"- Run ID: `{scanner.get('run_id', '-')}`",
            f"- Matched: {scanner.get('matched_symbols', 0)}",
            f"- Skipped: {scanner.get('skipped_symbols', 0)}",
            f"- Top symbols: {', '.join(scanner.get('top_symbols') or []) or '-'}",
            "",
            "## Portfolio Matrix",
            "",
            "| Preset | Frequency | Return | Max Drawdown | Sharpe | Turnover |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
        lines.extend(
            [
                "| {preset} | {frequency} | {ret} | {dd} | {sharpe} | {turnover} |".format(
                    preset=item.get("preset") or item.get("run_id") or "-",
                    frequency=item.get("frequency") or "-",
                    ret=_pct(item.get("total_return_pct")),
                    dd=_pct(item.get("max_drawdown_pct")),
                    sharpe=_number(item.get("sharpe_ratio")),
                    turnover=_pct(item.get("turnover_pct")),
                )
                for item in portfolio
            ]
            or ["| - | - | - | - | - | - |"]
        )
        lines.extend(
            [
                "",
                "## Strategy Comparison",
                "",
                "| Template | Average Return | Best Symbol | Worst Symbol | Success | Failed |",
                "| --- | ---: | --- | --- | ---: | ---: |",
            ]
        )
        lines.extend(
            [
                "| {template} | {ret} | {best} | {worst} | {success} | {failed} |".format(
                    template=item.get("template_id") or "-",
                    ret=_pct(item.get("average_total_return_pct")),
                    best=item.get("best_symbol") or "-",
                    worst=item.get("worst_symbol") or "-",
                    success=item.get("successful_symbols", 0),
                    failed=item.get("failed_symbols", 0),
                )
                for item in strategies
            ]
            or ["| - | - | - | - | - | - |"]
        )
        lines.extend(
            [
                "",
                "## Disclaimer",
                "",
                "Educational and research use only; not investment advice.",
                "",
            ]
        )
        return "\n".join(lines)

    def json_artifact(self, summary: dict[str, Any], artifact: str) -> str:
        return json.dumps(self._artifact(summary, artifact), indent=2, sort_keys=True)

    def csv_artifact(self, summary: dict[str, Any], artifact: str) -> str:
        data = self._artifact(summary, artifact)
        rows = data if isinstance(data, list) else [data]
        flattened = [_flatten(row) for row in rows if isinstance(row, dict)]
        if not flattened:
            return ""
        headers = sorted({key for row in flattened for key in row})
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(flattened)
        return output.getvalue()

    def _artifact(self, summary: dict[str, Any], artifact: str) -> dict[str, Any] | list[Any]:
        if artifact == "summary":
            quality = summary.get("quality") or {}
            scanner = summary.get("scanner") or {}
            return {
                "run_id": summary.get("run_id"),
                "run_label": summary.get("run_label"),
                "status": summary.get("status"),
                "started_at": summary.get("started_at"),
                "finished_at": summary.get("finished_at"),
                "coverage_pct": quality.get("coverage_pct"),
                "scanner_matched_symbols": scanner.get("matched_symbols"),
                "scanner_skipped_symbols": scanner.get("skipped_symbols"),
                "best_portfolio_run_id": summary.get("best_portfolio_run_id"),
                "best_multi_backtest_run_id": summary.get("best_multi_backtest_run_id"),
            }
        if artifact == "scanner":
            return list((summary.get("scanner") or {}).get("results") or [])
        if artifact == "quality":
            return list((summary.get("quality") or {}).get("symbols") or [])
        if artifact == "portfolio":
            return list(summary.get("portfolio_matrix") or [])
        if artifact == "strategy":
            return list(summary.get("strategy_comparison") or [])
        raise ValueError(f"Unsupported research artifact: {artifact}")


def _number(value: object) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "-"


def _pct(value: object) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "-"


def _flatten(row: dict[str, Any]) -> dict[str, Any]:
    flattened = {}
    for key, value in row.items():
        if isinstance(value, dict | list | tuple):
            flattened[key] = json.dumps(value, sort_keys=True)
        else:
            flattened[key] = value
    return flattened
