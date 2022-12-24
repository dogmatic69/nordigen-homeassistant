"""Nordigen Platform integration."""
import asyncio
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .ng import get_client, get_requisitions

NAME = "Nordigen HomeAssistant"
ISSUE_URL = "https://github.com/dogmatic69/nordigen-homeassistant/issues"
DOMAIN = "nordigen"
PLATFORMS = ["sensor"]

with open("VERSION", "r") as buf:
    VERSION = buf.read()

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

const = {
    "DOMAIN": DOMAIN,
    "DOMAIN_DATA": f"{DOMAIN}_data",
    "SECRET_ID": "secret_id",
    "SECRET_KEY": "secret_key",
    "DEBUG": "debug",
    "ENDUSER_ID": "enduser_id",
    "INSTITUTION_ID": "institution_id",
    "BALANCE_TYPES": "balance_types",
    "ACCOUNT_HOLDER": "account_holder",
    "REQUISITION_STATUS": "requisition_status",
    "TRANSACTIONS": "transactions",
    "REQUISITIONS": "requisitions",
    "HISTORICAL_DAYS": "max_historical_days",
    "REFRESH_RATE": "refresh_rate",
    "IGNORE_ACCOUNTS": "ignore_accounts",
    "COUNTRY_FIELD": "country",
    "COUNTRIES": ["SE", "GB"],
    "ICON_FIELD": "icon",
    "ICON": {
        "default": "mdi:cash-100",
        "auth": "mdi:two-factor-authentication",
        "sign": "mdi:currency-sign",
        "eur-off": "mdi:currency-eur-off",
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

CONFIG_SCHEMA = vol.Schema(
    {
        const["DOMAIN"]: vol.Schema(
            {
                vol.Required(const["SECRET_ID"]): cv.string,
                vol.Required(const["SECRET_KEY"]): cv.string,
                vol.Optional(const["DEBUG"], default=False): cv.string,
                vol.Required(const["REQUISITIONS"]): [
                    {
                        vol.Required(const["ENDUSER_ID"]): cv.string,
                        vol.Required(const["INSTITUTION_ID"]): cv.string,
                        vol.Optional(const["REFRESH_RATE"], default=240): cv.string,
                        vol.Optional(const["BALANCE_TYPES"], default=[]): [cv.string],
                        vol.Optional(const["HISTORICAL_DAYS"], default=30): cv.string,
                        vol.Optional(const["IGNORE_ACCOUNTS"], default=[]): [cv.string],
                        vol.Optional(const["ICON_FIELD"], default="mdi:cash-100"): cv.string,
                    },
                ],
            },
            extra=vol.ALLOW_EXTRA,
        )
    },
    extra=vol.ALLOW_EXTRA,
)


logger = logging.getLogger(__package__)


def get_config(configs, requisition):
    for config in configs:
        ref = f"{config['enduser_id']}-{config['institution_id']}"
        if requisition["reference"] == ref:
            return config


def setup(hass, config):
    domain_config = config.get(const["DOMAIN"])
    if domain_config is None:
        logger.warning("Nordigen not configured")
        return True

    logger.debug("config: %s", domain_config)
    client = get_client(secret_id=domain_config[const["SECRET_ID"]], secret_key=domain_config[const["SECRET_KEY"]])
    hass.data[const["DOMAIN"]] = {
        "client": client,
    }

    requisitions = get_requisitions(
        client=client,
        configs=domain_config[const["REQUISITIONS"]],
        logger=logger,
        const=const,
    )

    discovery = {
        "requisitions": requisitions,
    }

    for platform in PLATFORMS:
        hass.helpers.discovery.load_platform(platform, const["DOMAIN"], discovery, config)

    return True


async def async_setup(hass, config):
    return True


async def async_setup_entry(hass, entry):
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        logger.info(STARTUP_MESSAGE)

    # coordinator = BlueprintDataUpdateCoordinator(hass, client=client)
    # await coordinator.async_refresh()

    # if not coordinator.last_update_success:
    #     raise ConfigEntryNotReady

    # hass.data[DOMAIN][entry.entry_id] = coordinator

    # for platform in PLATFORMS:
    #     if entry.options.get(platform, True):
    #         coordinator.platforms.append(platform)
    #         hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, platform))

    # entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    # return True


async def async_unload_entry(hass, entry) -> bool:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass, entry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
