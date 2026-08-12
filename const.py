"""Constants for the Govee light local integration."""

from datetime import timedelta

DOMAIN = "govee_light_local"
MANUFACTURER = "Govee"

CONF_MULTICAST_ADDRESS_DEFAULT = "239.255.255.250"
CONF_TARGET_PORT_DEFAULT = 4001
CONF_LISTENING_PORT_DEFAULT = 4002
CONF_DISCOVERY_INTERVAL_DEFAULT = 60

SCAN_INTERVAL = timedelta(seconds=30)
DISCOVERY_TIMEOUT = 5

#custom
DISCOVERY_TYPE = "device discovery method"
SOURCE_IP = "source ip"
AUTOMATIC = "automatic (requires broadcast range)"
MANUAL = "manual setup"
FINGERPRINT = "fingerprint"
SKU = "sku"
DISCOVERED_DEVICES = "discovered_devices"
CONTROLLERS = "controllers"