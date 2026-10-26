"""Lift and trail binary sensors for Jackson Hole Mountain Resort."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import is_open, section, to_number
from .const import (
    CONF_CREATE_LIFT_ENTITIES,
    CONF_CREATE_SUMMER_ENTITIES,
    CONF_CREATE_TRAIL_ENTITIES,
    LIFT_ICONS,
    TRAIL_DIFFICULTY,
)
from .coordinator import JacksonHoleConfigEntry, JacksonHoleCoordinator, entry_config
from .entity import JacksonHoleEntity

# Trail category -> feed key.
TRAIL_SOURCES = {
    "winter": "trails",
    "hiking": "summerHikingTrails",
    "bike": "summerBikeTrails",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JacksonHoleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up lift and trail binary sensors."""
    coordinator = entry.runtime_data
    config = entry_config(entry)
    data = coordinator.data
    entities: list[BinarySensorEntity] = []

    if config[CONF_CREATE_LIFT_ENTITIES]:
        entities.extend(
            JacksonHoleLiftBinarySensor(coordinator, slug, lift)
            for slug, lift in section(data, "lifts").items()
            if isinstance(lift, dict)
        )
    categories = []
    if config[CONF_CREATE_TRAIL_ENTITIES]:
        categories.append("winter")
    if config[CONF_CREATE_SUMMER_ENTITIES]:
        categories += ["hiking", "bike"]
    for category in categories:
        entities.extend(
            JacksonHoleTrailBinarySensor(coordinator, slug, trail, category)
            for slug, trail in section(data, TRAIL_SOURCES[category]).items()
            if isinstance(trail, dict)
        )
    async_add_entities(entities)


def _with_unit(node: Any, default_unit: str) -> str | None:
    """Format a measurement as '6000 ft'. The feed sends 0 for unknown."""
    if not isinstance(node, dict):
        return None
    value = to_number(node.get("value"))
    if not value:
        return None
    return f"{value:g} {node.get('unitSymbol') or default_unit}"


def _add_measures(attributes: dict[str, Any], item: dict[str, Any], fields: dict) -> None:
    for attr, (key, unit) in fields.items():
        if (text := _with_unit(item.get(key), unit)) is not None:
            attributes[attr] = text


class JacksonHoleLiftBinarySensor(JacksonHoleEntity, BinarySensorEntity):
    """On when the lift is running."""

    _attr_translation_key = "lift"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self, coordinator: JacksonHoleCoordinator, slug: str, lift: dict[str, Any]
    ) -> None:
        super().__init__(coordinator, f"lift_{slug}")
        self._slug = slug
        self._attr_translation_placeholders = {"name": lift.get("name") or slug}
        self._attr_icon = LIFT_ICONS.get(lift.get("liftType") or "", "mdi:ski-lift")

    @property
    def _lift(self) -> dict[str, Any] | None:
        lift = section(self.coordinator.data, "lifts").get(self._slug)
        return lift if isinstance(lift, dict) else None

    @property
    def available(self) -> bool:
        return super().available and self._lift is not None

    @property
    def is_on(self) -> bool | None:
        return is_open(lift.get("openingStatus")) if (lift := self._lift) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if (lift := self._lift) is None:
            return {}
        attributes: dict[str, Any] = {
            "lift_type": lift.get("liftType"),
            "message": lift.get("message"),
            "opening_status": lift.get("openingStatus"),
        }
        _add_measures(
            attributes,
            lift,
            {
                "departure_altitude": ("departureAltitude", "ft"),
                "arrival_altitude": ("arrivalAltitude", "ft"),
                "length": ("length", "ft"),
                "speed": ("speed", "ft/sec"),
            },
        )
        return attributes


class JacksonHoleTrailBinarySensor(JacksonHoleEntity, BinarySensorEntity):
    """On when the trail is open."""

    _attr_translation_key = "trail"
    _attr_device_class = BinarySensorDeviceClass.OPENING

    def __init__(
        self,
        coordinator: JacksonHoleCoordinator,
        slug: str,
        trail: dict[str, Any],
        category: str,
    ) -> None:
        super().__init__(coordinator, f"trail_{category}_{slug}")
        self._slug = slug
        self._category = category
        self._attr_translation_placeholders = {"name": trail.get("name") or slug}
        level = trail.get("trailLevel") or ""
        self._attr_icon = TRAIL_DIFFICULTY.get(level, {}).get("icon", "mdi:ski")

    @property
    def _trail(self) -> dict[str, Any] | None:
        trails = section(self.coordinator.data, TRAIL_SOURCES[self._category])
        trail = trails.get(self._slug)
        return trail if isinstance(trail, dict) else None

    @property
    def available(self) -> bool:
        return super().available and self._trail is not None

    @property
    def is_on(self) -> bool | None:
        return is_open(trail.get("openingStatus")) if (trail := self._trail) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if (trail := self._trail) is None:
            return {}
        attributes: dict[str, Any] = {
            "trail_level": trail.get("trailLevel"),
            "trail_type": trail.get("trailType"),
            "grooming_status": trail.get("groomingStatus") or "",
            "message": trail.get("message"),
            "opening_status": trail.get("openingStatus"),
            "category": self._category,
        }
        _add_measures(
            attributes,
            trail,
            {
                "departure_altitude": ("departureAltitude", "ft"),
                "arrival_altitude": ("arrivalAltitude", "ft"),
                "length": ("length", "ft"),
            },
        )
        return attributes
