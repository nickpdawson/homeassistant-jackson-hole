"""Sensor platform for Jackson Hole Mountain Resort."""
from __future__ import annotations
from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    ATTRIBUTION,
    TRAIL_DIFFICULTY,
)
from .coordinator import JacksonHoleDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jackson Hole sensors."""
    coordinator: JacksonHoleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        # Snow depth sensors
        JacksonHoleSnowDepthSensor(coordinator, "midMountain", "Mid-Mountain"),
        JacksonHoleSnowDepthSensor(coordinator, "tramSummit", "Summit"),
        # Snowfall sensors
        JacksonHoleSnowfallSensor(coordinator, "24h", "24 Hour"),
        JacksonHoleSnowfallSensor(coordinator, "48h", "48 Hour"),
        JacksonHoleSnowfallSensor(coordinator, "7d", "7 Day"),
        # Temperature sensors
        JacksonHoleTemperatureSensor(coordinator, "base", "Base"),
        JacksonHoleTemperatureSensor(coordinator, "midMountain", "Mid-Mountain"),
        JacksonHoleTemperatureSensor(coordinator, "tramSummit", "Summit"),
        # Wind sensors
        JacksonHoleWindSensor(coordinator, "base", "Base"),
        JacksonHoleWindSensor(coordinator, "midMountain", "Mid-Mountain"),
        JacksonHoleWindSensor(coordinator, "tramSummit", "Summit"),
        # Status sensors
        JacksonHoleLiftStatusSensor(coordinator),
        JacksonHoleTrailStatusSensor(coordinator),
        JacksonHoleTrailsByDifficultySensor(coordinator),
        # Info sensors
        JacksonHoleLastSnowfallSensor(coordinator),
        JacksonHoleLastUpdateSensor(coordinator),
    ]

    # Add summer trail sensors if enabled
    if entry.data.get("create_summer_entities", True):
        entities.extend([
            JacksonHoleSummerHikingTrailsSensor(coordinator),
            JacksonHoleSummerBikeTrailsSensor(coordinator),
        ])

    async_add_entities(entities)


class JacksonHoleBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Jackson Hole sensors."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: JacksonHoleDataUpdateCoordinator, sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_unique_id = f"jackson_hole_{sensor_type}"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "jackson_hole_resort")},
            "name": "Jackson Hole Mountain Resort",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }


class JacksonHoleSnowDepthSensor(JacksonHoleBaseSensor):
    """Snow depth sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.INCHES
    _attr_icon = "mdi:ruler"

    def __init__(
        self, coordinator: JacksonHoleDataUpdateCoordinator, location: str, location_name: str,
    ) -> None:
        """Initialize the sensor."""
        self._location = location
        self._location_name = location_name
        super().__init__(coordinator, f"snow_depth_{location}")
        self._attr_name = f"Snow Depth {location_name}"

    @property
    def native_value(self) -> float | None:
        """Return the snow depth."""
        try:
            snow_data = self.coordinator.data.get("snow", {})
            location_data = snow_data.get(self._location, {})
            depth_data = location_data.get("totalSnowDepth", {})
            return float(depth_data.get("value", 0))
        except (KeyError, ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        try:
            snow_data = self.coordinator.data.get("snow", {})
            location_data = snow_data.get(self._location, {})
            return {
                "location": self._location_name,
                "altitude": location_data.get("altitude", {}).get("value"),
                "altitude_unit": location_data.get("altitude", {}).get("unit"),
            }
        except (KeyError, TypeError):
            return {}


class JacksonHoleSnowfallSensor(JacksonHoleBaseSensor):
    """Snowfall accumulation sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.INCHES
    _attr_icon = "mdi:weather-snowy-heavy"

    def __init__(
        self, coordinator: JacksonHoleDataUpdateCoordinator, period: str, period_name: str,
    ) -> None:
        """Initialize the sensor."""
        self._period = period
        self._period_name = period_name
        super().__init__(coordinator, f"snowfall_{period}")
        self._attr_name = f"{period_name} Snowfall"

    @property
    def native_value(self) -> float | None:
        """Return the snowfall amount."""
        try:
            snow_data = self.coordinator.data.get("snow", {})
            # Use mid-mountain as default
            location_data = snow_data.get("midMountain", {})
            # Map period to API field
            field_map = {
                "24h": "newSnowLast24H",
                "48h": "newSnowLast48H",
                "7d": "newSnowLast7D",
            }
            field_name = field_map.get(self._period)
            if field_name:
                snowfall_data = location_data.get(field_name, {})
                return float(snowfall_data.get("value", 0))
            return None
        except (KeyError, ValueError, TypeError):
            return None


class JacksonHoleTemperatureSensor(JacksonHoleBaseSensor):
    """Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_icon = "mdi:thermometer"

    def __init__(
        self, coordinator: JacksonHoleDataUpdateCoordinator, location: str, location_name: str,
    ) -> None:
        """Initialize the sensor."""
        self._location = location
        self._location_name = location_name
        super().__init__(coordinator, f"temperature_{location}")
        self._attr_name = f"Temperature {location_name}"

    @property
    def native_value(self) -> float | None:
        """Return the temperature."""
        try:
            weather_data = self.coordinator.data.get("weather", {})
            location_data = weather_data.get(self._location, {})
            temp_data = location_data.get("temperature", {})
            return float(temp_data.get("value"))
        except (KeyError, ValueError, TypeError):
            return None


class JacksonHoleWindSensor(JacksonHoleBaseSensor):
    """Wind speed sensor."""

    _attr_device_class = SensorDeviceClass.WIND_SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfSpeed.MILES_PER_HOUR
    _attr_icon = "mdi:weather-windy"

    def __init__(
        self, coordinator: JacksonHoleDataUpdateCoordinator, location: str, location_name: str,
    ) -> None:
        """Initialize the sensor."""
        self._location = location
        self._location_name = location_name
        super().__init__(coordinator, f"wind_{location}")
        self._attr_name = f"Wind {location_name}"

    @property
    def native_value(self) -> float | None:
        """Return the wind speed."""
        try:
            weather_data = self.coordinator.data.get("weather", {})
            location_data = weather_data.get(self._location, {})
            wind_data = location_data.get("wind", {})
            value = wind_data.get("value")
            return float(value) if value is not None else None
        except (KeyError, ValueError, TypeError):
            return None


class JacksonHoleLiftStatusSensor(JacksonHoleBaseSensor):
    """Lift status summary sensor."""

    _attr_icon = "mdi:ski-lift"

    def __init__(self, coordinator: JacksonHoleDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "lift_status")
        self._attr_name = "Lift Status"

    @property
    def native_value(self) -> int | None:
        """Return number of open lifts."""
        try:
            lift_status = self.coordinator.data.get("liftStatus", {})
            return int(lift_status.get("openLifts", 0))
        except (KeyError, ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        try:
            lift_status = self.coordinator.data.get("liftStatus", {})
            return {
                "total_lifts": lift_status.get("totalLifts", 0),
                "open_lifts": lift_status.get("openLifts", 0),
                "expected_open_lifts": lift_status.get("expectedOpenLifts", 0),
            }
        except (KeyError, TypeError):
            return {}


class JacksonHoleTrailStatusSensor(JacksonHoleBaseSensor):
    """Trail status summary sensor."""

    _attr_icon = "mdi:ski"

    def __init__(self, coordinator: JacksonHoleDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "trail_status")
        self._attr_name = "Trail Status"

    @property
    def native_value(self) -> int | None:
        """Return number of open trails."""
        try:
            trail_status = self.coordinator.data.get("trailStatus", {})
            return int(trail_status.get("openTrails", 0))
        except (KeyError, ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        try:
            trail_status = self.coordinator.data.get("trailStatus", {})
            return {
                "total_trails": trail_status.get("totalTrails", 0),
                "open_trails": trail_status.get("openTrails", 0),
                "groomed_trails": trail_status.get("groomedTrails", 0),
                "total_parks": trail_status.get("totalParks", 0),
                "open_parks": trail_status.get("openParks", 0),
            }
        except (KeyError, TypeError):
            return {}


class JacksonHoleTrailsByDifficultySensor(JacksonHoleBaseSensor):
    """Trail breakdown by difficulty sensor."""

    _attr_icon = "mdi:ski"

    def __init__(self, coordinator: JacksonHoleDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "trails_by_difficulty")
        self._attr_name = "Trails by Difficulty"

    @property
    def native_value(self) -> int | None:
        """Return total number of trails."""
        try:
            trail_status = self.coordinator.data.get("trailStatus", {})
            return int(trail_status.get("totalTrails", 0))
        except (KeyError, ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return trail breakdown by difficulty."""
        try:
            trails = self.coordinator.data.get("trails", {})
            # Count trails by difficulty
            difficulty_counts = {}
            open_counts = {}
            groomed_counts = {}

            for trail_data in trails.values():
                level = trail_data.get("trailLevel", "UNKNOWN")
                status = trail_data.get("openingStatus", "CLOSED")
                grooming = trail_data.get("groomingStatus", "")

                # Total count
                difficulty_counts[level] = difficulty_counts.get(level, 0) + 1

                # Open count
                if status == "OPEN":
                    open_counts[level] = open_counts.get(level, 0) + 1

                # Groomed count
                if grooming:
                    groomed_counts[level] = groomed_counts.get(level, 0) + 1

            # Build attributes with friendly names
            attributes = {}
            for level, count in difficulty_counts.items():
                friendly_name = TRAIL_DIFFICULTY.get(level, {}).get("name", level)
                attributes[f"{friendly_name.lower().replace(' ', '_')}_total"] = count
                attributes[f"{friendly_name.lower().replace(' ', '_')}_open"] = open_counts.get(level, 0)
                attributes[f"{friendly_name.lower().replace(' ', '_')}_groomed"] = groomed_counts.get(level, 0)

            return attributes
        except (KeyError, TypeError):
            return {}


class JacksonHoleSummerHikingTrailsSensor(JacksonHoleBaseSensor):
    """Summer hiking trails sensor."""

    _attr_icon = "mdi:hiking"

    def __init__(self, coordinator: JacksonHoleDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "summer_hiking_trails")
        self._attr_name = "Summer Hiking Trails"

    @property
    def native_value(self) -> int | None:
        """Return number of open hiking trails."""
        try:
            summer_status = self.coordinator.data.get("summerTrailStatus", {})
            return int(summer_status.get("openHikingTrails", 0))
        except (KeyError, ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        try:
            summer_status = self.coordinator.data.get("summerTrailStatus", {})
            return {
                "total_hiking_trails": summer_status.get("totalHikingTrails", 0),
                "open_hiking_trails": summer_status.get("openHikingTrails", 0),
            }
        except (KeyError, TypeError):
            return {}


class JacksonHoleSummerBikeTrailsSensor(JacksonHoleBaseSensor):
    """Summer bike trails sensor."""

    _attr_icon = "mdi:bike"

    def __init__(self, coordinator: JacksonHoleDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "summer_bike_trails")
        self._attr_name = "Summer Bike Trails"

    @property
    def native_value(self) -> int | None:
        """Return number of open bike trails."""
        try:
            summer_status = self.coordinator.data.get("summerTrailStatus", {})
            return int(summer_status.get("openBikeTrails", 0))
        except (KeyError, ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        try:
            summer_status = self.coordinator.data.get("summerTrailStatus", {})
            return {
                "total_bike_trails": summer_status.get("totalBikeTrails", 0),
                "open_bike_trails": summer_status.get("openBikeTrails", 0),
            }
        except (KeyError, TypeError):
            return {}


class JacksonHoleLastSnowfallSensor(JacksonHoleBaseSensor):
    """Last snowfall date sensor."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: JacksonHoleDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "last_snowfall")
        self._attr_name = "Last Snowfall"

    @property
    def native_value(self) -> str | None:
        """Return last snowfall date."""
        try:
            return self.coordinator.data.get("lastSnowFallDate")
        except (KeyError, TypeError):
            return None


class JacksonHoleLastUpdateSensor(JacksonHoleBaseSensor):
    """Last update timestamp sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:update"

    def __init__(self, coordinator: JacksonHoleDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "last_update")
        self._attr_name = "Last Update"

    @property
    def native_value(self) -> datetime | None:
        """Return last update timestamp."""
        try:
            timestamp_str = self.coordinator.data.get("respTimestamp")
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return None
        except (KeyError, ValueError, TypeError):
            return None
