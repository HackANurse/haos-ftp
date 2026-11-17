"""Config flow for the FTP integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from ftplib import all_errors
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_BACKUP_PATH,
    CONF_CA_FILE,
    CONF_CHARSET,
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_CLIENT_KEY_PASSWORD,
    CONF_COMPATIBILITY_MODE,
    CONF_DEFAULTS,
    CONF_NAME,
    CONF_PROTOCOL,
    CONF_TLS_VERSION,
    CONF_TLS_SERVER_NAME,
    CONF_TRANSFER_MODE,
    DOMAIN,
)
from .helpers import CertificateConfigurationError, FtpClient

_LOGGER = logging.getLogger(__name__)


class BaseFtpConfigFlow:
    async def async_check_user_input(self, user_input: Mapping[str, Any] | None) -> bool:
        """Check FTP connection with user input"""
        # Check if we can connect to the FTP server
        client = FtpClient(
            hass=self.hass,
            host=user_input[CONF_HOST],
            port=user_input[CONF_PORT],
            username=user_input.get(CONF_USERNAME, ""),
            password=user_input.get(CONF_PASSWORD, ""),
            protocol=user_input.get(CONF_PROTOCOL, "explicit_optional"),
            transfer_mode=user_input.get(CONF_TRANSFER_MODE, "passive"),
            charset=user_input.get(CONF_CHARSET, "utf-8"),
            compatibility_mode=user_input.get(CONF_COMPATIBILITY_MODE, False),
            tls_version=user_input.get(CONF_TLS_VERSION, "1.2"),
            tls_server_name=user_input.get(CONF_TLS_SERVER_NAME, ""),
            ca_file=user_input.get(CONF_CA_FILE, ""),
            client_cert=user_input.get(CONF_CLIENT_CERT, ""),
            client_key=user_input.get(CONF_CLIENT_KEY, ""),
            client_key_password=user_input.get(CONF_CLIENT_KEY_PASSWORD, ""),
        )
        try:
            _LOGGER.info("Check FTP connection on %s", client)
            async with client.connect():
                pass
        except CertificateConfigurationError:
            _LOGGER.exception("Invalid certificate configuration")
            self._errors["base"] = "invalid_certificate"
            return False
        except all_errors:
            _LOGGER.exception("Connection error")
            self._errors["base"] = "cannot_connect"
            return False
        return True

    @staticmethod
    def _get_config_schema(defaults=None):
        """Get configuration schema"""
        defaults = {**CONF_DEFAULTS, **(defaults or {})}
        return vol.Schema(
            {
                vol.Required(CONF_HOST, default=defaults.get(CONF_HOST)): str,
                vol.Required(CONF_PORT, default=int(defaults.get(CONF_PORT))): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Optional(CONF_NAME, default=defaults.get(CONF_NAME, "")): str,
                vol.Optional(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): str,
                vol.Optional(CONF_PASSWORD): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.PASSWORD,
                    )
                ),
                vol.Required(CONF_BACKUP_PATH, default=defaults.get(CONF_BACKUP_PATH)): str,
                vol.Required(CONF_PROTOCOL, default=defaults.get(CONF_PROTOCOL)): vol.In(
                    ["plain", "explicit_optional", "explicit_required", "implicit"]
                ),
                vol.Required(CONF_TRANSFER_MODE, default=defaults.get(CONF_TRANSFER_MODE)): vol.In(
                    ["passive", "active"]
                ),
                vol.Required(CONF_CHARSET, default=defaults.get(CONF_CHARSET)): vol.In(
                    ["utf-8", "latin-1", "cp1252"]
                ),
                vol.Required(
                    CONF_COMPATIBILITY_MODE,
                    default=defaults.get(CONF_COMPATIBILITY_MODE),
                ): bool,
                vol.Required(CONF_TLS_VERSION, default=defaults.get(CONF_TLS_VERSION)): vol.In(
                    ["1.2", "1.3"]
                ),
                vol.Optional(
                    CONF_TLS_SERVER_NAME, default=defaults.get(CONF_TLS_SERVER_NAME, "")
                ): str,
                vol.Optional(CONF_CA_FILE, default=defaults.get(CONF_CA_FILE, "")): str,
                vol.Optional(CONF_CLIENT_CERT, default=defaults.get(CONF_CLIENT_CERT, "")): str,
                vol.Optional(CONF_CLIENT_KEY, default=defaults.get(CONF_CLIENT_KEY, "")): str,
                vol.Optional(CONF_CLIENT_KEY_PASSWORD): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )


class FtpConfigFlow(BaseFtpConfigFlow, ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FTP."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        self._errors: dict[str, str] = {}
        if user_input is not None:
            # Check if we can connect to the FTP server
            if await self.async_check_user_input(user_input) and not self._errors:
                self._async_abort_entries_match(
                    {
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_USERNAME: user_input.get(CONF_USERNAME, ""),
                        CONF_BACKUP_PATH: user_input[CONF_BACKUP_PATH],
                        CONF_PROTOCOL: user_input[CONF_PROTOCOL],
                    }
                )

                return self.async_create_entry(
                    title=user_input.get(CONF_NAME)
                    or (
                        f"{user_input.get(CONF_USERNAME, '')}@{user_input[CONF_HOST]}:"
                        f"{user_input[CONF_PORT]}/"
                        f"{user_input[CONF_BACKUP_PATH].strip('/')}"
                    ),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=self._get_config_schema(), errors=self._errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return OptionsFlow()


class OptionsFlow(BaseFtpConfigFlow, OptionsFlow):
    """Handle a options flow for FTP."""

    @property
    def config_entry(self):
        return self.hass.config_entries.async_get_entry(self.handler)

    async def async_step_init(self, user_input: Mapping[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        self._errors: dict[str, str] = {}
        if user_input:
            user_input = dict(user_input)
            if not user_input.get(CONF_PASSWORD):
                _LOGGER.debug("User do not enter password, keep current configured one")
                user_input[CONF_PASSWORD] = self.config_entry.data.get(CONF_PASSWORD)
            if not user_input.get(CONF_CLIENT_KEY_PASSWORD):
                same_key = user_input.get(CONF_CLIENT_CERT, "") == self.config_entry.data.get(
                    CONF_CLIENT_CERT, ""
                ) and user_input.get(CONF_CLIENT_KEY, "") == self.config_entry.data.get(
                    CONF_CLIENT_KEY, ""
                )
                user_input[CONF_CLIENT_KEY_PASSWORD] = (
                    self.config_entry.data.get(CONF_CLIENT_KEY_PASSWORD, "") if same_key else ""
                )
            if await self.async_check_user_input(user_input) and not self._errors:
                # update config entry
                self.hass.config_entries.async_update_entry(self.config_entry, data=user_input)
                # Finish
                return self.async_create_entry(data=None)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_config_schema(self.config_entry.data),
            errors=self._errors,
        )
