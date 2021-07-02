"""Nordigen Platform integration."""

import requests
import voluptuous as vol

from voluptuous.error import Error
from homeassistant.helpers.service import verify_domain_control
from homeassistant.exceptions import ConfigEntryNotReady

import homeassistant.helpers.config_validation as cv

from nordigen import Client

from .const import (
    DOMAIN,
    CONF_ASPSP_ID,
    CONF_ENDUSER_ID,
    CONF_REQUISITIONS,
    CONF_REFRESH_RATE,
    CONF_TOKEN,
    CONF_ICON,
    CONF_HISTORICAL_DAYS,
    CONF_AVAILABLE_BALANCE,
    CONF_IGNORE_ACCOUNTS,
    CONF_BOOKED_BALANCE,
    DATA_CLIENT,
    LOGGER,
)

PLATFORMS = ["sensor"]
TOPIC_UPDATE = f"{DOMAIN}_data_update"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_TOKEN): cv.string,
                vol.Required(CONF_REQUISITIONS): [
                    {
                        vol.Required(CONF_ENDUSER_ID): cv.string,
                        vol.Required(CONF_ASPSP_ID): cv.string,
                        vol.Optional(CONF_REFRESH_RATE, default=240): cv.string,
                        vol.Optional(CONF_AVAILABLE_BALANCE, default=True): cv.string,
                        vol.Optional(CONF_BOOKED_BALANCE, default=True): cv.string,
                        vol.Optional(CONF_HISTORICAL_DAYS, default=30): cv.string,
                        vol.Optional(CONF_IGNORE_ACCOUNTS, default=[]): [cv.string],
                        vol.Optional(
                            CONF_ICON, default="mdi:currency-usd-circle"
                        ): cv.string,
                    },
                ],
            },
            extra=vol.ALLOW_EXTRA,
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def get_config(configs, requisition):
    """Get the associated config."""
    for config in configs:
        ref = "{}-{}".format(config["enduser_id"], config["aspsp_id"])
        if requisition["reference"] == ref:
            return config


def matched_requisition(ref, requisitions):
    """Get the requisition for current ref."""
    for req in requisitions:
        if req["reference"] == ref:
            return req


def get_reference(enduser_id, aspsp_id, *args, **kwargs):
    return "{}-{}".format(enduser_id, aspsp_id)


def create_requisition(create, enduser_id, reference):
    return create(
        **{
            "redirect": "http://127.0.0.1/",
            "reference": reference,
            "enduser_id": enduser_id,
            "agreements": [],  # not used as we are using default end-user agreement
        }
    )


def get_accounts(client, configs):
    """Get a list of the accounts."""
    accounts = []
    requisitions = []
    try:
        requisitions = client.requisitions.list()["results"]
    except (requests.exceptions.HTTPError, KeyError) as error:
        LOGGER.error("Unable to fetch Nordigen requisitions: %s", error)

    for config in configs:
        ref = get_reference(**config)
        requisition = matched_requisition(ref, requisitions)

        if not requisition:
            requisition = create_requisition(
                create=client.requisitions.create,
                enduser_id=config["enduser_id"],
                reference=ref,
            )
            LOGGER.debug("No requisition found, created :%s", requisition)

        if requisition.get("status") != "LN":
            init = client.requisitions.initiate(
                id=requisition["id"], aspsp_id=config[CONF_ASPSP_ID]
            )
            LOGGER.debug("Initiate connection and restart :%s", init)
            LOGGER.error("Accept connection and restart :%s", init["initiate"])
            continue

        LOGGER.debug("Handling requisition :%s", requisition["id"])
        for account_id in requisition.get("accounts", []):
            account = {}
            try:
                account = client.account.details(account_id)
                account = account.get("account", {})
            except requests.exceptions.HTTPError as error:
                LOGGER.error("Unable to fetch account details from Nordigen: %s", error)
                continue

            if account["iban"] in config[CONF_IGNORE_ACCOUNTS]:
                LOGGER.warn("Account ignored due to configuration :%s", account["iban"])
                continue

            account = {
                "account_id": account.get("resourceId"),
                "name": account.get("name"),
                "owner": account.get("ownerName"),
                "currency": account.get("currency"),
                "product": account.get("product"),
                "status": account.get("status"),
                "bic": account.get("bic"),
                "iban": account.get("iban"),
                "requisition": {
                    "id": requisition.get("id"),
                    "status": requisition.get("status"),
                    "reference": requisition.get("reference"),
                    "redirect": requisition.get("redirect"),
                    "enduser_id": requisition.get("enduser_id"),
                },
                "config": config,
            }
            LOGGER.debug(
                "Loaded account info for account # :%s", account.get("account_id")
            )

            accounts.append(account)
    return accounts


def setup(hass, config):
    """Setup Nordigen platform."""
    if config.get(DOMAIN) is None:
        LOGGER.debug("Nordigen not configured")
        return True

    LOGGER.debug("config: %s", config[DOMAIN])
    client = Client(token=config[DOMAIN][CONF_TOKEN])
    hass.data[DOMAIN] = {
        "client": client,
    }

    hass.data[DOMAIN] = {
        DATA_CLIENT: client,
    }

    accounts = get_accounts(client, config[DOMAIN][CONF_REQUISITIONS])
    discovery = {"accounts": accounts}
    for platform in PLATFORMS:
        hass.helpers.discovery.load_platform(platform, DOMAIN, discovery, config)

    return True
