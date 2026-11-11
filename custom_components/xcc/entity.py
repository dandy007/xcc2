"""Base entities for XCC components."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XCCCoordinator


class XCCEntity(CoordinatorEntity[XCCCoordinator]):
    """Base class for a scalar property on an XCC component."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: XCCCoordinator,
        entry_id: str,
        component_id: str,
        component: dict,
        property_path: tuple[str, ...],
        value: bool | int | float | str,
    ) -> None:
        super().__init__(coordinator)
        self.component_id = component_id
        self.property_path = property_path
        self._attr_unique_id = f"{entry_id}_{component_id}_{'_'.join(property_path)}"
        self._attr_name = " ".join(part.replace("_", " ").capitalize() for part in property_path)
        self._attr_native_value = value
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{component_id}")},
            name=str(component.get("name") or f"XCC komponent {component_id}"),
            manufacturer="XCC",
            model=str(component.get("TYPE", "PLC komponent")).rsplit(".", 1)[-1],
        )

    @property
    def value(self):
        """Read the latest value from coordinator data."""
        value = self.coordinator.data.get(self.component_id, {})
        for part in self.property_path:
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        return value

    @property
    def available(self) -> bool:
        """Only report values for currently available controller data."""
        return super().available and self.value is not None

