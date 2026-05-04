from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_datastore_obj(client: Any, datastore_name: str) -> Any | None:
    """Find a datastore by name and return its managed object."""
    items = collect_properties(client, vim.Datastore, ["name"])
    for item in items:
        if item.get("name") == datastore_name:
            return item["_obj"]
    return None


def _find_datacenter(client: Any) -> Any | None:
    """Find the first datacenter (needed for fileManager operations)."""
    items = collect_properties(client, vim.Datacenter, ["name"])
    if items:
        return items[0]["_obj"]
    return None


def register_datastore_browser_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def browse_datastore(
        datastore_name: str,
        path: str = "/",
        file_pattern: str = "*",
    ) -> dict[str, Any]:
        """Browse files on a datastore. Returns file names, sizes, and modification times."""
        logger.info(
            "browse_datastore",
            datastore_name=datastore_name,
            path=path,
            file_pattern=file_pattern,
        )
        ds_obj = _find_datastore_obj(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        browser = ds_obj.browser
        search_spec = vim.host.DatastoreBrowser.SearchSpec(
            matchPattern=[file_pattern],
            details=vim.host.DatastoreBrowser.FileInfo.Details(
                fileType=True,
                fileSize=True,
                modification=True,
            ),
            query=[
                vim.host.DatastoreBrowser.VmDiskQuery(),
                vim.host.DatastoreBrowser.IsoImageQuery(),
                vim.host.DatastoreBrowser.FloppyImageQuery(),
                vim.host.DatastoreBrowser.FolderQuery(),
                vim.host.DatastoreBrowser.FileQuery(),
            ],
        )

        ds_path = path.strip("/")
        datastore_path = f"[{datastore_name}] {ds_path}" if ds_path else f"[{datastore_name}]"

        task = browser.SearchDatastoreSubFolders_Task(
            datastorePath=datastore_path,
            searchSpec=search_spec,
        )
        task_result = wait_for_task(task)
        if task_result.get("status") != "success":
            return task_result

        results = []
        if hasattr(task.info, "result") and task.info.result:
            for folder_result in task.info.result:
                folder_path = folder_result.folderPath
                for file_info in folder_result.file or []:
                    entry: dict[str, Any] = {
                        "folder": folder_path,
                        "name": file_info.path,
                        "size_bytes": file_info.fileSize if hasattr(file_info, "fileSize") else None,
                    }
                    if hasattr(file_info, "modification") and file_info.modification:
                        entry["modification"] = str(file_info.modification)
                    results.append(entry)

        return {
            "datastore": datastore_name,
            "path": path,
            "pattern": file_pattern,
            "total_files": len(results),
            "files": results,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def delete_datastore_file(datastore_name: str, file_path: str) -> dict[str, Any]:
        """Delete a file or directory from a datastore. This operation is irreversible."""
        logger.info("delete_datastore_file", datastore_name=datastore_name, file_path=file_path)
        dc = _find_datacenter(client)
        if dc is None:
            return {"status": "error", "error": "No datacenter found"}

        ds_obj = _find_datastore_obj(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        content = client.content
        file_manager = content.fileManager
        datastore_file_path = f"[{datastore_name}] {file_path}"

        task = file_manager.DeleteDatastoreFile_Task(name=datastore_file_path, datacenter=dc)
        result = wait_for_task(task)
        result["datastore"] = datastore_name
        result["file_path"] = file_path
        result["operation"] = "delete_datastore_file"
        return result
