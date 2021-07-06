"""Nordigen Platform integration."""
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from nordigen_lib import config_schema, entry

DOMAIN = "nordigen"
CONST = {
    "DOMAIN": DOMAIN,
    "DOMAIN_DATA": "{}_data".format(DOMAIN),
    "TOKEN": "token",
    "DEBUG": "debug",
    "ENDUSER_ID": "enduser_id",
    "ASPSP_ID": "aspsp_id",
    "AVAILABLE_BALANCE": "available_balance",
    "BOOKED_BALANCE": "booked_balance",
    "TRANSACTIONS": "transactions",
    "REQUISITIONS": "requisitions",
    "HISTORICAL_DAYS": "max_historical_days",
    "REFRESH_RATE": "refresh_rate",
    "IGNORE_ACCOUNTS": "ignore_accounts",
    "ICON_FIELD": "icon",
    "ICON": {
        "default": "mdi:currency-usd-circle",
        "GBP": "mdi:currency-gbp",
        "EUR": "mdi:currency-eur",
        "USD": "mdi:currency-usd",
    },
}

CONFIG_SCHEMA = config_schema(
    vol,
    cv,
    CONST,
)

LOGGER = logging.getLogger(__package__)


def setup(hass, config):
    """Setup the Nordigen platform."""
    return entry(hass, config, CONST=CONST, LOGGER=LOGGER)
