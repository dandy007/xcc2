"""Config flow for XCC."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from aiohttp import CookieJar
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import XCCApi, XCCApiError
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DEFAULT_HOST, DOMAIN


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for XCC."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Configure controller host and credentials."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = _normalize_host(user_input[CONF_HOST])
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()
            session = async_create_clientsession(self.hass, cookie_jar=CookieJar(unsafe=True))
            api = XCCApi(host, user_input[CONF_USERNAME], user_input[CONF_PASSWORD], session)
            try:
                await api.async_login()
                await api.async_get_functions()
            except XCCApiError as err:
                error = str(err)
                errors["base"] = error if error in {
                    "cannot_connect", "invalid_auth", "invalid_response", "http_403", "http_404"
                } else "unknown"
            else:
                return self.async_create_entry(
                    title=urlparse(host).hostname or host,
                    data={**user_input, CONF_HOST: host},
                )
            finally:
                await session.close()

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, DEFAULT_HOST)): str,
                vol.Required(CONF_USERNAME, default=(user_input or {}).get(CONF_USERNAME, "")): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


def _normalize_host(host: str) -> str:
    """Add a scheme when the user enters a bare hostname or IP address."""
    value = host.strip().rstrip("/")
    if not value.startswith(("http://", "https://")):
        value = f"http://{value}"
    return value


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate credentials against the controller."""
    host = _normalize_host(data[CONF_HOST])
    session = async_create_clientsession(hass, cookie_jar=CookieJar(unsafe=True))
    try:
        api = XCCApi(host, data[CONF_USERNAME], data[CONF_PASSWORD], session)
        await api.async_login()
        await api.async_get_functions()
    finally:
        await session.close()
    return {CONF_HOST: host}
