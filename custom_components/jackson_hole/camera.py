"""Webcam still images for Jackson Hole Mountain Resort."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any
from urllib.parse import urlparse

import aiohttp

from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import ApiError, read_limited, webcam_keys
from .const import (
    CONF_CREATE_WEBCAM_ENTITIES,
    FETCH_TIMEOUT,
    IMAGE_CACHE_SECONDS,
    MAX_IMAGE_BYTES,
)
from .coordinator import JacksonHoleConfigEntry, JacksonHoleCoordinator, entry_config
from .entity import JacksonHoleEntity

_LOGGER = logging.getLogger(__name__)

# Below this requested width, the feed's thumbnail is good enough.
THUMBNAIL_MAX_WIDTH = 640


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JacksonHoleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up one camera per webcam in the feed."""
    if not entry_config(entry)[CONF_CREATE_WEBCAM_ENTITIES]:
        return
    coordinator = entry.runtime_data
    webcams = coordinator.data.get("webcams")
    async_add_entities(
        JacksonHoleWebcam(coordinator, key, cam)
        for key, cam in zip(webcam_keys(webcams), webcams or [])
    )


def _https_url(value: Any) -> str | None:
    """Only fetch https URLs; the feed decides what we download."""
    if isinstance(value, str) and urlparse(value).scheme == "https":
        return value
    return None


class JacksonHoleWebcam(JacksonHoleEntity, Camera):
    """Still image from one resort webcam."""

    _attr_translation_key = "webcam"
    _attr_frame_interval = IMAGE_CACHE_SECONDS

    def __init__(
        self, coordinator: JacksonHoleCoordinator, key: str, webcam: dict[str, Any]
    ) -> None:
        JacksonHoleEntity.__init__(self, coordinator, f"webcam_{key}")
        Camera.__init__(self)
        self._key = key
        self._attr_translation_placeholders = {
            "name": webcam.get("caption") or webcam.get("altText") or key
        }
        self._cache: dict[str, tuple[float, bytes]] = {}

    @property
    def _webcam(self) -> dict[str, Any] | None:
        webcams = self.coordinator.data.get("webcams")
        for key, cam in zip(webcam_keys(webcams), webcams or []):
            if key == self._key:
                return cam
        return None

    @property
    def available(self) -> bool:
        return super().available and self._webcam is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if (cam := self._webcam) is None:
            return {}
        return {
            "caption": cam.get("caption") or "",
            "alt_text": cam.get("altText") or "",
            "is_pano_cam": bool(cam.get("isPanoCam")),
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        if (cam := self._webcam) is None:
            return None
        url = _https_url(cam.get("url"))
        if width is not None and width <= THUMBNAIL_MAX_WIDTH:
            url = _https_url(cam.get("thumbUrl")) or url
        if url is None:
            return None

        cached = self._cache.get(url)
        if cached and time.monotonic() - cached[0] < IMAGE_CACHE_SECONDS:
            return cached[1]

        try:
            async with asyncio.timeout(FETCH_TIMEOUT):
                async with self.coordinator.session.get(url) as response:
                    if response.status != 200:
                        _LOGGER.debug("Webcam %s returned HTTP %s", url, response.status)
                        return cached[1] if cached else None
                    if not response.content_type.startswith("image/"):
                        _LOGGER.debug("Webcam %s sent %s, not an image", url, response.content_type)
                        return cached[1] if cached else None
                    image = await read_limited(response, MAX_IMAGE_BYTES)
        except (TimeoutError, aiohttp.ClientError, ApiError) as err:
            _LOGGER.debug("Could not fetch webcam %s: %s", url, err)
            return cached[1] if cached else None

        self._cache[url] = (time.monotonic(), image)
        return image
