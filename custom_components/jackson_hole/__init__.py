"""Jackson Hole Mountain Resort integration for Home Assistant."""
from __future__ import annotations
import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    CONF_UPDATE_INTERVAL,
    CONF_CREATE_LIFT_ENTITIES,
    CONF_CREATE_TRAIL_ENTITIES,
    CONF_CREATE_SUMMER_ENTITIES,
    CONF_CREATE_WEATHER_ENTITY,
    CONF_CREATE_WEBCAM_ENTITIES,
    DEFAULT_UPDATE_INTERVAL,
)
from .coordinator import JacksonHoleDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Determine which platforms to load based on configuration
PLATFORMS: list[Platform] = [Platform.SENSOR]  # Always load sensors


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Jackson Hole component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Jackson Hole from a config entry."""
    # Create coordinator
    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    coordinator = JacksonHoleDataUpdateCoordinator(
        hass, entry.data, timedelta(minutes=update_interval),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Determine platforms to load
    platforms = [Platform.SENSOR]  # Always have sensors

    if entry.data.get(CONF_CREATE_LIFT_ENTITIES) or entry.data.get(CONF_CREATE_TRAIL_ENTITIES):
        platforms.append(Platform.BINARY_SENSOR)

    if entry.data.get(CONF_CREATE_WEATHER_ENTITY):
        platforms.append(Platform.WEATHER)

    if entry.data.get(CONF_CREATE_WEBCAM_ENTITIES):
        platforms.append(Platform.CAMERA)

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Determine which platforms were loaded
    platforms = [Platform.SENSOR]
    if entry.data.get(CONF_CREATE_LIFT_ENTITIES) or entry.data.get(CONF_CREATE_TRAIL_ENTITIES):
        platforms.append(Platform.BINARY_SENSOR)
    if entry.data.get(CONF_CREATE_WEATHER_ENTITY):
        platforms.append(Platform.WEATHER)
    if entry.data.get(CONF_CREATE_WEBCAM_ENTITIES):
        platforms.append(Platform.CAMERA)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
