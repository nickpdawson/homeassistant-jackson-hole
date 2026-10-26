"""Diagnostics for Jackson Hole Mountain Resort."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .api import section
from .coordinator import JacksonHoleConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: JacksonHoleConfigEntry
) -> dict[str, Any]:
    """Return entry settings and the last feed response.

    The feed is public resort data and the entry holds no secrets, so
    nothing is redacted.
    """
    coordinator = entry.runtime_data
    data = coordinator.data or {}
    return {
        "entry": {
            "version": entry.version,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "coordinator": {
            "api_url": coordinator.api_url,
            "update_interval_seconds": coordinator.update_interval.total_seconds()
            if coordinator.update_interval
            else None,
            "last_update_success": coordinator.last_update_success,
            "last_exception": repr(coordinator.last_exception)
            if coordinator.last_exception
            else None,
        },
        "counts": {
            "lifts": len(section(data, "lifts")),
            "trails": len(section(data, "trails")),
            "summer_hiking_trails": len(section(data, "summerHikingTrails")),
            "summer_bike_trails": len(section(data, "summerBikeTrails")),
            "webcams": len(data.get("webcams") or []),
            "forecast_days": len(
                section(data, "forecast", "midMountain").get("days") or []
            ),
        },
        "data": data,
    }
