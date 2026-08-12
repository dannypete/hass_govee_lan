"""The Govee Light local integration."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from errno import EADDRINUSE
from ipaddress import IPv4Address
import logging
from typing import Any, List

from govee_local_api import GoveeController
from govee_local_api.controller import LISTENING_PORT

from homeassistant.components import network
from homeassistant.const import Platform, CONF_IP_ADDRESS, EVENT_HOMEASSISTANT_STOP
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType

from .const import (
    AUTOMATIC,
    CONF_MULTICAST_ADDRESS_DEFAULT, 
    CONF_LISTENING_PORT_DEFAULT, 
    CONF_TARGET_PORT_DEFAULT, 
    CONTROLLERS,
    DISCOVERY_TIMEOUT, 
    DISCOVERY_TYPE,
    DOMAIN,
    FINGERPRINT,
    SOURCE_IP 
)
from .coordinator import GoveeLocalApiCoordinator, GoveeLocalConfigEntry

PLATFORMS: list[Platform] = [Platform.LIGHT]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    pass

    # 1. put empty dict about the gateway into hass.data[gateway.entry_id]


    # 2. create gateway (i think analogous to a GoveeController)

    # find correct outbound source_ip->controller->coordinator to use with the device
    source_ip = await network.async_get_source_ip(hass, entry.data[CONF_IP_ADDRESS])

    # hass.data.<DOMAIN>[CONTROLLERS][<source_ip>] -> controller
    controller = hass.data.setdefault(DOMAIN, {}).setdefault(CONTROLLERS, {}).get(source_ip, None)

    if controller is None:
        controller = GoveeController(
            loop=hass.loop,
            logger=_LOGGER,
            listening_address=source_ip,
            broadcast_address=CONF_MULTICAST_ADDRESS_DEFAULT,
            broadcast_port=CONF_TARGET_PORT_DEFAULT,
            listening_port=CONF_LISTENING_PORT_DEFAULT,
            discovery_enabled=False,
            discovery_interval=1,
            update_enabled=False
        )
        hass.data[DOMAIN][CONTROLLERS][source_ip] = controller
        
    # (3. register `on_unload` for EVENT_HOMEASSISSTANT_STOP that does [obj from step 2].shutdown)
    async def on_hass_stop(event: Event) -> None:
        await controller.cleanup()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, on_hass_stop)
    )

    # 4. work with the device in the Entry
    # entry details
    device_ip = entry.data[CONF_IP_ADDRESS]
    discovery_type = entry.data[DISCOVERY_TYPE]

    # TODO what happens if source_ip != entry_source_ip
    # entry_source_ip = entry.data[SOURCE_IP]

    coordinator = GoveeLocalApiCoordinator(hass=hass, config_entry=entry, controller=controller)

    try:
        await coordinator.start()
    except OSError as ex:
        if ex.errno == EADDRINUSE:
            _LOGGER.error("Port %s already in use", LISTENING_PORT)
            raise ConfigEntryNotReady from ex
        
        # else:
        _LOGGER.error("Start failed, errno: %d", ex.errno)
        return False
        

    await coordinator.async_config_entry_first_refresh()

    try:
        await look_for_device(controller=controller, device_ip=device_ip, discovery_type=discovery_type)
    except TimeoutError as ex:
        raise ConfigEntryNotReady from ex
    
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GoveeLocalConfigEntry) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_get_source_ips(
    hass: HomeAssistant,
) -> set[str]:
    """Get the source ips for Govee local."""
    source_ips = await network.async_get_enabled_source_ips(hass)
    return {
        str(source_ip) for source_ip in source_ips if isinstance(source_ip, IPv4Address)
    }


async def look_for_device(controller: GoveeController, discovery_type: str, device_ip: str = None) -> bool:

    if device_ip is None or discovery_type == AUTOMATIC:
        controller.set_discovery_enabled(True)

    try:
        _LOGGER.debug("Starting discovery")
        await controller.start()
    except OSError as ex:
        _LOGGER.error("Start failed, errno: %d", ex.errno)
        return False

    if device_ip is not None:
        controller.add_device_to_discovery_queue(device_ip)

    try:
        async with asyncio.timeout(delay=DISCOVERY_TIMEOUT):
            while not controller.devices:
                _LOGGER.debug("Looking for devices...")
                await asyncio.sleep(delay=1)
    except TimeoutError:
        _LOGGER.debug(f"No devices found.")
        raise
    finally:
        controller.set_discovery_enabled(False)

    return bool(controller.devices)
