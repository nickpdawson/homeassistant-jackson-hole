"""Weather entity for Jackson Hole Mountain Resort."""
from __future__ import annotations

from datetime import datetime, time
from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import child, measure, parse_date, section, to_number
from .const import CONF_CREATE_WEATHER_ENTITY, RESORT_TIME_ZONE, WEATHER_CONDITION_MAP
from .coordinator import JacksonHoleConfigEntry, JacksonHoleCoordinator, entry_config
from .entity import JacksonHoleEntity

type Data = dict[str, Any]


def map_condition(icon: Any) -> str | None:
    """Map a feed icon class like 'icon-svg_sun' to an HA condition."""
    if not isinstance(icon, str) or not icon:
        return None
    return WEATHER_CONDITION_MAP.get(icon.strip())


def _days(data: Data) -> list[dict[str, Any]]:
    days = child(data, "forecast", "midMountain", "days")
    if not isinstance(days, list):
        return []
    return [day for day in days if isinstance(day, dict)]


def build_forecast(data: Data) -> list[Forecast]:
    """Daily forecast for mid-mountain, dated midnight resort time."""
    tz = dt_util.get_time_zone(RESORT_TIME_ZONE)
    forecast: list[Forecast] = []
    for day in _days(data):
        if (when := parse_date(day.get("date"))) is None:
            continue
        item = Forecast(
            datetime=datetime.combine(when, time.min, tzinfo=tz).isoformat(),
            condition=map_condition(day.get("icon")),
            native_temperature=measure(day, "highTemperature"),
            native_templow=measure(day, "lowTemperature"),
        )
        wind = section(day, "wind")
        if (speed := to_number(wind.get("valueMin"))) is not None:
            item["native_wind_speed"] = speed
        if direction := wind.get("direction"):
            item["wind_bearing"] = direction
        if (chance := measure(day, "precipitationChance")) is not None:
            item["precipitation_probability"] = int(chance)
        forecast.append(item)
    return forecast


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JacksonHoleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the weather entity."""
    if entry_config(entry)[CONF_CREATE_WEATHER_ENTITY]:
        async_add_entities([JacksonHoleWeather(entry.runtime_data)])


class JacksonHoleWeather(JacksonHoleEntity, WeatherEntity):
    """Mid-mountain conditions and the resort's daily forecast."""

    _attr_translation_key = "weather"
    _attr_native_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_native_wind_speed_unit = UnitOfSpeed.MILES_PER_HOUR
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, coordinator: JacksonHoleCoordinator) -> None:
        super().__init__(coordinator, "weather")

    @property
    def condition(self) -> str | None:
        # The feed has no current condition; today's forecast icon is closest.
        days = _days(self.coordinator.data)
        return map_condition(days[0].get("icon")) if days else None

    @property
    def native_temperature(self) -> float | None:
        return measure(self.coordinator.data, "weather", "midMountain", "temperature")

    @property
    def native_wind_speed(self) -> float | None:
        return measure(self.coordinator.data, "weather", "midMountain", "wind")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        snow = section(data, "snow")
        mid = section(snow, "midMountain")
        attributes: dict[str, Any] = {}
        if (depth := measure(mid, "totalSnowDepth")) is not None:
            attributes["snow_depth"] = f"{depth:g} in"
        if (fresh := measure(mid, "newSnowLast24H")) is not None:
            attributes["snowfall_24h"] = f"{fresh:g} in"
        if last_snow := data.get("lastSnowFallDate"):
            attributes["last_snowfall"] = last_snow
        if snow.get("inversion") is True:
            attributes["inversion_alert"] = snow.get("inversionMessage") or ""
        return attributes

    async def async_forecast_daily(self) -> list[Forecast] | None:
        return build_forecast(self.coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        super()._handle_coordinator_update()
        self.coordinator.config_entry.async_create_task(
            self.hass, self.async_update_listeners(("daily",))
        )
