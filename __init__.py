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
        "auth": "mdi:two-factor-authentication",
        "sign": "mdi:currency-sign",
        "eur-off": "mdi:currency-eur-off",
        "usd-circle": "mdi:currency-usd-circle",
        "usd-circle-outline": "mdi:currency-usd-circle-outline",
        "usd-off": "mdi:currency-usd-off",
        "BDT": "mdi:currency-bdt",
        "BRL": "mdi:currency-brl",
        "BTC": "mdi:currency-btc",
        "CNY": "mdi:currency-cny",
        "ETH": "mdi:currency-eth",
        "EUR": "mdi:currency-eur",
        "GBP": "mdi:currency-gbp",
        "ILS": "mdi:currency-ils",
        "INR": "mdi:currency-inr",
        "JPY": "mdi:currency-jpy",
        "KRW": "mdi:currency-krw",
        "KZT": "mdi:currency-kzt",
        "NGN": "mdi:currency-ngn",
        "PHP": "mdi:currency-php",
        "RIAL": "mdi:currency-rial",
        "RUB": "mdi:currency-rub",
        "TRY": "mdi:currency-try",
        "TWD": "mdi:currency-twd",
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
