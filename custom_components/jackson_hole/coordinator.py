"""DataUpdateCoordinator for Jackson Hole."""
from __future__ import annotations
from datetime import timedelta
import logging
from typing import Any
import aiohttp
import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_API_URL, DEFAULT_API_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class JacksonHoleDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Jackson Hole data."""

    def __init__(
        self, hass: HomeAssistant, config: dict[str, Any], update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.api_url = config.get(CONF_API_URL, DEFAULT_API_URL)
        super().__init__(
            hass, _LOGGER, name="Jackson Hole Mountain Resort", update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            async with async_timeout.timeout(API_TIMEOUT):
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.api_url) as response:
                        if response.status != 200:
                            raise UpdateFailed(
                                f"Error fetching data: HTTP {response.status}"
                            )
                        data = await response.json()
                        # Validate response structure
                        if "respTimestamp" not in data:
                            raise UpdateFailed("Invalid API response structure")
                        _LOGGER.debug(
                            "Successfully fetched data. Timestamp: %s",
                            data.get("respTimestamp"),
                        )
                        return data
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout communicating with API") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
