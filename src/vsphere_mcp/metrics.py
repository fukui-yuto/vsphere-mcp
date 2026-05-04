"""Optional Prometheus metrics for vsphere-mcp server monitoring."""

from __future__ import annotations

try:
    from prometheus_client import Counter, Histogram, start_http_server

    tool_calls_total = Counter(
        "vsphere_mcp_tool_calls_total",
        "Total number of tool calls",
        ["tool", "status"],
    )
    tool_duration_seconds = Histogram(
        "vsphere_mcp_tool_duration_seconds",
        "Duration of tool calls in seconds",
        ["tool"],
    )
    connection_errors_total = Counter(
        "vsphere_mcp_connection_errors_total",
        "Total number of connection errors",
        ["error_type"],
    )
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    tool_calls_total = None
    tool_duration_seconds = None
    connection_errors_total = None


def start_metrics_server(port: int = 9090) -> None:
    if METRICS_AVAILABLE:
        start_http_server(port)


def record_tool_call(tool: str, status: str, duration_s: float) -> None:
    if METRICS_AVAILABLE:
        tool_calls_total.labels(tool=tool, status=status).inc()
        tool_duration_seconds.labels(tool=tool).observe(duration_s)


def record_connection_error(error_type: str) -> None:
    if METRICS_AVAILABLE:
        connection_errors_total.labels(error_type=error_type).inc()
