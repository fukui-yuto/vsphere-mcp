from __future__ import annotations

import os
from typing import Any

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "confirmation_required": ("This is a {danger_level}-risk operation. Re-call with confirm=True to execute."),
        "vm_not_found": "VM '{name}' not found",
        "host_not_found": "Host '{name}' not found",
        "task_timeout": "Task timed out after {timeout}s",
        "tool_not_allowed": "Tool '{tool}' is not allowed by RBAC policy",
        "already_powered_on": "VM '{name}' is already powered on",
        "already_powered_off": "VM '{name}' is already powered off",
        "tools_not_running": "VMware Tools not running on '{name}' (status: {status})",
    },
    "ja": {
        "confirmation_required": (
            "これは{danger_level}リスクの操作です。実行するには confirm=True を指定して再呼び出ししてください。"
        ),
        "vm_not_found": "VM '{name}' が見つかりません",
        "host_not_found": "ホスト '{name}' が見つかりません",
        "task_timeout": "タスクが {timeout} 秒でタイムアウトしました",
        "tool_not_allowed": "ツール '{tool}' は RBAC ポリシーにより許可されていません",
        "already_powered_on": "VM '{name}' は既に起動済みです",
        "already_powered_off": "VM '{name}' は既に停止済みです",
        "tools_not_running": "VM '{name}' で VMware Tools が動作していません (状態: {status})",
    },
}

_current_lang: str = os.environ.get("VSPHERE_LANG", "en")


def set_language(lang: str) -> None:
    """Set the current message language."""
    global _current_lang
    if lang in MESSAGES:
        _current_lang = lang


def get_language() -> str:
    """Return the current message language."""
    return _current_lang


def msg(key: str, **kwargs: Any) -> str:
    """Get a localized message by key."""
    catalog = MESSAGES.get(_current_lang, MESSAGES["en"])
    template = catalog.get(key, MESSAGES["en"].get(key, key))
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template
