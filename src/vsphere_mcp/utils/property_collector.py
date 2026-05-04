from __future__ import annotations

from typing import Any

from pyVmomi import vim, vmodl

from vsphere_mcp.client import VSphereClient


def collect_properties(
    client: VSphereClient,
    obj_type: type,
    path_set: list[str],
    root: vim.ManagedEntity | None = None,
) -> list[dict[str, Any]]:
    """Use PropertyCollector to efficiently retrieve object properties."""
    content = client.content
    root_folder = root if root is not None else content.rootFolder

    container = content.viewManager.CreateContainerView(root_folder, [obj_type], recursive=True)

    traversal_spec = vmodl.query.PropertyCollector.TraversalSpec(
        name="traverseEntities",
        type=vim.view.ContainerView,
        path="view",
        skip=False,
    )

    obj_spec = vmodl.query.PropertyCollector.ObjectSpec(
        obj=container,
        skip=True,
        selectSet=[traversal_spec],
    )

    prop_spec = vmodl.query.PropertyCollector.PropertySpec(
        type=obj_type,
        pathSet=path_set,
    )

    filter_spec = vmodl.query.PropertyCollector.FilterSpec(
        objectSet=[obj_spec],
        propSet=[prop_spec],
    )

    try:
        props = content.propertyCollector.RetrieveContents([filter_spec])
    finally:
        container.Destroy()

    results = []
    for obj in props:
        item: dict[str, Any] = {"_obj": obj.obj}
        for prop in obj.propSet:
            item[prop.name] = prop.val
        results.append(item)
    return results
