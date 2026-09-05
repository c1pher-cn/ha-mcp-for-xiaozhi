import logging
import anyio
import asyncio
import aiohttp
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp import types
from mcp.shared.message import SessionMessage

from homeassistant.components import conversation
from homeassistant.const import CONF_LLM_HASS_API
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import llm

from .const import DOMAIN
from .server import create_server
from .session import Session
from .types import WsMCPServerConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant,  entry: WsMCPServerConfigEntry) -> bool:
    """Set up MCP Server from a config entry."""
    hass.async_create_task(_connect_loop(hass, entry))
    #hass.async_create_task(_connect_to_client(hass, entry))
    return True

def async_get_config_entry(hass: HomeAssistant) -> WsMCPServerConfigEntry:
    """Get the first enabled MCP server config entry."""
    config_entries: list[WsMCPServerConfigEntry] = (
        hass.config_entries.async_loaded_entries(DOMAIN)
    )
    if not config_entries:
        raise RuntimeError("Model Context Protocol server is not configured")
    if len(config_entries) > 1:
        raise RuntimeError("Found multiple Model Context Protocol configurations")
    return config_entries[0]


async def _connect_loop(hass: HomeAssistant, entry: WsMCPServerConfigEntry) -> None:
    """Reconnect on failure loop."""
    while True:
        try:
            _LOGGER.info("mcp websocket.py loop")
            if await _connect_to_client(hass, entry) == False:
                break
        except Exception as e:
            _LOGGER.warning("mcp WebSocket disconnected or failed: %s", e)
        _LOGGER.info("mcp websocket.py retry after 20 seconds")
        await asyncio.sleep(20)  # 20秒后重连

async def _connect_to_client(hass: HomeAssistant, entry: WsMCPServerConfigEntry) -> None:
    """Connect to external WebSocket endpoint as MCP server."""
    #entry = async_get_config_entry(hass)
    session_manager = entry.runtime_data
    endpoint = entry.data.get("client_endpoint")
    if not endpoint:
        _LOGGER.error("No client endpoint configured in config entry")
        return False

    _LOGGER.info("mcp websocket.py _connect_to_client")
    context = llm.LLMContext(
        platform=DOMAIN,
        context={},  # Could be extended
        language="*",
        assistant=conversation.DOMAIN,
        device_id=None,
    )
    llm_api_id = entry.data[CONF_LLM_HASS_API]
    _LOGGER.info("mcp llm_api_id: %s", llm_api_id)
    server = await create_server(hass, llm_api_id, context)
    options = await hass.async_add_executor_job(server.create_initialization_options)

    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)
    
    bReConnect = True
    async with session_manager.create(Session(read_stream_writer)) as session_id:
        _LOGGER.info("mcp Connecting to MCP client at: %s", endpoint)
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as client_session:
            try:
                async with client_session.ws_connect(endpoint) as ws:
                    async def ws_reader():
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    json_data = msg.json()
                                    message = types.JSONRPCMessage.model_validate(json_data)
                                    #_LOGGER.info("mcp reader: %s", message)
                                    #await read_stream_writer.send(message)
                                    session_message = SessionMessage(message)
                                    _LOGGER.info("mcp reader: %s", session_message)
                                    await read_stream_writer.send(session_message)
                                except Exception as err:
                                    _LOGGER.error("mcp Invalid message from client: %s", err)
                            elif msg.type == aiohttp.WSMsgType.CLOSE:
                                _LOGGER.error("mcp WebSocket closed: %s", msg.extra)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                _LOGGER.error("mcp WebSocket error: %s", msg.data)
                        _LOGGER.info("websocket was closed")
                        tg.cancel_scope.cancel()  #立即取消任务组,避免50秒的心跳等待
                    async def ws_writer():
                        #async for message in write_stream_reader:
                        #    _LOGGER.info("mcp writer: %s", message)
                        #    await ws.send_str(message.model_dump_json(by_alias=True, exclude_none=True))
                        async for session_message in write_stream_reader:
                            _LOGGER.info("mcp writer: %s", session_message)
                            # 从 SessionMessage 中提取实际的 JSONRPCMessage
                            actual_message = session_message.message
                            await ws.send_str(actual_message.model_dump_json(by_alias=True, exclude_none=True))
                        _LOGGER.info("disconnect websocket")
                        nonlocal bReConnect
                        bReConnect = False
                        await ws.close()  #断开旧websocket连接
                    async def heartbeat():
                        while True:
                            try:
                                await asyncio.sleep(50)
                                _LOGGER.info("mcp heartbeat")
                                await ws.ping()
                            except Exception as e:
                                _LOGGER.info("mcp heartbeat ping failed: %s", e)
                                break  # 主动退出 heartbeat，让整个连接关闭并重连
                    async with anyio.create_task_group() as tg:
                        tg.start_soon(ws_reader)
                        tg.start_soon(ws_writer)
                        tg.start_soon(heartbeat)
                        await server.run(read_stream, write_stream, options)
            except Exception as e:
                _LOGGER.exception("mcp Failed to connect to client WebSocket at %s: %s", endpoint, e)
    return bReConnect
