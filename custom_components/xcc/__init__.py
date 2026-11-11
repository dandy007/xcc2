"""XCC PLC integration."""

from __future__ import annotations

from aiohttp import CookieJar
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import XCCApi
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, PLATFORMS
from .coordinator import XCCCoordinator

type XCCConfigEntry = ConfigEntry[XCCCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: XCCConfigEntry) -> bool:
    """Set up XCC from a config entry."""
    session = async_create_clientsession(hass, cookie_jar=CookieJar(unsafe=True))
    api = XCCApi(
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        session,
    )
    try:
        await api.async_login()
        coordinator = XCCCoordinator(hass, api)
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await session.close()
        raise

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: XCCConfigEntry) -> bool:
    """Unload an XCC config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.api.session.close()
    return unload_ok
