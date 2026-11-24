"""Check the LLM context passed to Home Assistant without a running instance."""

import ast
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "ws_mcp_server"


@dataclass
class FakeContext:
    user_id: str | None = None


class LLMContextTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        tree = ast.parse((COMPONENT / "websocket_transport.py").read_text(encoding="utf-8"))
        nodes = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                 and node.name == "_async_create_llm_context"]
        self.assertEqual(len(nodes), 1)
        namespace = {
            "Context": FakeContext,
            "HomeAssistant": object,
            "DOMAIN": "ws_mcp_server",
            "conversation": SimpleNamespace(DOMAIN="conversation"),
            "llm": SimpleNamespace(LLMContext=lambda **kwargs: SimpleNamespace(**kwargs)),
        }
        module = ast.Module(body=[ast.ImportFrom(
            module="__future__", names=[ast.alias(name="annotations")], level=0
        ), *nodes], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), "websocket_transport.py", "exec"), namespace)
        self.create = namespace["_async_create_llm_context"]

    async def test_context_is_owner_context(self):
        owner = SimpleNamespace(id="owner-id")
        hass = SimpleNamespace(auth=SimpleNamespace(async_get_owner=AsyncMock(return_value=owner)))
        llm_context = await self.create(hass)
        # Home Assistant 2026.11 reads llm_context.context.user_id for admin-only APIs.
        self.assertIsInstance(llm_context.context, FakeContext)
        self.assertEqual(llm_context.context.user_id, "owner-id")
        self.assertEqual(llm_context.platform, "ws_mcp_server")
        self.assertIsNone(llm_context.device_id)

    async def test_no_owner_gives_none_not_dict(self):
        hass = SimpleNamespace(auth=SimpleNamespace(async_get_owner=AsyncMock(return_value=None)))
        llm_context = await self.create(hass)
        self.assertIsNone(llm_context.context)


if __name__ == "__main__":
    unittest.main()
