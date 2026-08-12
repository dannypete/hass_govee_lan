"""Config flow for Govee light local."""

from __future__ import annotations

import asyncio
from contextlib import suppress
import logging
from typing import Any
import voluptuous as vol

from govee_local_api import GoveeController, GoveeDevice

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
)

from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_UNIQUE_ID
)

from . import async_get_source_ips, look_for_device
from .const import (
    AUTOMATIC,
    CONF_LISTENING_PORT_DEFAULT,
    CONF_MULTICAST_ADDRESS_DEFAULT,
    CONF_TARGET_PORT_DEFAULT,
    DISCOVERED_DEVICES,
    DISCOVERY_TIMEOUT,
    DISCOVERY_TYPE,
    DOMAIN,
    FINGERPRINT, 
    MANUAL,
    SKU,
    SOURCE_IP
)

_LOGGER = logging.getLogger(__name__)


class GoveeLightLocalConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION = 1

    def __init__(self) -> None:
        self.mode: str = None
        self.controller: GoveeController = None
        self.adapter_ip: str = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""

        errors = {}

        if user_input is not None:
            self.mode = user_input[DISCOVERY_TYPE]
            self.adapter_ip = user_input[SOURCE_IP]

            if user_input[DISCOVERY_TYPE] == AUTOMATIC:
                return await self.async_step_discovery()
            else: # MANUAL
                return await self.async_step_manual()
            

        data_schema = vol.Schema(
            {
                vol.Required(DISCOVERY_TYPE, default=AUTOMATIC): vol.In(
                    (
                        AUTOMATIC,
                        MANUAL
                    )
                ),
                vol.Required(SOURCE_IP): vol.In(
                    await async_get_source_ips(self.hass)
                )
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)


        # data_schema = vol.Schema(
        #     {
        #         vol.Required(DISCOVERY_TYPE, default=AUTOMATIC): vol.In(
        #             (
        #                 AUTOMATIC,
        #                 MANUAL
        #             )
        #         ),
        #         vol.Required(SOURCE_IP): vol.In(
        #             await async_get_source_ips(self.hass)
        #         )
        #     }
        # )
        #
        # if user_input is None:
        #     return self.async_show_form(step_id="user", data_schema=data_schema)
        #
        # self.mode = user_input[DISCOVERY_TYPE]
        # self.adapter_ip = user_input[SOURCE_IP]
        #
        # if user_input[DISCOVERY_TYPE] == AUTOMATIC:
        #     return await self.async_step_discovery()
        # return await self.async_step_manual()
            

    async def async_step_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle discovery method"""

        errors = {}

        if user_input is not None:
            self._cleanup_controller()
            self.controller: GoveeController = GoveeController(
                loop=self.hass.loop,
                logger=_LOGGER,
                listening_address=self.adapter_ip,
                broadcast_address=CONF_MULTICAST_ADDRESS_DEFAULT,
                broadcast_port=CONF_TARGET_PORT_DEFAULT,
                listening_port=CONF_LISTENING_PORT_DEFAULT,
                discovery_enabled=True,
                discovery_interval=1,
                update_enabled=False,
            )

            try:
              await look_for_device(controller=self.controller, discovery_type=self.mode)
            except TimeoutError:
              errors["base"] = "discovery_unsuccessful"
            except Exception as e:
              errors["base"] = f"other_error:{e.with_traceback}"
            else:
                return await self.async_step_choosedevice()
        
        data_schema = vol.Schema({})
        
        return self.async_show_form(step_id="discovery", data_schema=data_schema, errors=errors)


        # self.controller: GoveeController = GoveeController(
        #     loop=self.hass.loop,
        #     logger=_LOGGER,
        #     listening_address=self.adapter_ip,
        #     broadcast_address=CONF_MULTICAST_ADDRESS_DEFAULT,
        #     broadcast_port=CONF_TARGET_PORT_DEFAULT,
        #     listening_port=CONF_LISTENING_PORT_DEFAULT,
        #     discovery_enabled=True,
        #     discovery_interval=1,
        #     update_enabled=False,
        # )
        # 
        # errors = {}
        #
        # try:
        #     await look_for_device(controller=self.controller, discovery_type=self.mode)
        # except TimeoutError:
        #     errors["base"] = "discovery_unsuccessful"
        #     return self.async_show_form(step_id="user", errors=errors)
        #
        # return await self.async_step_choosedevice()
    

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle discovery method"""
        
        errors = {}

        if user_input is not None:
            self.controller: GoveeController = GoveeController(
                loop=self.hass.loop,
                logger=_LOGGER,
                listening_address=self.adapter_ip,
                broadcast_address=CONF_MULTICAST_ADDRESS_DEFAULT,
                broadcast_port=CONF_TARGET_PORT_DEFAULT,
                listening_port=CONF_LISTENING_PORT_DEFAULT,
                discovery_enabled=False,
                discovery_interval=1,
                update_enabled=False,
            )

            try:
                await look_for_device(self.controller, discovery_type=self.mode, device_ip=user_input[CONF_IP_ADDRESS])
            except TimeoutError:
                errors["base"] = "cannot_connect"
            else:
                 return await self.async_step_choosedevice()     
                
        data_schema = vol.Schema(
            {
                vol.Required(CONF_IP_ADDRESS): str
            }
        )

        return self.async_show_form(step_id="manual", data_schema=data_schema, errors=errors)

        # data_schema = vol.Schema(
        #     {
        #         vol.Required(CONF_IP_ADDRESS): str
        #     }
        # )

        # if user_input is None:
        #         return self.async_show_form(step_id="manual", data_schema=data_schema)

        # self.controller: GoveeController = GoveeController(
        #     loop=self.hass.loop,
        #     logger=_LOGGER,
        #     listening_address=self.adapter_ip,
        #     broadcast_address=CONF_MULTICAST_ADDRESS_DEFAULT,
        #     broadcast_port=CONF_TARGET_PORT_DEFAULT,
        #     listening_port=CONF_LISTENING_PORT_DEFAULT,
        #     discovery_enabled=False,
        #     discovery_interval=1,
        #     update_enabled=False,
        # )

        # errors = {}

        # try:
        #     await look_for_device(self.controller, discovery_type=self.mode, device_ip=user_input[CONF_IP_ADDRESS])
        # except TimeoutError:
        #     errors["base"] = "cannot_connect"
        #     return self.async_show_form(step_id="manual", data_schema=data_schema, errors=errors)

        # return await self.async_step_choosedevice()
    

    async def async_step_choosedevice(
        self, user_input: dict[str, Any] | None = None, 
    ) -> ConfigFlowResult:
        
        errors = {}

        def format_device(device: GoveeDevice):
            return f"<GoveeDevice ip={device.ip}, fingerprint={device.fingerprint}, sku={device.sku}, is_on={device._is_on}"
        
        device_mapping = {format_device(device): device for device in self.controller.devices}

        if user_input is not None:
        
            _LOGGER.debug("Found %s devices", len(self.controller.devices))

            device = device_mapping[user_input[DISCOVERED_DEVICES]]
            _LOGGER.debug("Chosen device is: %s", str(device))
            unique_id = str(f"{device.sku}@{device.ip}")
            existing_device = await self.async_set_unique_id(unique_id)

            if existing_device is not None:
                return self.async_abort(reason='already_configured')

            self._abort_if_unique_id_configured()
            entry = self.async_create_entry(
            title=unique_id,
            data={
                CONF_IP_ADDRESS: device.ip,
                CONF_UNIQUE_ID: unique_id,
                DISCOVERY_TYPE: self.mode,
                SKU: device.sku,
                FINGERPRINT: device.fingerprint,
                # SOURCE_IP: self.adapter_ip
                }
            ) 

            cleanup_complete: asyncio.Event = self.controller.cleanup()
            with suppress(TimeoutError):
                await asyncio.wait_for(cleanup_complete.wait(), 1)
            return entry
        
        
        data_schema = vol.Schema(
            {
                vol.Required(DISCOVERED_DEVICES): vol.In(
                    list(device_mapping.keys())
                )
            }
        )

        return self.async_show_form(step_id="choosedevice", data_schema=data_schema, errors=errors, last_step=True)

        # def format_device(device: GoveeDevice):
        #     return f"<GoveeDevice ip={device.ip}, fingerprint={device.fingerprint}, sku={device.sku}, is_on={device._is_on}"
        
        # device_mapping = {format_device(device): device for device in self.controller.devices}

        # data_schema = vol.Schema(
        #     {
        #         vol.Required(DISCOVERED_DEVICES): vol.In(
        #             list(device_mapping.keys())
        #         )
        #     }
        # )

        # if not user_input:
        #     return self.async_show_form(step_id="choosedevice", data_schema=data_schema, last_step=True)
        
        # _LOGGER.debug("Found %s devices", len(self.controller.devices))
    
        # device = device_mapping[user_input[DISCOVERED_DEVICES]]
        # _LOGGER.debug("Chosen device is: %s", str(device))
        # unique_id = str(f"{device.sku}@{device.ip}")
        # await self.async_set_unique_id(unique_id)
        # self._abort_if_unique_id_configured()
        
        # entry = self.async_create_entry(
        #     title=unique_id,
        #     data={
        #         CONF_IP_ADDRESS: device.ip,
        #         CONF_UNIQUE_ID: unique_id,
        #         DISCOVERY_TYPE: self.mode,
        #         SKU: device.sku,
        #         FINGERPRINT: device.fingerprint,
        #         # SOURCE_IP: self.adapter_ip
        #     }
        # ) 

        # cleanup_complete: asyncio.Event = self.controller.cleanup()
        # with suppress(TimeoutError):
        #     await asyncio.wait_for(cleanup_complete.wait(), 1)

        # return entry


    async def async_step_reconfigure(self, user_input: dict[str,Any] | None = None) -> ConfigFlowResult:
        # allow change of MODE or/and IP ADDRESS
        pass

    async def _cleanup_controller(self) -> None:
        if self.controller is not None:
            cleanup_complete = self.controller.cleanup()
            with suppress(TimeoutError):
                await asyncio.wait_for(cleanup_complete.wait(), 1)
            self.controller = None