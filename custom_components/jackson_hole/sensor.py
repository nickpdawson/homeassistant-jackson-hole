"""Sensors for Jackson Hole Mountain Resort."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import is_open, measure, parse_date, parse_timestamp, section, to_int
from .const import CONF_CREATE_SUMMER_ENTITIES, TRAIL_DIFFICULTY
from .coordinator import JacksonHoleConfigEntry, JacksonHoleCoordinator, entry_config
from .entity import JacksonHoleEntity

type Data = dict[str, Any]

# Feed location key -> name used in the old entity names.
SNOW_LOCATIONS = {"midMountain": "mid_mountain", "tramSummit": "summit"}
WEATHER_LOCATIONS = {"base": "base", "midMountain": "mid_mountain", "tramSummit": "summit"}
# Snowfall is reported at mid-mountain.
SNOWFALL_FIELDS = {"24h": "newSnowLast24H", "48h": "newSnowLast48H", "7d": "newSnowLast7D"}


@dataclass(frozen=True, kw_only=True)
class JacksonHoleSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Data], float | int | str | date | datetime | None]
    attrs_fn: Callable[[Data], dict[str, Any]] | None = None


def _count(path: str, field: str) -> Callable[[Data], int | None]:
    return lambda data: to_int(section(data, path).get(field))


def _snow_depth_attrs(location: str) -> Callable[[Data], dict[str, Any]]:
    def attrs(data: Data) -> dict[str, Any]:
        loc = section(data, "snow", location)
        return {
            "location": loc.get("name"),
            "altitude": measure(loc, "altitude"),
            "altitude_unit": section(loc, "altitude").get("unit"),
        }

    return attrs


def _lift_attrs(data: Data) -> dict[str, Any]:
    status = section(data, "liftStatus")
    return {
        "total_lifts": to_int(status.get("totalLifts")),
        "open_lifts": to_int(status.get("openLifts")),
        "expected_open_lifts": to_int(status.get("expectedOpenLifts")),
    }


def _trail_attrs(data: Data) -> dict[str, Any]:
    status = section(data, "trailStatus")
    return {
        "total_trails": to_int(status.get("totalTrails")),
        "open_trails": to_int(status.get("openTrails")),
        "groomed_trails": to_int(status.get("groomedTrails")),
        "total_parks": to_int(status.get("totalParks")),
        "open_parks": to_int(status.get("openParks")),
    }


def _difficulty_attrs(data: Data) -> dict[str, Any]:
    totals: dict[str, int] = {}
    opened: dict[str, int] = {}
    groomed: dict[str, int] = {}
    for trail in section(data, "trails").values():
        if not isinstance(trail, dict):
            continue
        level = trail.get("trailLevel") or "UNKNOWN"
        totals[level] = totals.get(level, 0) + 1
        if is_open(trail.get("openingStatus")):
            opened[level] = opened.get(level, 0) + 1
        if trail.get("groomingStatus"):
            groomed[level] = groomed.get(level, 0) + 1
    attributes: dict[str, Any] = {}
    for level, count in totals.items():
        name = TRAIL_DIFFICULTY.get(level, {}).get("name", level).lower().replace(" ", "_")
        attributes[f"{name}_total"] = count
        attributes[f"{name}_open"] = opened.get(level, 0)
        attributes[f"{name}_groomed"] = groomed.get(level, 0)
    return attributes


def _summer_attrs(kind: str) -> Callable[[Data], dict[str, Any]]:
    def attrs(data: Data) -> dict[str, Any]:
        status = section(data, "summerTrailStatus")
        return {
            f"total_{kind}_trails": to_int(status.get(f"total{kind.title()}Trails")),
            f"open_{kind}_trails": to_int(status.get(f"open{kind.title()}Trails")),
        }

    return attrs


SENSORS: list[JacksonHoleSensorDescription] = [
    *(
        JacksonHoleSensorDescription(
            key=f"snow_depth_{loc}",
            translation_key=f"snow_depth_{name}",
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfLength.INCHES,
            value_fn=lambda data, loc=loc: measure(data, "snow", loc, "totalSnowDepth"),
            attrs_fn=_snow_depth_attrs(loc),
        )
        for loc, name in SNOW_LOCATIONS.items()
    ),
    *(
        JacksonHoleSensorDescription(
            key=f"snowfall_{period}",
            translation_key=f"snowfall_{period}",
            device_class=SensorDeviceClass.PRECIPITATION,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPrecipitationDepth.INCHES,
            value_fn=lambda data, field=field: measure(data, "snow", "midMountain", field),
        )
        for period, field in SNOWFALL_FIELDS.items()
    ),
    *(
        JacksonHoleSensorDescription(
            key=f"temperature_{loc}",
            translation_key=f"temperature_{name}",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
            value_fn=lambda data, loc=loc: measure(data, "weather", loc, "temperature"),
        )
        for loc, name in WEATHER_LOCATIONS.items()
    ),
    *(
        JacksonHoleSensorDescription(
            key=f"wind_{loc}",
            translation_key=f"wind_{name}",
            device_class=SensorDeviceClass.WIND_SPEED,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
            value_fn=lambda data, loc=loc: measure(data, "weather", loc, "wind"),
        )
        for loc, name in WEATHER_LOCATIONS.items()
    ),
    JacksonHoleSensorDescription(
        key="lift_status",
        translation_key="lift_status",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_count("liftStatus", "openLifts"),
        attrs_fn=_lift_attrs,
    ),
    JacksonHoleSensorDescription(
        key="trail_status",
        translation_key="trail_status",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_count("trailStatus", "openTrails"),
        attrs_fn=_trail_attrs,
    ),
    JacksonHoleSensorDescription(
        key="trails_by_difficulty",
        translation_key="trails_by_difficulty",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_count("trailStatus", "totalTrails"),
        attrs_fn=_difficulty_attrs,
    ),
    JacksonHoleSensorDescription(
        key="last_snowfall",
        translation_key="last_snowfall",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda data: parse_date(data.get("lastSnowFallDate")),
    ),
    JacksonHoleSensorDescription(
        key="last_update",
        translation_key="last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: parse_timestamp(data.get("respTimestamp")),
    ),
]

SUMMER_SENSORS: list[JacksonHoleSensorDescription] = [
    JacksonHoleSensorDescription(
        key=f"summer_{kind}_trails",
        translation_key=f"summer_{kind}_trails",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_count("summerTrailStatus", f"open{kind.title()}Trails"),
        attrs_fn=_summer_attrs(kind),
    )
    for kind in ("hiking", "bike")
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JacksonHoleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Jackson Hole sensors."""
    coordinator = entry.runtime_data
    descriptions = list(SENSORS)
    if entry_config(entry)[CONF_CREATE_SUMMER_ENTITIES]:
        descriptions += SUMMER_SENSORS
    async_add_entities(JacksonHoleSensor(coordinator, d) for d in descriptions)


class JacksonHoleSensor(JacksonHoleEntity, SensorEntity):
    """A value read from all.json."""

    entity_description: JacksonHoleSensorDescription

    def __init__(
        self, coordinator: JacksonHoleCoordinator, description: JacksonHoleSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | int | str | date | datetime | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)
