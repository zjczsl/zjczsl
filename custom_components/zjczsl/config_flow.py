"""Config flow for Navien Water Heater integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .navien_api import (
    NavienSmartControl,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,       
    }
)

class NavienConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NavienSmartTok."""

    def __init__(self):
        self.navien = None

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user and password for NavienSmartTok account."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            self.navien = NavienSmartControl(user_input['username'],user_input['password'])
            gateways = await self.navien.login()
        except Exception:  # pylint: disable=broad-except
            errors["base"] = "invalid_auth"
        else:
            title = 'navien_' + user_input['username']
            existing_entry = await self.async_set_unique_id(title)
            if not existing_entry:
                return self.async_create_entry(title=title, data=user_input)
            else:
                self.hass.config_entries.async_update_entry(existing_entry, data={"username":user_input["username"],"password":user_input["password"]})
                await self.hass.config_entries.async_reload(existing_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
