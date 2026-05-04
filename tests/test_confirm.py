from vsphere_mcp.tools._base import require_confirm


class TestRequireConfirm:
    def test_without_confirm_returns_confirmation_required(self) -> None:
        @require_confirm(danger_level="medium")
        def dummy_op(name: str) -> dict:
            return {"status": "success"}

        result = dummy_op(name="test")
        assert result["status"] == "confirmation_required"
        assert result["danger_level"] == "medium"
        assert result["tool"] == "dummy_op"

    def test_with_confirm_executes(self) -> None:
        @require_confirm(danger_level="high")
        def dummy_op(name: str) -> dict:
            return {"status": "success", "name": name}

        result = dummy_op(name="test", confirm=True)
        assert result["status"] == "success"
        assert result["name"] == "test"

    def test_critical_danger_level(self) -> None:
        @require_confirm(danger_level="critical")
        def delete_something(target: str) -> dict:
            return {"deleted": target}

        result = delete_something(target="item1")
        assert result["status"] == "confirmation_required"
        assert result["danger_level"] == "critical"

        result = delete_something(target="item1", confirm=True)
        assert result["deleted"] == "item1"
