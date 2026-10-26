"""Setup, unload, reload, entity, migration and diagnostics tests."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jackson_hole.const import DEFAULT_API_URL, DOMAIN
from custom_components.jackson_hole.diagnostics import async_get_config_entry_diagnostics

P = "jackson_hole_mountain_resort"


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_unload_reload(hass: HomeAssistant, mock_api, config_entry) -> None:
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retries_when_api_down(
    hass: HomeAssistant, aioclient_mock, config_entry
) -> None:
    aioclient_mock.get(DEFAULT_API_URL, status=500)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_retries_on_timeout(
    hass: HomeAssistant, aioclient_mock, config_entry
) -> None:
    aioclient_mock.get(DEFAULT_API_URL, exc=TimeoutError())
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_sensors(hass: HomeAssistant, mock_api, config_entry) -> None:
    await _setup(hass, config_entry)

    depth = hass.states.get(f"sensor.{P}_snow_depth_mid_mountain")
    assert depth.state == "40.0"
    # The feed sends "10,000".
    assert depth.attributes["altitude"] == 10000.0
    assert hass.states.get(f"sensor.{P}_snow_depth_summit").state == "74.0"

    snow = hass.states.get(f"sensor.{P}_24_hour_snowfall")
    assert snow.state == "0.0"
    assert snow.attributes["device_class"] == "precipitation"
    # Mid-mountain sends {} for 7 days; that is unknown, not 0.
    assert hass.states.get(f"sensor.{P}_7_day_snowfall").state == STATE_UNKNOWN

    assert hass.states.get(f"sensor.{P}_temperature_mid_mountain").state == "42.0"
    assert hass.states.get(f"sensor.{P}_wind_base").state == STATE_UNKNOWN

    lifts = hass.states.get(f"sensor.{P}_lift_status")
    assert lifts.state == "0"
    assert lifts.attributes["total_lifts"] == 13
    assert lifts.attributes["state_class"] == "measurement"

    by_level = hass.states.get(f"sensor.{P}_trails_by_difficulty")
    assert by_level.state == "130"
    assert by_level.attributes["intermediate_total"] == 2
    assert by_level.attributes["intermediate_groomed"] == 2

    # Was a plain string before 2.0.0, which the date device class rejects.
    assert hass.states.get(f"sensor.{P}_last_snowfall").state == "2026-04-12"
    assert hass.states.get(f"sensor.{P}_last_update").state == "2026-10-26T19:58:00+00:00"
    assert hass.states.get(f"sensor.{P}_summer_hiking_trails").state == "0"


async def test_binary_sensors(hass: HomeAssistant, aioclient_mock, feed, config_entry) -> None:
    feed["trails"]["easyDoesIt"]["openingStatus"] = "OPEN"
    feed["summerBikeTrails"] = {
        "lowerLeisure": {"name": "Lower Leisure", "openingStatus": "OPEN", "trailLevel": "GREEN"}
    }
    aioclient_mock.get(DEFAULT_API_URL, json=feed)
    await _setup(hass, config_entry)

    tram = hass.states.get(f"binary_sensor.{P}_lift_aerial_tram")
    assert tram.state == STATE_OFF
    assert tram.attributes["device_class"] == "running"
    assert tram.attributes["departure_altitude"] == "6000 ft"
    # The feed sends 0 for unknown lengths.
    assert "length" not in tram.attributes

    trail = hass.states.get(f"binary_sensor.{P}_trail_easy_does_it")
    assert trail.state == STATE_ON
    assert trail.attributes["device_class"] == "opening"
    assert trail.attributes["grooming_status"] == "Groomed AM"

    # Summer trails load even with lift and trail entities off in 1.0.0
    # (the binary_sensor platform was skipped then).
    bike = hass.states.get(f"binary_sensor.{P}_trail_lower_leisure")
    assert bike.state == STATE_ON

    registry = er.async_get(hass)
    assert (
        registry.async_get(f"binary_sensor.{P}_lift_aerial_tram").unique_id
        == f"{config_entry.entry_id}_lift_aerialTram"
    )


async def test_one_device(hass: HomeAssistant, mock_api, config_entry) -> None:
    await _setup(hass, config_entry)
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), config_entry.entry_id)
    assert len(devices) == 1
    # Same identifier as 1.0.0, so the device id survives the upgrade.
    assert devices[0].identifiers == {(DOMAIN, "jackson_hole_resort")}


async def test_lift_gone_from_feed(
    hass: HomeAssistant, aioclient_mock, feed, config_entry
) -> None:
    aioclient_mock.get(DEFAULT_API_URL, json=feed)
    await _setup(hass, config_entry)
    del feed["lifts"]["aerialTram"]
    aioclient_mock.clear_requests()
    aioclient_mock.get(DEFAULT_API_URL, json=feed)
    await config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(f"binary_sensor.{P}_lift_aerial_tram").state == "unavailable"


async def test_unique_id_migration(hass: HomeAssistant, mock_api, config_entry) -> None:
    config_entry.add_to_hass(hass)
    registry = er.async_get(hass)
    old = {
        "sensor": "jackson_hole_snow_depth_midMountain",
        "binary_sensor": "jackson_hole_lift_aerialTram",
        "weather": "jackson_hole_weather",
    }
    entries = {
        domain: registry.async_get_or_create(
            domain, DOMAIN, unique_id, config_entry=config_entry, suggested_object_id=f"old_{domain}"
        )
        for domain, unique_id in old.items()
    }
    # Index 1 in the feed is "Summit - Pano Cam".
    cam = registry.async_get_or_create(
        "camera", DOMAIN, "jackson_hole_webcam_1", config_entry=config_entry,
        suggested_object_id="old_cam",
    )
    gone_cam = registry.async_get_or_create(
        "camera", DOMAIN, "jackson_hole_webcam_9", config_entry=config_entry
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    eid = config_entry.entry_id
    assert registry.async_get(entries["sensor"].entity_id).unique_id == f"{eid}_snow_depth_midMountain"
    assert registry.async_get(entries["binary_sensor"].entity_id).unique_id == f"{eid}_lift_aerialTram"
    assert registry.async_get(entries["weather"].entity_id).unique_id == f"{eid}_weather"
    assert registry.async_get(cam.entity_id).unique_id == f"{eid}_webcam_summit_pano_cam"
    assert registry.async_get(gone_cam.entity_id).unique_id == "jackson_hole_webcam_9"

    # Old entity_ids keep working and no duplicates appear.
    assert hass.states.get("sensor.old_sensor").state == "40.0"
    assert hass.states.get("camera.old_cam") is not None
    assert hass.states.get(f"sensor.{P}_snow_depth_mid_mountain") is None
    assert hass.states.get(f"camera.{P}_webcam_summit_pano_cam") is None


async def test_disabled_groups_removed(hass: HomeAssistant, mock_api, config_entry) -> None:
    await _setup(hass, config_entry)
    assert hass.states.get(f"binary_sensor.{P}_trail_easy_does_it")
    hass.config_entries.async_update_entry(
        config_entry, options={**config_entry.data, "create_trail_entities": False}
    )
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    assert registry.async_get(f"binary_sensor.{P}_trail_easy_does_it") is None
    assert registry.async_get(f"binary_sensor.{P}_lift_aerial_tram") is not None


async def test_camera_image(hass: HomeAssistant, mock_api, config_entry) -> None:
    from homeassistant.components.camera import async_get_image

    full = "https://cams.jacksonhole.com/webcam/codybowl.jpg"
    thumb = "https://cams.jacksonhole.com/webcam/thumbnails/codybowl.jpg"
    mock_api.get(full, content=b"full", headers={"Content-Type": "image/jpeg"})
    mock_api.get(thumb, content=b"thumb", headers={"Content-Type": "image/jpeg"})
    await _setup(hass, config_entry)

    entity_id = f"camera.{P}_webcam_cody_bowl"
    assert (await async_get_image(hass, entity_id)).content == b"full"
    assert (await async_get_image(hass, entity_id, width=320)).content == b"thumb"
    calls = mock_api.call_count
    # Cached for a minute.
    assert (await async_get_image(hass, entity_id)).content == b"full"
    assert mock_api.call_count == calls


async def test_diagnostics(hass: HomeAssistant, mock_api, config_entry) -> None:
    await _setup(hass, config_entry)
    diag = await async_get_config_entry_diagnostics(hass, config_entry)
    assert diag["counts"]["lifts"] == 13
    assert diag["counts"]["webcams"] == 3
    assert diag["counts"]["forecast_days"] == 6
    assert diag["coordinator"]["last_update_success"] is True
