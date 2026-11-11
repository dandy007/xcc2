"""Base entities for XCC components."""

from __future__ import annotations

import re

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XCCCoordinator

_PROPERTY_LABELS = {
    "acttemp": "Aktuální teplota",
    "actualtemp": "Aktuální teplota",
    "actualwater": "Aktuální teplota vody",
    "actualtuv": "Aktuální teplota TUV",
    "acttuv": "Aktuální teplota TUV",
    "alarm": "Alarm",
    "antiledionella": "Antilegionelní ohřev",
    "cirkulace": "Cirkulace TUV",
    "compressor": "Kompresor",
    "curr": "Odebíraný proud",
    "current": "Proud",
    "enabled": "Povoleno",
    "error": "Chyba",
    "errorcode": "Kód chyby",
    "fanlo": "Otáčky dolního ventilátoru",
    "fanup": "Otáčky horního ventilátoru",
    "frequency": "Frekvence",
    "flow": "Průtok",
    "hdo": "Respektovat HDO",
    "hdoignore": "Ignorovat HDO",
    "hdoignoretemp": "Teplotní mez ignorování HDO",
    "heatpump": "Tepelné čerpadlo",
    "icon": "Ikona",
    "mototime": "Počítadlo motohodin",
    "mintuv": "Minimální teplota TUV",
    "natop": "Natápění",
    "on": "Zapnuto",
    "operationmode": "Provozní režim",
    "power": "Výkon jednotky",
    "poweract": "Výkon tepelného čerpadla",
    "powerkw": "Vypočtený výkon",
    "powerpct": "Výkon jednotky",
    "pressure": "Tlak",
    "reqprop": "Požadovaná hodnota",
    "reqtemp": "Požadovaná teplota",
    "requestair": "Požadovaná teplota vzduchu",
    "requestwater": "Požadovaná teplota vody",
    "running": "V provozu",
    "state": "Stav",
    "status": "Provozní stav",
    "tempact": "Aktuální teplota topné vody",
    "tcj": "Teplota kondenzátu (TCj)",
    "td": "Teplota TD",
    "te": "Teplota TE",
    "tempout": "Venkovní teplota",
    "tempreq": "Požadovaná teplota topné vody",
    "ts": "Teplota TS",
    "warning": "Varování",
    "pump": "Čerpadlo",
}

_WORD_LABELS = {
    "act": "Aktuální",
    "actual": "Aktuální",
    "air": "vzduchu",
    "alarm": "Alarm",
    "capacity": "Výkon",
    "code": "Kód",
    "current": "Proud",
    "desired": "Požadovaná",
    "error": "Chyba",
    "fan": "ventilátor",
    "flow": "Průtok",
    "heat": "Topení",
    "indoor": "Vnitřní",
    "input": "Vstupní",
    "mode": "Režim",
    "outdoor": "Venkovní",
    "output": "Výstupní",
    "power": "Výkon",
    "pressure": "Tlak",
    "pump": "čerpadlo",
    "req": "Požadovaná",
    "request": "Požadovaná",
    "room": "Pokojová",
    "rpm": "Otáčky",
    "run": "Provoz",
    "speed": "Rychlost",
    "state": "Stav",
    "status": "Stav",
    "temp": "teplota",
    "temperature": "teplota",
    "tuv": "TUV",
    "water": "vody",
}


def _property_label(part: str) -> str:
    """Return a Czech display label for a PLC property path segment."""
    if label := _PROPERTY_LABELS.get(part.casefold()):
        return label

    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", part)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    words = re.sub(r"[_-]+", " ", spaced).split()
    return " ".join(_WORD_LABELS.get(word.casefold(), word.capitalize()) for word in words)


class XCCEntity(CoordinatorEntity[XCCCoordinator]):
    """Base class for a scalar property on an XCC component."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: XCCCoordinator,
        entry_id: str,
        source: str,
        source_id: str,
        component: dict | None,
        property_path: tuple[str, ...],
        value: bool | int | float | str,
    ) -> None:
        super().__init__(coordinator)
        self.source = source
        self.source_id = source_id
        self.property_path = property_path
        if source == "component":
            self._attr_unique_id = f"{entry_id}_{source_id}_{'_'.join(property_path)}"
            device_id = f"{entry_id}_{source_id}"
            device_name = str((component or {}).get("name") or f"XCC komponent {source_id}")
            model = str((component or {}).get("TYPE", "PLC komponent")).rsplit(".", 1)[-1]
        elif source == "global":
            self._attr_unique_id = f"{entry_id}_global_{'_'.join(property_path)}"
            device_id = f"{entry_id}_global"
            device_name = "Systém"
            model = "Globální regulátor"
        else:
            self._attr_unique_id = f"{entry_id}_unit_{source_id}_{'_'.join(property_path)}"
            device_id = f"{entry_id}_unit_{source_id}"
            device_name = f"Tepelné čerpadlo {int(source_id) + 1}"
            model = "Tepelné čerpadlo"
        self._attr_name = " · ".join(_property_label(part) for part in property_path)
        self._attr_native_value = value
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer="XCC",
            model=model,
        )

    @property
    def value(self):
        """Read the latest value from coordinator data."""
        if self.source == "component":
            value = self.coordinator.data.components.get(self.source_id, {})
        elif self.source == "global":
            value = self.coordinator.data.global_data
        else:
            units = self.coordinator.data.units
            index = int(self.source_id)
            value = units[index] if index < len(units) else {}
        for part in self.property_path:
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        return value

    @property
    def available(self) -> bool:
        """Only report values for currently available controller data."""
        return super().available and self.value is not None

