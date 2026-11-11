"""Constants for the XCC integration."""

from datetime import timedelta

DOMAIN = "xcc"
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
DEFAULT_HOST = "http://192.168.0.122"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)
PLATFORMS = ["sensor", "binary_sensor"]
