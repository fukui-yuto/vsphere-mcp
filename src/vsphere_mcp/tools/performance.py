from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, find_vm_with_props, handle_tool_errors
from vsphere_mcp.utils.property_collector import collect_properties

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

    @mcp.tool()
    @handle_tool_errors
    def get_datastore_performance(
        datastore_name: str,
        interval_seconds: int = 300,
        max_samples: int = 10,
    ) -> dict[str, Any]:
        """Get I/O performance metrics for a datastore.

        Args:
            datastore_name: Name of the datastore.
            interval_seconds: Performance sampling interval in seconds (default 300).
            max_samples: Maximum number of samples to retrieve (default 10).
        """
        logger.info("get_datastore_performance", datastore_name=datastore_name)

        items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        perf_manager = client.content.perfManager
        counter_map = _build_counter_map(perf_manager)

        target_metrics = {
            "datastore.numberReadAveraged.average": "read_iops",
            "datastore.numberWriteAveraged.average": "write_iops",
            "datastore.totalReadLatency.average": "read_latency_ms",
            "datastore.totalWriteLatency.average": "write_latency_ms",
        }

        metric_id_list, metric_names = _build_metric_ids(counter_map, target_metrics)

        if not metric_id_list:
            return {
                "datastore_name": datastore_name,
                "metrics": {},
                "message": "Target datastore metrics not available",
            }

        query_spec = vim.PerformanceManager.QuerySpec(
            entity=ds_obj,
            metricId=metric_id_list,
            intervalId=interval_seconds,
            maxSample=max_samples,
        )

        try:
            results = perf_manager.QueryPerf(querySpec=[query_spec])
        except Exception as e:
            return {"datastore_name": datastore_name, "metrics": {}, "message": f"Performance query failed: {e}"}

        metrics = _parse_perf_results(results, metric_names)
        return {"datastore_name": datastore_name, "metrics": metrics}

    @mcp.tool()
    @handle_tool_errors
    def get_historical_performance(
        entity_type: str,
        entity_name: str,
        metric_keys: list[str],
        interval_id: int = 300,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        """Get historical performance data for any vSphere entity.

        Args:
            entity_type: Type of entity: 'vm', 'host', 'datastore', or 'cluster'.
            entity_name: Name of the entity.
            metric_keys: List of performance counter keys (e.g. ['cpu.usage.average', 'mem.usage.average']).
            interval_id: Historical interval ID in seconds (default 300; typical: 20, 300, 1800, 7200, 86400).
            start_time: ISO 8601 start time for the query (optional, e.g. '2024-01-01T00:00:00Z').
            end_time: ISO 8601 end time for the query (optional).
        """
        logger.info(
            "get_historical_performance",
            entity_type=entity_type,
            entity_name=entity_name,
        )

        valid_entity_types = {"vm", "host", "datastore", "cluster"}
        if entity_type not in valid_entity_types:
            return {
                "status": "error",
                "error": f"Invalid entity_type '{entity_type}'. Valid values: {', '.join(sorted(valid_entity_types))}",
            }

        entity_obj = None
        if entity_type == "vm":
            found = find_vm_with_props(client, entity_name)
            if found:
                entity_obj = found["_obj"]
        elif entity_type == "host":
            entity_obj = find_host_by_name(client, entity_name)
        elif entity_type == "datastore":
            items = collect_properties(client, vim.Datastore, ["name"])
            for item in items:
                if item.get("name") == entity_name:
                    entity_obj = item["_obj"]
                    break
        elif entity_type == "cluster":
            items = collect_properties(client, vim.ClusterComputeResource, ["name"])
            for item in items:
                if item.get("name") == entity_name:
                    entity_obj = item["_obj"]
                    break

        if entity_obj is None:
            return {"status": "error", "error": f"{entity_type.capitalize()} '{entity_name}' not found"}

        perf_manager = client.content.perfManager
        counter_map = _build_counter_map(perf_manager)

        target_metrics = {key: key for key in metric_keys}
        metric_id_list, metric_names = _build_metric_ids(counter_map, target_metrics)

        if not metric_id_list:
            return {
                "entity_type": entity_type,
                "entity_name": entity_name,
                "metrics": {},
                "message": "None of the requested metric keys were found",
            }

        query_kwargs: dict[str, Any] = {
            "entity": entity_obj,
            "metricId": metric_id_list,
            "intervalId": interval_id,
        }

        if start_time is not None or end_time is not None:
            import datetime

            if start_time is not None:
                query_kwargs["startTime"] = datetime.datetime.fromisoformat(
                    start_time.replace("Z", "+00:00")
                )
            if end_time is not None:
                query_kwargs["endTime"] = datetime.datetime.fromisoformat(
                    end_time.replace("Z", "+00:00")
                )

        query_spec = vim.PerformanceManager.QuerySpec(**query_kwargs)

        try:
            results = perf_manager.QueryPerf(querySpec=[query_spec])
        except Exception as e:
            return {
                "entity_type": entity_type,
                "entity_name": entity_name,
                "metrics": {},
                "message": f"Performance query failed: {e}",
            }

        metrics = _parse_perf_results(results, metric_names)
        return {"entity_type": entity_type, "entity_name": entity_name, "metrics": metrics}

    @mcp.tool()
    @handle_tool_errors
    def get_custom_metrics(
        entity_type: str,
        entity_name: str,
        counter_keys: list[str],
        interval_seconds: int = 20,
        max_samples: int = 10,
    ) -> dict[str, Any]:
        """Get custom performance metrics for a vSphere entity by specific counter keys.

        Args:
            entity_type: Type of entity: 'vm', 'host', 'datastore', or 'cluster'.
            entity_name: Name of the entity.
            counter_keys: List of performance counter keys (e.g. ['cpu.usage.average', 'net.usage.average']).
            interval_seconds: Performance sampling interval in seconds (default 20).
            max_samples: Maximum number of samples to retrieve (default 10).
        """
        logger.info("get_custom_metrics", entity_type=entity_type, entity_name=entity_name)

        valid_entity_types = {"vm", "host", "datastore", "cluster"}
        if entity_type not in valid_entity_types:
            return {
                "status": "error",
                "error": f"Invalid entity_type '{entity_type}'. Valid values: {', '.join(sorted(valid_entity_types))}",
            }

        entity_obj = None
        if entity_type == "vm":
            found = find_vm_with_props(client, entity_name)
            if found:
                entity_obj = found["_obj"]
        elif entity_type == "host":
            entity_obj = find_host_by_name(client, entity_name)
        elif entity_type == "datastore":
            items = collect_properties(client, vim.Datastore, ["name"])
            for item in items:
                if item.get("name") == entity_name:
                    entity_obj = item["_obj"]
                    break
        elif entity_type == "cluster":
            items = collect_properties(client, vim.ClusterComputeResource, ["name"])
            for item in items:
                if item.get("name") == entity_name:
                    entity_obj = item["_obj"]
                    break

        if entity_obj is None:
            return {"status": "error", "error": f"{entity_type.capitalize()} '{entity_name}' not found"}

        perf_manager = client.content.perfManager
        counter_map = _build_counter_map(perf_manager)

        target_metrics = {key: key for key in counter_keys}
        metric_id_list, metric_names = _build_metric_ids(counter_map, target_metrics)

        if not metric_id_list:
            return {
                "entity_type": entity_type,
                "entity_name": entity_name,
                "metrics": {},
                "message": "None of the requested counter keys were found",
            }

        query_spec = vim.PerformanceManager.QuerySpec(
            entity=entity_obj,
            metricId=metric_id_list,
            intervalId=interval_seconds,
            maxSample=max_samples,
        )

        try:
            results = perf_manager.QueryPerf(querySpec=[query_spec])
        except Exception as e:
            return {
                "entity_type": entity_type,
                "entity_name": entity_name,
                "metrics": {},
                "message": f"Performance query failed: {e}",
            }

        metrics = _parse_perf_results(results, metric_names)
        return {"entity_type": entity_type, "entity_name": entity_name, "metrics": metrics}

    @mcp.tool()
    @handle_tool_errors
    def list_performance_intervals() -> dict[str, Any]:
        """List all available historical performance collection intervals configured in vCenter."""
        logger.info("list_performance_intervals")

        perf_manager = client.content.perfManager
        intervals = perf_manager.historicalInterval or []

        interval_list: list[dict[str, Any]] = []
        for interval in intervals:
            interval_list.append(
                {
                    "key": interval.key,
                    "name": interval.name,
                    "samplingPeriod": interval.samplingPeriod,
                    "length": interval.length,
                    "level": interval.level,
                    "enabled": interval.enabled,
                }
            )

        return {
            "total": len(interval_list),
            "intervals": interval_list,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_available_metrics(
        entity_type: str,
        entity_name: str,
    ) -> dict[str, Any]:
        """List all available performance metrics for a vSphere entity.

        Args:
            entity_type: Type of entity: 'vm', 'host', 'datastore', or 'cluster'.
            entity_name: Name of the entity.
        """
        logger.info("list_available_metrics", entity_type=entity_type, entity_name=entity_name)

        valid_entity_types = {"vm", "host", "datastore", "cluster"}
        if entity_type not in valid_entity_types:
            return {
                "status": "error",
                "error": f"Invalid entity_type '{entity_type}'. Valid values: {', '.join(sorted(valid_entity_types))}",
            }

        entity_obj = None
        if entity_type == "vm":
            found = find_vm_with_props(client, entity_name)
            if found:
                entity_obj = found["_obj"]
        elif entity_type == "host":
            entity_obj = find_host_by_name(client, entity_name)
        elif entity_type == "datastore":
            items = collect_properties(client, vim.Datastore, ["name"])
            for item in items:
                if item.get("name") == entity_name:
                    entity_obj = item["_obj"]
                    break
        elif entity_type == "cluster":
            items = collect_properties(client, vim.ClusterComputeResource, ["name"])
            for item in items:
                if item.get("name") == entity_name:
                    entity_obj = item["_obj"]
                    break

        if entity_obj is None:
            return {"status": "error", "error": f"{entity_type.capitalize()} '{entity_name}' not found"}

        perf_manager = client.content.perfManager
        available_metric_ids = perf_manager.QueryAvailablePerfMetric(entity=entity_obj)

        counter_map_by_id: dict[int, str] = {}
        for counter in perf_manager.perfCounter:
            key = f"{counter.groupInfo.key}.{counter.nameInfo.key}.{counter.rollupType}"
            counter_map_by_id[counter.key] = key

        metrics: list[dict[str, Any]] = []
        seen: set[int] = set()
        for metric_id in available_metric_ids or []:
            counter_id = metric_id.counterId
            if counter_id not in seen:
                seen.add(counter_id)
                metrics.append(
                    {
                        "counterId": counter_id,
                        "key": counter_map_by_id.get(counter_id, f"counter_{counter_id}"),
                    }
                )

        metrics.sort(key=lambda m: m["key"])

        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "total": len(metrics),
            "metrics": metrics,
        }
