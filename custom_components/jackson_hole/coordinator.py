"""Data update coordinator for Jackson Hole Mountain Resort."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiError, fetch_data
from .const import (
    CONF_API_URL,
    CONF_UPDATE_INTERVAL,
    DEFAULTS,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__package__)

type JacksonHoleConfigEntry = ConfigEntry[JacksonHoleCoordinator]


def entry_config(entry: ConfigEntry) -> dict[str, Any]:
    """Return defaults, then setup data, then options saved later."""
    return {**DEFAULTS, **entry.data, **entry.options}


class JacksonHoleCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls all.json."""

    config_entry: JacksonHoleConfigEntry

    def __init__(self, hass: HomeAssistant, entry: JacksonHoleConfigEntry) -> None:
        config = entry_config(entry)
        minutes = max(
            MIN_UPDATE_INTERVAL, min(MAX_UPDATE_INTERVAL, int(config[CONF_UPDATE_INTERVAL]))
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=minutes),
        )
        self.api_url: str = config[CONF_API_URL]
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await fetch_data(self.session, self.api_url)
        except ApiError as err:
            raise UpdateFailed(str(err)) from err
        _LOGGER.debug("Fetched feed, respTimestamp %s", data.get("respTimestamp"))
        return data
