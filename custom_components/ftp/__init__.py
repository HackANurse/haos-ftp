"""The FTP integration."""

from __future__ import annotations

import logging

from ftplib import all_errors
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_BACKUP_PATH,
    CONF_CHARSET,
    CONF_COMPATIBILITY_MODE,
    CONF_PROTOCOL,
    CONF_TLS_VERSION,
    CONF_TRANSFER_MODE,
    DATA_BACKUP_AGENT_LISTENERS,
    DOMAIN,
)
from .helpers import FtpClient, async_ensure_path_exists

type FtpConfigEntry = ConfigEntry[FtpClient]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: FtpConfigEntry) -> bool:
    """Set up FTP from a config entry."""
    client = FtpClient(
        hass=hass,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        username=entry.data.get(CONF_USERNAME, ""),
        password=entry.data.get(CONF_PASSWORD, ""),
        protocol=entry.data.get(CONF_PROTOCOL, "plain"),
        transfer_mode=entry.data.get(CONF_TRANSFER_MODE, "passive"),
        charset=entry.data.get(CONF_CHARSET, "utf-8"),
        compatibility_mode=entry.data.get(CONF_COMPATIBILITY_MODE, False),
        tls_version=entry.data.get(CONF_TLS_VERSION, "1.2"),
    )
    try:
        _LOGGER.info("Initialize FTP connection on %s", client)
        async with client.connect() as connection:
            # Ensure the backup directory exists
            path = entry.data.get(CONF_BACKUP_PATH, "/")
            if not await async_ensure_path_exists(connection, path):
                raise ConfigEntryNotReady(
                    translation_domain=DOMAIN,
                    translation_key="cannot_access_or_create_backup_path",
                )
    except all_errors as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
        ) from err

    entry.runtime_data = client

    async def async_update_options(hass: HomeAssistant, updated_entry: FtpConfigEntry) -> None:
        await hass.config_entries.async_reload(updated_entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    def async_notify_backup_listeners() -> None:
        for listener in hass.data.get(DATA_BACKUP_AGENT_LISTENERS, []):
            listener()

    entry.async_on_unload(entry.async_on_state_change(async_notify_backup_listeners))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FtpConfigEntry) -> bool:
    """Unload a FTP config entry."""
    return True
