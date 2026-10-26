"""The Jackson Hole Mountain Resort integration."""
from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .api import webcam_keys
from .const import (
    CONF_CREATE_LIFT_ENTITIES,
    CONF_CREATE_SUMMER_ENTITIES,
    CONF_CREATE_TRAIL_ENTITIES,
    CONF_CREATE_WEATHER_ENTITY,
    CONF_CREATE_WEBCAM_ENTITIES,
    DOMAIN,
)
from .coordinator import JacksonHoleConfigEntry, JacksonHoleCoordinator, entry_config

_LOGGER = logging.getLogger(__name__)

# Every platform loads; each one decides which entities to add from the
# entry settings. Unload then always matches what was set up.
PLATFORMS = [Platform.BINARY_SENSOR, Platform.CAMERA, Platform.SENSOR, Platform.WEATHER]

LEGACY_PREFIX = "jackson_hole_"
LEGACY_WEBCAM = re.compile(r"webcam_(\d+)")


async def async_setup_entry(hass: HomeAssistant, entry: JacksonHoleConfigEntry) -> bool:
    """Set up Jackson Hole Mountain Resort from a config entry."""
    coordinator = JacksonHoleCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await _async_migrate_unique_ids(hass, entry, coordinator.data)
    _async_remove_disabled_entities(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: JacksonHoleConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: JacksonHoleConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_migrate_unique_ids(
    hass: HomeAssistant, entry: JacksonHoleConfigEntry, data: dict[str, Any]
) -> None:
    """Move pre-2.0 unique_ids to entry-scoped ids.

    Old ids were 'jackson_hole_<key>'. Webcams used their position in the
    feed list, which breaks when the resort reorders cameras, so they move
    to a key built from the caption at that position today.
    """
    registry = er.async_get(hass)
    cams = webcam_keys(data.get("webcams"))
    prefix = entry.entry_id

    @callback
    def _migrate(entity: er.RegistryEntry) -> dict[str, str] | None:
        old = entity.unique_id
        if not old.startswith(LEGACY_PREFIX):
            return None
        key = old.removeprefix(LEGACY_PREFIX)
        if match := LEGACY_WEBCAM.fullmatch(key):
            index = int(match.group(1))
            if index >= len(cams):
                return None
            key = f"webcam_{cams[index]}"
        new = f"{prefix}_{key}"
        if registry.async_get_entity_id(entity.domain, DOMAIN, new):
            _LOGGER.warning(
                "Not migrating %s: unique_id %s is already in use", entity.entity_id, new
            )
            return None
        _LOGGER.debug("Migrating %s unique_id %s -> %s", entity.entity_id, old, new)
        return {"new_unique_id": new}

    await er.async_migrate_entries(hass, entry.entry_id, _migrate)


@callback
def _async_remove_disabled_entities(hass: HomeAssistant, entry: JacksonHoleConfigEntry) -> None:
    """Drop entities for groups the user turned off in options."""
    config = entry_config(entry)
    eid = entry.entry_id
    dropped: list[str] = []
    if not config[CONF_CREATE_LIFT_ENTITIES]:
        dropped.append(f"{eid}_lift_")
    if not config[CONF_CREATE_TRAIL_ENTITIES]:
        dropped.append(f"{eid}_trail_winter_")
    if not config[CONF_CREATE_SUMMER_ENTITIES]:
        dropped += [
            f"{eid}_trail_hiking_",
            f"{eid}_trail_bike_",
            f"{eid}_summer_hiking_trails",
            f"{eid}_summer_bike_trails",
        ]
    if not config[CONF_CREATE_WEATHER_ENTITY]:
        dropped.append(f"{eid}_weather")
    if not config[CONF_CREATE_WEBCAM_ENTITIES]:
        dropped.append(f"{eid}_webcam_")
    if not dropped:
        return
    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, eid):
        if entity.unique_id.startswith(tuple(dropped)):
            registry.async_remove(entity.entity_id)
