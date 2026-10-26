"""Base entity for Jackson Hole Mountain Resort."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DEVICE_IDENTIFIER, DOMAIN, MANUFACTURER, MODEL, NAME
from .coordinator import JacksonHoleCoordinator


class JacksonHoleEntity(CoordinatorEntity[JacksonHoleCoordinator]):
    """Shared device, naming and unique_id for every entity in the entry."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: JacksonHoleCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DEVICE_IDENTIFIER)},
            name=NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://www.jacksonhole.com/mountain-report",
        )
