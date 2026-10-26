"""Weather platform for Jackson Hole Mountain Resort."""
from __future__ import annotations
from datetime import datetime
import logging
from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    ATTRIBUTION,
    WEATHER_CONDITION_MAP,
)
from .coordinator import JacksonHoleDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jackson Hole weather entity."""
    coordinator: JacksonHoleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    if entry.data.get("create_weather_entity", True):
        async_add_entities([JacksonHoleWeather(coordinator)])


class JacksonHoleWeather(CoordinatorEntity, WeatherEntity):
    """Weather entity for Jackson Hole Mountain Resort."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_name = "Weather"
    _attr_native_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_native_wind_speed_unit = UnitOfSpeed.MILES_PER_HOUR
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, coordinator: JacksonHoleDataUpdateCoordinator) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._attr_unique_id = "jackson_hole_weather"

    @property
    def condition(self) -> str | None:
        """Return current weather condition."""
        try:
            forecast_data = self.coordinator.data.get("forecast", {})
            mid_mountain = forecast_data.get("midMountain", {})
            days = mid_mountain.get("days", [])
            if days:
                today = days[0]
                icon = today.get("icon", "")
                return WEATHER_CONDITION_MAP.get(icon, "cloudy")
            return None
        except (KeyError, IndexError, TypeError):
            return None

    @property
    def native_temperature(self) -> float | None:
        """Return current temperature."""
        try:
            weather_data = self.coordinator.data.get("weather", {})
            mid_mountain = weather_data.get("midMountain", {})
            temp_data = mid_mountain.get("temperature", {})
            return float(temp_data.get("value"))
        except (KeyError, ValueError, TypeError):
            return None

    @property
    def native_wind_speed(self) -> float | None:
        """Return current wind speed."""
        try:
            weather_data = self.coordinator.data.get("weather", {})
            mid_mountain = weather_data.get("midMountain", {})
            wind_data = mid_mountain.get("wind", {})
            value = wind_data.get("value")
            return float(value) if value is not None else None
        except (KeyError, ValueError, TypeError):
            return None

    @property
    def forecast(self) -> list[Forecast] | None:
        """Return forecast."""
        try:
            forecast_data = self.coordinator.data.get("forecast", {})
            mid_mountain = forecast_data.get("midMountain", {})
            days = mid_mountain.get("days", [])
            forecasts = []

            for day in days:
                try:
                    date_str = day.get("date")
                    if not date_str:
                        continue

                    # Parse date
                    forecast_date = datetime.strptime(date_str, "%Y-%m-%d")

                    # Map weather condition
                    icon = day.get("icon", "")
                    condition = WEATHER_CONDITION_MAP.get(icon, "cloudy")

                    # Get temperatures
                    high_temp_data = day.get("highTemperature", {})
                    low_temp_data = day.get("lowTemperature", {})

                    forecast = Forecast(
                        datetime=forecast_date.isoformat(),
                        condition=condition,
                        native_temperature=float(high_temp_data.get("value", 0)),
                        native_templow=float(low_temp_data.get("value", 0)),
                    )

                    # Add wind if available
                    wind_data = day.get("wind", {})
                    if wind_data.get("valueMin"):
                        forecast["native_wind_speed"] = float(wind_data.get("valueMin", 0))

                    forecasts.append(forecast)
                except (KeyError, ValueError, TypeError) as err:
                    _LOGGER.debug("Error parsing forecast day: %s", err)
                    continue

            return forecasts if forecasts else None
        except (KeyError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        try:
            attributes = {}

            # Add snow data
            snow_data = self.coordinator.data.get("snow", {})
            mid_mountain = snow_data.get("midMountain", {})
            depth = mid_mountain.get("totalSnowDepth", {})
            if depth.get("value"):
                attributes["snow_depth"] = f"{depth.get('value')} {depth.get('unitSymbol', 'in')}"

            snowfall_24h = mid_mountain.get("newSnowLast24H", {})
            if snowfall_24h.get("value"):
                attributes["snowfall_24h"] = f"{snowfall_24h.get('value')} {snowfall_24h.get('unitSymbol', 'in')}"

            # Add last snowfall date
            last_snow = self.coordinator.data.get("lastSnowFallDate")
            if last_snow:
                attributes["last_snowfall"] = last_snow

            # Add inversion alert if present
            if snow_data.get("inversion"):
                attributes["inversion_alert"] = snow_data.get("inversionMessage", "")

            return attributes
        except (KeyError, TypeError):
            return {}

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "jackson_hole_resort")},
            "name": "Jackson Hole Mountain Resort",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }
