"""Config flow for Jackson Hole Mountain Resort."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import ApiError, ResponseTooLarge, fetch_data
from .const import (
    CONF_API_URL,
    CONF_CREATE_LIFT_ENTITIES,
    CONF_CREATE_SUMMER_ENTITIES,
    CONF_CREATE_TRAIL_ENTITIES,
    CONF_CREATE_WEATHER_ENTITY,
    CONF_CREATE_WEBCAM_ENTITIES,
    CONF_UPDATE_INTERVAL,
    DEFAULTS,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    NAME,
)

_LOGGER = logging.getLogger(__name__)

TOGGLES = (
    CONF_CREATE_LIFT_ENTITIES,
    CONF_CREATE_TRAIL_ENTITIES,
    CONF_CREATE_SUMMER_ENTITIES,
    CONF_CREATE_WEATHER_ENTITY,
    CONF_CREATE_WEBCAM_ENTITIES,
)


def _schema(current: dict[str, Any]) -> vol.Schema:
    values = {**DEFAULTS, **current}
    interval = max(
        MIN_UPDATE_INTERVAL, min(MAX_UPDATE_INTERVAL, int(values[CONF_UPDATE_INTERVAL]))
    )
    fields: dict[Any, Any] = {
        vol.Required(CONF_API_URL, default=values[CONF_API_URL]): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)
        ),
        vol.Required(CONF_UPDATE_INTERVAL, default=interval): vol.All(
            NumberSelector(
                NumberSelectorConfig(
                    min=MIN_UPDATE_INTERVAL,
                    max=MAX_UPDATE_INTERVAL,
                    step=1,
                    unit_of_measurement="min",
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Coerce(int),
        ),
    }
    for key in TOGGLES:
        fields[vol.Required(key, default=bool(values[key]))] = bool
    return vol.Schema(fields)


async def validate_input(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, str]:
    """Check the URL and try one fetch. Returns form errors, empty on success."""
    url = str(user_input.get(CONF_API_URL, "")).strip()
    try:
        cv.url(url)
    except vol.Invalid:
        return {CONF_API_URL: "invalid_url"}
    if urlparse(url).scheme != "https":
        return {CONF_API_URL: "https_required"}
    user_input[CONF_API_URL] = url
    try:
        await fetch_data(async_get_clientsession(hass), url)
    except ResponseTooLarge:
        return {"base": "response_too_large"}
    except ApiError as err:
        _LOGGER.debug("API check failed for %s: %s", url, err)
        return {"base": "cannot_connect"}
    return {}


class JacksonHoleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up Jackson Hole Mountain Resort from the UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            errors = await validate_input(self.hass, user_input)
            if not errors:
                return self.async_create_entry(title=NAME, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(_schema({}), user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> JacksonHoleOptionsFlow:
        return JacksonHoleOptionsFlow()


class JacksonHoleOptionsFlow(OptionsFlow):
    """Change the API URL, polling interval and which entities to create."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        current = {**DEFAULTS, **self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            # Only re-check the API when the URL changes, so an outage does
            # not block changing the interval or the entity choices.
            if user_input.get(CONF_API_URL) != current[CONF_API_URL]:
                errors = await validate_input(self.hass, user_input)
            if not errors:
                return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(_schema(current), user_input),
            errors=errors,
        )
