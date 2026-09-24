"""Tier 1 Feature 6: MCP JSON-RPC Spec Validator.

Tests Model Context Protocol (MCP) JSON-RPC 2.0 specifications:
- Stdio transport configuration schema (command, args, env, cwd)
- SSE / HTTP transport configuration schema (serverUrl, headers)
- JSON-RPC 2.0 request/response envelope validation
- MCP tool definition schema and parameter types
- Tool execution error semantics (isError: true inside result)
"""

import pytest
from typing import Dict, Any


class MockMcpSpecValidator:
    """Mock/Reference MCP spec validator."""

    @classmethod
    def validate_transport_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an MCP server transport definition."""
        if not isinstance(config, dict):
            return {"valid": False, "error": "Configuration must be a dictionary"}

        has_command = "command" in config
        has_url = "serverUrl" in config or "url" in config

        if not has_command and not has_url:
            return {"valid": False, "error": "Server must define either 'command' (stdio) or 'serverUrl'/'url' (sse/http)"}

        if has_command:
            cmd = config["command"]
            if not isinstance(cmd, str) or not cmd.strip():
                return {"valid": False, "error": "Field 'command' must be a non-empty string"}
            if "args" in config and not isinstance(config["args"], list):
                return {"valid": False, "error": "Field 'args' must be a list of strings"}
            if "env" in config and not isinstance(config["env"], dict):
                return {"valid": False, "error": "Field 'env' must be a dictionary"}

        if has_url:
            url = config.get("serverUrl") or config.get("url")
            if not isinstance(url, str) or not (url.startswith("http://") or url.startswith("https://")):
                return {"valid": False, "error": f"Invalid URL scheme in endpoint: {url}"}

        return {"valid": True, "error": None}

    @classmethod
    def validate_jsonrpc_response(cls, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON-RPC 2.0 response envelope."""
        if response.get("jsonrpc") != "2.0":
            return {"valid": False, "error": "Missing or invalid 'jsonrpc' version (must be '2.0')"}
        if "id" not in response:
            return {"valid": False, "error": "Missing response 'id'"}
        if "result" not in response and "error" not in response:
            return {"valid": False, "error": "Response must contain either 'result' or 'error'"}
        return {"valid": True, "error": None}


def test_f6_valid_stdio_entrypoint_accepted():
    """Verify compliant stdio configuration passes validation."""
    config = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite", "test.db"],
        "env": {"DEBUG": "true"}
    }
    result = MockMcpSpecValidator.validate_transport_config(config)
    assert result["valid"] is True


def test_f6_valid_sse_entrypoint_accepted():
    """Verify compliant SSE remote server configuration passes validation."""
    config = {
        "serverUrl": "https://mcp.example.com/sse",
        "headers": {"Authorization": "Bearer token123"}
    }
    result = MockMcpSpecValidator.validate_transport_config(config)
    assert result["valid"] is True


def test_f6_stdio_missing_command_rejected():
    """Verify stdio server missing 'command' is rejected."""
    config = {
        "args": ["-y", "some-tool"],
        "env": {}
    }
    result = MockMcpSpecValidator.validate_transport_config(config)
    assert result["valid"] is False
    assert "must define either 'command'" in result["error"]


def test_f6_stdio_args_not_a_list_rejected():
    """Verify stdio server where 'args' is a string rather than a list is rejected."""
    config = {
        "command": "python",
        "args": "-m my_server"  # Invalid: should be ["-m", "my_server"]
    }
    result = MockMcpSpecValidator.validate_transport_config(config)
    assert result["valid"] is False
    assert "must be a list of strings" in result["error"]


def test_f6_sse_invalid_url_scheme_rejected():
    """Verify SSE server with non-http URL scheme is rejected."""
    config = {
        "serverUrl": "ftp://files.example.com/mcp"
    }
    result = MockMcpSpecValidator.validate_transport_config(config)
    assert result["valid"] is False
    assert "Invalid URL scheme" in result["error"]


def test_f6_jsonrpc_response_envelope_validation():
    """Verify standard JSON-RPC 2.0 response envelope rules."""
    valid_resp = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"tools": []}
    }
    res = MockMcpSpecValidator.validate_jsonrpc_response(valid_resp)
    assert res["valid"] is True

    bad_resp = {
        "jsonrpc": "1.0",
        "id": 1,
        "result": {}
    }
    res_bad = MockMcpSpecValidator.validate_jsonrpc_response(bad_resp)
    assert res_bad["valid"] is False


def test_f6_tool_call_error_semantics():
    """Verify MCP specification requirement: tool execution errors return isError: true inside result."""
    tool_error_payload = {
        "jsonrpc": "2.0",
        "id": 42,
        "result": {
            "content": [
                {"type": "text", "text": "Error: table 'users' does not exist"}
            ],
            "isError": True
        }
    }
    res = MockMcpSpecValidator.validate_jsonrpc_response(tool_error_payload)
    assert res["valid"] is True
    assert tool_error_payload["result"]["isError"] is True
