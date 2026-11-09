
"""The Model Context Protocol Server integration."""

from __future__ import annotations
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
import logging
from . import websocket_transport
from .const import DOMAIN
from .session import SessionManager
from .types import WsMCPServerConfigEntry
_LOGGER = logging.getLogger(__name__)

__all__ = [
    "CONFIG_SCHEMA",
    "DOMAIN",
    "async_setup",
    "async_setup_entry",
    "async_unload_entry",
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Model Context Protocol component."""
    #websocket_transport.async_register(hass)
    return True



async def async_setup_entry(hass: HomeAssistant, entry: WsMCPServerConfigEntry) -> bool:
    """Set up Model Context Protocol Server from a config entry."""
    async def _system_started(event):
        try:
            # 为每个配置实例创建独立的会话管理器
            session_manager = SessionManager()
            # 将会话管理器存储在 hass.data 中,使用 entry.entry_id 作为唯一键
            hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
                "session_manager": session_manager,
                "config": entry.data
            }
            # 添加状态实体
            hass.states.async_set(f"{DOMAIN}.{entry.entry_id}_status", "connecting")

            entry.runtime_data = session_manager
            await websocket_transport.async_setup_entry(hass, entry)
            hass.states.async_set(f"{DOMAIN}.{entry.entry_id}_status", "connected")
        except ConnectionError as ex:
            hass.states.async_set(f"{DOMAIN}.{entry.entry_id}_status", "error")
            _LOGGER.error("MCP connect failed due to connection error: %s", ex)
            await websocket_transport.async_stop_entry(hass, entry)
            # 清理已添加的 session_manager
            if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
                hass.data[DOMAIN].pop(entry.entry_id)
        except Exception as ex:
            hass.states.async_set(f"{DOMAIN}.{entry.entry_id}_status", "error")
            _LOGGER.error("MCP connect failed: %s", ex)
            await websocket_transport.async_stop_entry(hass, entry)
            if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
                hass.data[DOMAIN].pop(entry.entry_id)
    if hass.is_running:
        await _system_started(None)
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _system_started)
    return True
    


async def async_unload_entry(hass: HomeAssistant, entry: WsMCPServerConfigEntry) -> bool:
    """Unload a config entry."""
    await websocket_transport.async_stop_entry(hass, entry)
    # 清理资源
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        entry_data = hass.data[DOMAIN][entry.entry_id]
        session_manager = entry_data.get("session_manager")
        if session_manager is not None:
            session_manager.close()
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return True
