"""Camera platform for Jackson Hole Mountain Resort."""
from __future__ import annotations
import logging
import aiohttp
import async_timeout

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL, ATTRIBUTION, API_TIMEOUT
from .coordinator import JacksonHoleDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jackson Hole webcam entities."""
    coordinator: JacksonHoleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    if not entry.data.get("create_webcam_entities", True):
        return

    entities = []
    webcams = coordinator.data.get("webcams", [])
    for index, webcam_data in enumerate(webcams):
        entities.append(JacksonHoleWebcam(coordinator, index, webcam_data))

    async_add_entities(entities)


class JacksonHoleWebcam(CoordinatorEntity, Camera):
    """Webcam entity for Jackson Hole Mountain Resort."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: JacksonHoleDataUpdateCoordinator, index: int, webcam_data: dict,
    ) -> None:
        """Initialize the camera."""
        super().__init__(coordinator)
        self._index = index
        self._attr_name = f"Webcam {webcam_data.get('caption', f'Camera {index + 1}')}"
        self._attr_unique_id = f"jackson_hole_webcam_{index}"
        Camera.__init__(self)

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        try:
            webcams = self.coordinator.data.get("webcams", [])
            if self._index < len(webcams):
                webcam = webcams[self._index]
                return {
                    "caption": webcam.get("caption", ""),
                    "alt_text": webcam.get("altText", ""),
                    "is_pano_cam": webcam.get("isPanoCam", False),
                }
            return {}
        except (KeyError, IndexError, TypeError):
            return {}

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return webcam image."""
        try:
            webcams = self.coordinator.data.get("webcams", [])
            if self._index >= len(webcams):
                return None

            webcam = webcams[self._index]
            url = webcam.get("url")
            if not url:
                return None

            async with async_timeout.timeout(API_TIMEOUT):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.read()
                        _LOGGER.error(
                            "Error fetching webcam image: HTTP %s", response.status
                        )
                        return None
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching webcam image: %s", err)
            return None
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching webcam image")
            return None
        except Exception as err:
            _LOGGER.error("Unexpected error fetching webcam image: %s", err)
            return None

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "jackson_hole_resort")},
            "name": "Jackson Hole Mountain Resort",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }
