from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, find_vm_with_props, handle_tool_errors

logger = get_logger(__name__)


def _build_counter_map(perf_manager: Any) -> dict[str, int]:
    """Build a mapping from counter key string to counter ID."""
    counter_map: dict[str, int] = {}
    for counter in perf_manager.perfCounter:
        key = f"{counter.groupInfo.key}.{counter.nameInfo.key}.{counter.rollupType}"
        counter_map[key] = counter.key
    return counter_map


def _build_metric_ids(
    counter_map: dict[str, int],
    target_metrics: dict[str, str],
) -> tuple[list[Any], dict[int, str]]:
    """Build metric ID list and name mapping from target metrics."""
    metric_id_list: list[Any] = []
    metric_names: dict[int, str] = {}
    for perf_key, friendly_name in target_metrics.items():
        counter_id = counter_map.get(perf_key)
        if counter_id is not None:
            metric_id_list.append(vim.PerformanceManager.MetricId(counterId=counter_id, instance=""))
            metric_names[counter_id] = friendly_name
    return metric_id_list, metric_names


def _parse_perf_results(results: Any, metric_names: dict[int, str]) -> dict[str, Any]:
    """Parse performance query results into a friendly dict."""
    metrics: dict[str, Any] = {}
    if results:
        for result in results:
            for val in result.value:
                name = metric_names.get(val.id.counterId, f"counter_{val.id.counterId}")
                values = list(val.value) if val.value else []
                metrics[name] = {
                    "latest": values[-1] if values else None,
                    "average": round(sum(values) / len(values), 2) if values else None,
                    "samples": len(values),
                }
    return metrics


def register_performance_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_vm_performance(
        vm_name: str,
        interval_seconds: int = 20,
        max_samples: int = 10,
    ) -> dict[str, Any]:
        """Get CPU and memory performance metrics for a VM. Uses real-time stats when available."""
        logger.info("get_vm_performance", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        content = client.content
        perf_manager = content.perfManager

        metric_ids = perf_manager.QueryAvailablePerfMetric(entity=vm_obj)
        if not metric_ids:
            return {"vm_name": vm_name, "metrics": {}, "message": "No performance data available"}

        counter_map = _build_counter_map(perf_manager)

        target_metrics = {
            "cpu.usage.average": "cpu_usage_percent",
            "mem.usage.average": "memory_usage_percent",
            "cpu.usagemhz.average": "cpu_usage_mhz",
            "mem.consumed.average": "memory_consumed_kb",
            "disk.usage.average": "disk_usage_kbps",
            "net.usage.average": "net_usage_kbps",
        }

        metric_id_list, metric_names = _build_metric_ids(counter_map, target_metrics)

        if not metric_id_list:
            return {"vm_name": vm_name, "metrics": {}, "message": "Target metrics not available"}

        query_spec = vim.PerformanceManager.QuerySpec(
            entity=vm_obj,
            metricId=metric_id_list,
            intervalId=interval_seconds,
            maxSample=max_samples,
        )

        try:
            results = perf_manager.QueryPerf(querySpec=[query_spec])
        except Exception as e:
            return {"vm_name": vm_name, "metrics": {}, "message": f"Performance query failed: {e}"}

        metrics = _parse_perf_results(results, metric_names)
        return {"vm_name": vm_name, "metrics": metrics}

    @mcp.tool()
    @handle_tool_errors
    def get_host_performance(
        host_name: str,
        interval_seconds: int = 20,
        max_samples: int = 10,
    ) -> dict[str, Any]:
        """Get CPU and memory performance metrics for an ESXi host."""
        logger.info("get_host_performance", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        content = client.content
        perf_manager = content.perfManager

        counter_map = _build_counter_map(perf_manager)

        target_metrics = {
            "cpu.usage.average": "cpu_usage_percent",
            "mem.usage.average": "memory_usage_percent",
            "cpu.usagemhz.average": "cpu_usage_mhz",
            "mem.consumed.average": "memory_consumed_kb",
        }

        metric_id_list, metric_names = _build_metric_ids(counter_map, target_metrics)

        if not metric_id_list:
            return {"host_name": host_name, "metrics": {}, "message": "Target metrics not available"}

        query_spec = vim.PerformanceManager.QuerySpec(
            entity=host_obj,
            metricId=metric_id_list,
            intervalId=interval_seconds,
            maxSample=max_samples,
        )

        try:
            results = perf_manager.QueryPerf(querySpec=[query_spec])
        except Exception as e:
            return {"host_name": host_name, "metrics": {}, "message": f"Performance query failed: {e}"}

        metrics = _parse_perf_results(results, metric_names)
        return {"host_name": host_name, "metrics": metrics}
