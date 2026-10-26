"""Weather forecast tests."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.weather import DOMAIN as WEATHER_DOMAIN, SERVICE_GET_FORECASTS
from homeassistant.core import HomeAssistant

from custom_components.jackson_hole.weather import map_condition

ENTITY = "weather.jackson_hole_mountain_resort_weather"


async def test_daily_forecast(hass: HomeAssistant, mock_api, config_entry) -> None:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY)
    assert state.state == "partlycloudy"
    assert state.attributes["temperature"] == 42
    assert state.attributes["snow_depth"] == "40 in"

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {"entity_id": ENTITY, "type": "daily"},
        blocking=True,
        return_response=True,
    )
    forecast = response[ENTITY]["forecast"]
    assert len(forecast) == 6
    dates = [datetime.fromisoformat(day["datetime"]) for day in forecast]
    assert dates[0].date().isoformat() == "2026-10-26"
    assert all(d.tzinfo is not None for d in dates)
    assert forecast[0]["temperature"] == 45
    assert forecast[0]["templow"] == 34
    assert forecast[0]["wind_speed"] == 9
    assert forecast[0]["wind_bearing"] == "South"
    assert forecast[4]["condition"] == "snowy"


def test_map_condition() -> None:
    assert map_condition("icon-svg_sun") == "sunny"
    assert map_condition("icon-svg_heavysnow") == "snowy"
    assert map_condition("icon-svg_new_kind") is None
    assert map_condition("") is None
    assert map_condition(None) is None
