"""Config flow for Jackson Hole Mountain Resort integration."""
from __future__ import annotations
import logging
from typing import Any
import aiohttp
import async_timeout
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    NAME,
    DEFAULT_API_URL,
    DEFAULT_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
    DEFAULT_CREATE_LIFT_ENTITIES,
    DEFAULT_CREATE_TRAIL_ENTITIES,
    DEFAULT_CREATE_SUMMER_ENTITIES,
    DEFAULT_CREATE_WEATHER_ENTITY,
    DEFAULT_CREATE_WEBCAM_ENTITIES,
    CONF_API_URL,
    CONF_UPDATE_INTERVAL,
    CONF_CREATE_LIFT_ENTITIES,
    CONF_CREATE_TRAIL_ENTITIES,
    CONF_CREATE_SUMMER_ENTITIES,
    CONF_CREATE_WEATHER_ENTITY,
    CONF_CREATE_WEBCAM_ENTITIES,
    API_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


async def validate_api_url(hass: HomeAssistant, api_url: str) -> dict[str, Any]:
    """Validate the API URL by attempting to fetch data."""
    try:
        async with async_timeout.timeout(API_TIMEOUT):
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status != 200:
                        raise ValueError(f"API returned status {response.status}")
                    data = await response.json()
                    # Validate response structure
                    if "respTimestamp" not in data:
                        raise ValueError("Invalid API response structure")
                    return {"title": NAME}
    except aiohttp.ClientError as err:
        _LOGGER.error("Error connecting to API: %s", err)
        raise ValueError("Cannot connect to API") from err
    except asyncio.TimeoutError as err:
        _LOGGER.error("Timeout connecting to API")
        raise ValueError("Timeout connecting to API") from err
    except Exception as err:
        _LOGGER.error("Unexpected error validating API: %s", err)
        raise ValueError("Unexpected error validating API") from err


class JacksonHoleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jackson Hole Mountain Resort."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate API URL
            try:
                info = await validate_api_url(self.hass, user_input[CONF_API_URL])
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        # Show configuration form
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_API_URL,
                    default=DEFAULT_API_URL,
                ): cv.string,
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=DEFAULT_UPDATE_INTERVAL,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
                vol.Required(
                    CONF_CREATE_LIFT_ENTITIES,
                    default=DEFAULT_CREATE_LIFT_ENTITIES,
                ): cv.boolean,
                vol.Required(
                    CONF_CREATE_TRAIL_ENTITIES,
                    default=DEFAULT_CREATE_TRAIL_ENTITIES,
                ): cv.boolean,
                vol.Required(
                    CONF_CREATE_SUMMER_ENTITIES,
                    default=DEFAULT_CREATE_SUMMER_ENTITIES,
                ): cv.boolean,
                vol.Required(
                    CONF_CREATE_WEATHER_ENTITY,
                    default=DEFAULT_CREATE_WEATHER_ENTITY,
                ): cv.boolean,
                vol.Required(
                    CONF_CREATE_WEBCAM_ENTITIES,
                    default=DEFAULT_CREATE_WEBCAM_ENTITIES,
                ): cv.boolean,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> JacksonHoleOptionsFlow:
        """Get the options flow for this handler."""
        return JacksonHoleOptionsFlow(config_entry)


class JacksonHoleOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Jackson Hole."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate API URL if changed
            if user_input[CONF_API_URL] != self.config_entry.data.get(CONF_API_URL):
                try:
                    await validate_api_url(self.hass, user_input[CONF_API_URL])
                except ValueError:
                    errors["base"] = "cannot_connect"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

            if not errors:
                # Update config entry
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=user_input,
                )
                return self.async_create_entry(title="", data={})

        # Show options form with current values
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_API_URL,
                    default=self.config_entry.data.get(CONF_API_URL, DEFAULT_API_URL),
                ): cv.string,
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=self.config_entry.data.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
                vol.Required(
                    CONF_CREATE_LIFT_ENTITIES,
                    default=self.config_entry.data.get(
                        CONF_CREATE_LIFT_ENTITIES, DEFAULT_CREATE_LIFT_ENTITIES
                    ),
                ): cv.boolean,
                vol.Required(
                    CONF_CREATE_TRAIL_ENTITIES,
                    default=self.config_entry.data.get(
                        CONF_CREATE_TRAIL_ENTITIES, DEFAULT_CREATE_TRAIL_ENTITIES
                    ),
                ): cv.boolean,
                vol.Required(
                    CONF_CREATE_SUMMER_ENTITIES,
                    default=self.config_entry.data.get(
                        CONF_CREATE_SUMMER_ENTITIES, DEFAULT_CREATE_SUMMER_ENTITIES
                    ),
                ): cv.boolean,
                vol.Required(
                    CONF_CREATE_WEATHER_ENTITY,
                    default=self.config_entry.data.get(
                        CONF_CREATE_WEATHER_ENTITY, DEFAULT_CREATE_WEATHER_ENTITY
                    ),
                ): cv.boolean,
                vol.Required(
                    CONF_CREATE_WEBCAM_ENTITIES,
                    default=self.config_entry.data.get(
                        CONF_CREATE_WEBCAM_ENTITIES, DEFAULT_CREATE_WEBCAM_ENTITIES
                    ),
                ): cv.boolean,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
