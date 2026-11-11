"""Sensors for scalar XCC component properties."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfElectricCurrent, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import XCCConfigEntry
from .entity import XCCEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: XCCConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up read-only sensors for scalar component properties."""
    coordinator = entry.runtime_data
    entities: list[XCCSensor] = []
    for component_id, component in coordinator.data.items():
        for path, value in _scalar_values(component):
            if isinstance(value, bool):
                continue
            entity = XCCSensor(coordinator, entry.entry_id, component_id, component, path, value)
            entities.append(entity)
    async_add_entities(entities)


class XCCSensor(XCCEntity, SensorEntity):
    """Read-only sensor for an XCC property."""

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        key = self.property_path[-1].lower()
        self._attr_native_value = self.value
        if "temp" in key or key in {"tcj", "ts", "td", "te"}:
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            if isinstance(self.value, (int, float)):
                self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key in {"curr", "current"}:
            self._attr_device_class = SensorDeviceClass.CURRENT
            self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
            if isinstance(self.value, (int, float)):
                self._attr_state_class = SensorStateClass.MEASUREMENT
        elif isinstance(self.value, (int, float)):
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return latest property value."""
        return self.value


def _scalar_values(data: dict[str, Any], prefix: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    """Recursively yield supported leaf values, omitting identity metadata."""
    for key, value in data.items():
        if key in {"id", "name", "TYPE", "type", "icon"}:
            continue
        path = (*prefix, str(key))
        if isinstance(value, dict):
            yield from _scalar_values(value, path)
        elif value is None or isinstance(value, (bool, int, float, str)):
            yield path, value
