"""Binary sensors for XCC component properties."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import XCCConfigEntry
from .entity import XCCEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: XCCConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors for boolean component properties."""
    coordinator = entry.runtime_data
    entities = [
        XCCBinarySensor(coordinator, entry.entry_id, component_id, component, path, value)
        for component_id, component in coordinator.data.items()
        for path, value in _boolean_values(component)
    ]
    async_add_entities(entities)


class XCCBinarySensor(XCCEntity, BinarySensorEntity):
    """Read-only binary sensor for an XCC property."""

    @property
    def is_on(self) -> bool | None:
        """Return the latest boolean property value."""
        return self.value if isinstance(self.value, bool) else None


def _boolean_values(data: dict, prefix: tuple[str, ...] = ()):
    """Recursively yield boolean leaf values, omitting identity metadata."""
    for key, value in data.items():
        if key in {"id", "name", "TYPE", "type", "icon"}:
            continue
        path = (*prefix, str(key))
        if isinstance(value, dict):
            yield from _boolean_values(value, path)
        elif isinstance(value, bool):
            yield path, value
