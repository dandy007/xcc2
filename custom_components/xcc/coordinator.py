"""Coordinator for polling XCC component state."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import XCCApi, XCCApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN


class XCCCoordinator(DataUpdateCoordinator):
    """Poll component data from the XCC controller."""

    def __init__(self, hass: HomeAssistant, api: XCCApi) -> None:
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self):
        try:
            return await self.api.async_get_functions()
        except XCCApiError as err:
            raise UpdateFailed(f"XCC request failed: {err}") from err
