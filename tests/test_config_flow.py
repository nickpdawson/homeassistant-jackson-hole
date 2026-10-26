"""Config and options flow tests."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.jackson_hole.const import (
    CONF_API_URL,
    CONF_CREATE_WEBCAM_ENTITIES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_API_URL,
    DEFAULTS,
    DOMAIN,
)

USER_INPUT = {**DEFAULTS, CONF_UPDATE_INTERVAL: 30}


async def _start(hass: HomeAssistant):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_user_flow_success(hass: HomeAssistant, mock_api) -> None:
    result = await _start(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Jackson Hole Mountain Resort"
    assert result["data"] == USER_INPUT


async def test_user_flow_cannot_connect(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(DEFAULT_API_URL, status=503)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_not_the_feed(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(DEFAULT_API_URL, json={"hello": "world"})
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_timeout(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(DEFAULT_API_URL, exc=TimeoutError())
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_rejects_http(hass: HomeAssistant, aioclient_mock) -> None:
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**USER_INPUT, CONF_API_URL: DEFAULT_API_URL.replace("https:", "http:")},
    )
    assert result["errors"] == {CONF_API_URL: "https_required"}
    assert aioclient_mock.call_count == 0


async def test_user_flow_rejects_bad_url(hass: HomeAssistant, aioclient_mock) -> None:
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, CONF_API_URL: "not a url"}
    )
    assert result["errors"] == {CONF_API_URL: "invalid_url"}


async def test_user_flow_rejects_oversize(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(DEFAULT_API_URL, text="{" + " " * (3 * 1024 * 1024))
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "response_too_large"}


async def test_single_instance(hass: HomeAssistant, config_entry) -> None:
    config_entry.add_to_hass(hass)
    result = await _start(hass)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow(hass: HomeAssistant, mock_api, config_entry) -> None:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("camera.jackson_hole_mountain_resort_webcam_cody_bowl")

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            **config_entry.data,
            CONF_UPDATE_INTERVAL: 60,
            CONF_CREATE_WEBCAM_ENTITIES: False,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options[CONF_UPDATE_INTERVAL] == 60
    # Setup data is left alone; options win when read.
    assert config_entry.data[CONF_CREATE_WEBCAM_ENTITIES] is True
    assert config_entry.runtime_data.update_interval.total_seconds() == 3600
    assert hass.states.get("camera.jackson_hole_mountain_resort_webcam_cody_bowl") is None
