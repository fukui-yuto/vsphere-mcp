from vsphere_mcp.tools._base import VSphereToolError, handle_tool_errors, require_confirm


class TestHandleToolErrors:
    def test_success_returns_result(self) -> None:
        @handle_tool_errors
        def ok_tool() -> dict:
            return {"status": "success"}

        result = ok_tool()
        assert result["status"] == "success"

    def test_vsphere_tool_error(self) -> None:
        @handle_tool_errors
        def fail_tool() -> dict:
            raise VSphereToolError("something went wrong")

        result = fail_tool()
        assert result["status"] == "error"
        assert "something went wrong" in result["error"]

    def test_unexpected_error(self) -> None:
        @handle_tool_errors
        def crash_tool() -> dict:
            raise RuntimeError("unexpected")

        result = crash_tool()
        assert result["status"] == "error"
        assert "RuntimeError" in result["error"]


class TestRequireConfirmWithHandleErrors:
    """Test that the two decorators work together correctly."""

    def test_combined_decorators_no_confirm(self) -> None:
        @handle_tool_errors
        @require_confirm(danger_level="high")
        def risky_op(name: str) -> dict:
            return {"done": True}

        result = risky_op(name="test")
        assert result["status"] == "confirmation_required"

    def test_combined_decorators_with_confirm(self) -> None:
        @handle_tool_errors
        @require_confirm(danger_level="high")
        def risky_op(name: str) -> dict:
            return {"done": True}

        result = risky_op(name="test", confirm=True)
        assert result["done"] is True

    def test_combined_decorators_error_caught(self) -> None:
        @handle_tool_errors
        @require_confirm(danger_level="low")
        def error_op() -> dict:
            raise VSphereToolError("fail")

        result = error_op(confirm=True)
        assert result["status"] == "error"
        assert "fail" in result["error"]
