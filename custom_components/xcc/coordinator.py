"""Coordinator for polling XCC component state."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import XCCApi, XCCApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN


@dataclass
class XCCSnapshot:
    """Current component, global, and unit data used by entities."""

    components: dict[str, dict[str, Any]]
    global_data: dict[str, Any]
    units: list[dict[str, Any]]


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
            components = await self.api.async_get_functions()
            extended = await self.api.async_get_extended_data()
            global_data = _find_global_data(extended)
            units = _safe_units(global_data.pop("units", None))
            return XCCSnapshot(
                components=components,
                global_data=global_data,
                units=units,
            )
        except XCCApiError as err:
            raise UpdateFailed(f"XCC request failed: {err}") from err


def _find_global_data(data: dict[str, Any]) -> dict[str, Any]:
    """Select safe global fields and discard owner/address metadata."""
    candidate = data.get("null")
    if not isinstance(candidate, dict):
        candidate = next(
            (
                value
                for value in data.values()
                if isinstance(value, dict)
                and ("idGlobal" in value or "units" in value or "tempOut" in value)
            ),
            {},
        )
    if not isinstance(candidate, dict):
        return {}

    allowed = {
        "on",
        "error",
        "tempOut",
        "powerAct",
        "tempAct",
        "tempReq",
        "hdo",
        "hdoIgnore",
        "hdoIgnoreTemp",
        "units",
    }
    return {key: value for key, value in candidate.items() if key in allowed}


def _safe_units(value: Any) -> list[dict[str, Any]]:
    """Keep only documented measurement fields from each unit."""
    if not isinstance(value, list):
        return []
    allowed = {
        "pump",
        "power",
        "tcj",
        "mototime",
        "fanUp",
        "fanLo",
        "ts",
        "td",
        "te",
        "curr",
    }
    return [
        {key: item for key, item in unit.items() if key in allowed}
        for unit in value
        if isinstance(unit, dict)
    ]
