"""Binary sensor platform for Jackson Hole Mountain Resort."""
from __future__ import annotations
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    ATTRIBUTION,
    CONF_CREATE_LIFT_ENTITIES,
    CONF_CREATE_TRAIL_ENTITIES,
    CONF_CREATE_SUMMER_ENTITIES,
    LIFT_TYPE,
    TRAIL_DIFFICULTY,
    OPENING_STATUS_MAP,
)
from .coordinator import JacksonHoleDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jackson Hole binary sensors."""
    coordinator: JacksonHoleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # Add lift entities if enabled
    if entry.data.get(CONF_CREATE_LIFT_ENTITIES, False):
        lifts = coordinator.data.get("lifts", {})
        for lift_slug, lift_data in lifts.items():
            entities.append(JacksonHoleLiftBinarySensor(coordinator, lift_slug, lift_data))

    # Add trail entities if enabled
    if entry.data.get(CONF_CREATE_TRAIL_ENTITIES, False):
        trails = coordinator.data.get("trails", {})
        for trail_slug, trail_data in trails.items():
            entities.append(JacksonHoleTrailBinarySensor(coordinator, trail_slug, trail_data, "winter"))

    # Add summer trail entities if enabled
    if entry.data.get(CONF_CREATE_SUMMER_ENTITIES, False):
        # Hiking trails
        hiking_trails = coordinator.data.get("summerHikingTrails", {})
        for trail_slug, trail_data in hiking_trails.items():
            entities.append(JacksonHoleTrailBinarySensor(coordinator, trail_slug, trail_data, "hiking"))

        # Bike trails
        bike_trails = coordinator.data.get("summerBikeTrails", {})
        for trail_slug, trail_data in bike_trails.items():
            entities.append(JacksonHoleTrailBinarySensor(coordinator, trail_slug, trail_data, "bike"))

    async_add_entities(entities)


class JacksonHoleLiftBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for individual lift."""

    _attr_attribution = ATTRIBUTION
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: JacksonHoleDataUpdateCoordinator, lift_slug: str, lift_data: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._lift_slug = lift_slug
        self._attr_name = f"Lift {lift_data.get('name', lift_slug)}"
        self._attr_unique_id = f"jackson_hole_lift_{lift_slug}"

        # Set icon based on lift type
        lift_type = lift_data.get("liftType", "")
        lift_info = LIFT_TYPE.get(lift_type, {})
        self._attr_icon = lift_info.get("icon", "mdi:ski-lift")

    @property
    def is_on(self) -> bool:
        """Return true if lift is open."""
        try:
            lifts = self.coordinator.data.get("lifts", {})
            lift = lifts.get(self._lift_slug, {})
            status = lift.get("openingStatus", "CLOSED")
            return OPENING_STATUS_MAP.get(status, "closed") == "open"
        except (KeyError, TypeError):
            return False

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        try:
            lifts = self.coordinator.data.get("lifts", {})
            lift = lifts.get(self._lift_slug, {})
            attributes = {
                "lift_type": lift.get("liftType"),
                "message": lift.get("message"),
                "opening_status": lift.get("openingStatus"),
            }

            # Add altitude data
            departure = lift.get("departureAltitude", {})
            if departure.get("value"):
                attributes["departure_altitude"] = f"{departure.get('value')} {departure.get('unitSymbol', 'ft')}"

            arrival = lift.get("arrivalAltitude", {})
            if arrival.get("value"):
                attributes["arrival_altitude"] = f"{arrival.get('value')} {arrival.get('unitSymbol', 'ft')}"

            # Add length and speed
            length = lift.get("length", {})
            if length.get("value"):
                attributes["length"] = f"{length.get('value')} {length.get('unitSymbol', 'ft')}"

            speed = lift.get("speed", {})
            if speed.get("value"):
                attributes["speed"] = f"{speed.get('value')} {speed.get('unitSymbol', 'mph')}"

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


class JacksonHoleTrailBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for individual trail."""

    _attr_attribution = ATTRIBUTION
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: JacksonHoleDataUpdateCoordinator, trail_slug: str, trail_data: dict, trail_category: str,  # "winter", "hiking", or "bike"
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._trail_slug = trail_slug
        self._trail_category = trail_category
        self._attr_name = f"Trail {trail_data.get('name', trail_slug)}"
        self._attr_unique_id = f"jackson_hole_trail_{trail_category}_{trail_slug}"

        # Set icon based on trail difficulty
        trail_level = trail_data.get("trailLevel", "")
        difficulty_info = TRAIL_DIFFICULTY.get(trail_level, {})
        self._attr_icon = difficulty_info.get("icon", "mdi:ski")

    @property
    def is_on(self) -> bool:
        """Return true if trail is open."""
        try:
            # Get trail data from appropriate category
            if self._trail_category == "winter":
                trails = self.coordinator.data.get("trails", {})
            elif self._trail_category == "hiking":
                trails = self.coordinator.data.get("summerHikingTrails", {})
            else:  # bike
                trails = self.coordinator.data.get("summerBikeTrails", {})

            trail = trails.get(self._trail_slug, {})
            status = trail.get("openingStatus", "CLOSED")
            return OPENING_STATUS_MAP.get(status, "closed") == "open"
        except (KeyError, TypeError):
            return False

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        try:
            # Get trail data from appropriate category
            if self._trail_category == "winter":
                trails = self.coordinator.data.get("trails", {})
            elif self._trail_category == "hiking":
                trails = self.coordinator.data.get("summerHikingTrails", {})
            else:  # bike
                trails = self.coordinator.data.get("summerBikeTrails", {})

            trail = trails.get(self._trail_slug, {})
            attributes = {
                "trail_level": trail.get("trailLevel"),
                "trail_type": trail.get("trailType"),
                "grooming_status": trail.get("groomingStatus", ""),
                "message": trail.get("message"),
                "opening_status": trail.get("openingStatus"),
                "category": self._trail_category,
            }

            # Add altitude data
            departure = trail.get("departureAltitude", {})
            if departure.get("value") and int(departure.get("value", 0)) > 0:
                attributes["departure_altitude"] = f"{departure.get('value')} {departure.get('unitSymbol', 'ft')}"

            arrival = trail.get("arrivalAltitude", {})
            if arrival.get("value") and int(arrival.get("value", 0)) > 0:
                attributes["arrival_altitude"] = f"{arrival.get('value')} {arrival.get('unitSymbol', 'ft')}"

            # Add length
            length = trail.get("length", {})
            if length.get("value") and int(length.get("value", 0)) > 0:
                attributes["length"] = f"{length.get('value')} {length.get('unitSymbol', 'ft')}"

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
