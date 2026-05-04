from vsphere_mcp.logging import _mask_sensitive_data


class TestMaskSensitiveData:
    def test_masks_password(self) -> None:
        event = {"event": "connect", "password": "secret123"}
        result = _mask_sensitive_data(None, None, event)
        assert result["password"] == "***MASKED***"
        assert result["event"] == "connect"

    def test_masks_partial_key(self) -> None:
        event = {"vsphere_password": "secret", "name": "test"}
        result = _mask_sensitive_data(None, None, event)
        assert result["vsphere_password"] == "***MASKED***"
        assert result["name"] == "test"

    def test_masks_token(self) -> None:
        event = {"auth_token": "abc123"}
        result = _mask_sensitive_data(None, None, event)
        assert result["auth_token"] == "***MASKED***"

    def test_no_sensitive_keys(self) -> None:
        event = {"host": "localhost", "port": 443}
        result = _mask_sensitive_data(None, None, event)
        assert result["host"] == "localhost"
        assert result["port"] == 443
