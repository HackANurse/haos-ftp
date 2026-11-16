"""Constants for the FTP integration."""

from collections.abc import Callable

from homeassistant.const import CONF_PORT
from homeassistant.util.hass_dict import HassKey

DOMAIN = "ftp"

DATA_BACKUP_AGENT_LISTENERS: HassKey[list[Callable[[], None]]] = HassKey(
    f"{DOMAIN}.backup_agent_listeners"
)

CONF_BACKUP_PATH = "backup_path"
CONF_NAME = "name"
CONF_PROTOCOL = "protocol"
CONF_TRANSFER_MODE = "transfer_mode"
CONF_CHARSET = "charset"
CONF_COMPATIBILITY_MODE = "compatibility_mode"
CONF_TLS_VERSION = "tls_version"

CONF_DEFAULTS = {
    CONF_PORT: 21,
    CONF_BACKUP_PATH: "/",
    CONF_PROTOCOL: "explicit_optional",
    CONF_TRANSFER_MODE: "passive",
    CONF_CHARSET: "utf-8",
    CONF_COMPATIBILITY_MODE: False,
    CONF_TLS_VERSION: "1.2",
}
