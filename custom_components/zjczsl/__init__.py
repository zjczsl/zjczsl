"""The Navien NavienSmartTok Water Heater Integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from datetime import timedelta
import logging
from .navien_api import (
    NavienSmartControl,
    DeviceSorting
)

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed
)

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN

PLATFORMS: list[str] = ["water_heater","sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Navien NavienSmartTok Water Heater Integration from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    NavienSmartTok = NavienSmartControl(entry.data["username"],entry.data["password"])
    gateways = await NavienSmartTok.login()

    async def _update_method():
        """Get the latest data from Navien."""
        deviceStates = {}
        try:
            for gateway in gateways:
                channelInfo = await NavienSmartTok.connect(gateway["GID"])
                deviceStates[gateway["GID"]] = {}
                deviceStates[gateway["GID"]]["channelInfo"] = channelInfo
                for channelNum in range(1,4):
                    if channelInfo["channel"][str(channelNum)]["deviceSorting"] > 0:
                        for deviceNum in range(1,channelInfo["channel"][str(channelNum)]["deviceCount"] + 1):
                            state = await NavienSmartTok.sendStateRequest(gateway["GID"], channelNum, deviceNum)
                            state = NavienSmartTok.convertState(state,channelInfo["channel"][str(channelNum)]["deviceTempFlag"])
                            deviceStates[gateway["GID"]]["state"] = {}
                            deviceStates[gateway["GID"]]["state"][str(channelNum)] = {}
                            deviceStates[gateway["GID"]]["state"][str(channelNum)][str(deviceNum)] = state
            await NavienSmartTok.disconnect()
        except:
            raise UpdateFailed
        return deviceStates

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_update_method,
        update_interval=timedelta(seconds=30),
    )
    
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

