"""Exercise server callbacks without requiring a running Home Assistant instance."""

import ast
from dataclasses import dataclass, replace
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
import unittest
from unittest.mock import AsyncMock


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "ws_mcp_server"


@dataclass
class FakeContext:
    device_id: str | None = None


class FakeServer:
    def __class_getitem__(cls, item):
        return cls

    def __init__(self, name):
        self.request_context = SimpleNamespace(meta=None)
        self.handlers = {}

    def __getattr__(self, name):
        def register():
            def decorate(handler):
                self.handlers[name] = handler
                return handler
            return decorate
        return register


class ServerCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Compile the actual factory and helper; stub only external dependencies.
        tree = ast.parse((COMPONENT / "server.py").read_text(encoding="utf-8"))
        nodes = [node for node in tree.body if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.name in {"create_server", "_has_live_context_tool"}]
        self.api = SimpleNamespace(
            tools=[SimpleNamespace(name="homeassistant__GetLiveContext")],
            async_call_tool=AsyncMock(),
        )
        namespace = {
            "Any": Any,
            "Server": FakeServer,
            "STATELESS_LLM_API": "stateless",
            "META_DEVICE_ID": "io.home-assistant/device_id",
            "LIVE_CONTEXT_TOOL_NAME": "homeassistant__GetLiveContext",
            "SNAPSHOT_RESOURCE_URI": "homeassistant://assist/context-snapshot",
            "SNAPSHOT_RESOURCE_MIME_TYPE": "text/plain",
            "llm": SimpleNamespace(
                async_get_api=AsyncMock(return_value=self.api),
                ToolInput=lambda **kwargs: SimpleNamespace(**kwargs),
            ),
            "types": SimpleNamespace(
                TextContent=lambda **kwargs: SimpleNamespace(**kwargs),
                CallToolResult=lambda **kwargs: SimpleNamespace(**kwargs),
            ),
            "ReadResourceContents": lambda **kwargs: SimpleNamespace(**kwargs),
            "HomeAssistantError": RuntimeError,
            "probatio": SimpleNamespace(Invalid=ValueError),
            "_LOGGER": SimpleNamespace(debug=lambda *args: None),
            "json": json,
            "cast": cast,
            "replace": replace,
        }
        module = ast.Module(body=[ast.ImportFrom(
            module="__future__", names=[ast.alias(name="annotations")], level=0
        ), *nodes], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), "server.py", "exec"), namespace)
        self.factory = namespace["create_server"]
        self.server = await self.factory(None, "assist", FakeContext(), read_only=False)

    async def test_transport_supplies_required_factory_arguments(self):
        tree = ast.parse((COMPONENT / "websocket_transport.py").read_text(encoding="utf-8"))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == "create_server"]
        self.assertEqual(len(calls), 1)
        call = calls[0]
        bound = inspect.signature(self.factory).bind(
            *[None for arg in call.args],
            **{kw.arg: ast.literal_eval(kw.value) for kw in call.keywords},
        )
        self.assertIs(bound.arguments["read_only"], False)

    async def test_tool_result_preserves_data_and_error_flag(self):
        for error in (False, True):
            with self.subTest(error=error):
                data = {"message": "测试", "nested": [1, {"success": not error}]}
                self.api.async_call_tool.return_value = SimpleNamespace(data=data, error=error)
                result = await self.server.handlers["call_tool"]("test", {})
                self.assertEqual(json.loads(result.content[0].text), data)
                self.assertIs(result.isError, error)

    async def test_context_resource_reads_tool_result_data(self):
        self.api.async_call_tool.return_value = SimpleNamespace(
            data={"result": "Sony XB10 is idle"}, error=False
        )
        result = await self.server.handlers["read_resource"](
            "homeassistant://assist/context-snapshot"
        )
        self.assertEqual(result[0].content, "Sony XB10 is idle")

    async def test_context_resource_propagates_tool_error(self):
        self.api.async_call_tool.return_value = SimpleNamespace(
            data={"error": "Context unavailable"}, error=True
        )
        with self.assertRaisesRegex(RuntimeError, "Context unavailable"):
            await self.server.handlers["read_resource"](
                "homeassistant://assist/context-snapshot"
            )


if __name__ == "__main__":
    unittest.main()
