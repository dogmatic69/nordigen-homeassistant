import logging

DOMAIN = "nordigen"
DOMAIN_DATA = "{}_data".format(DOMAIN)

DATA_CLIENT = "client"

CONF_TOKEN = "token"
CONF_ENDUSER_ID = "enduser_id"
CONF_ASPSP_ID = "aspsp_id"
CONF_AVAILABLE_BALANCE = "available_balance"
CONF_BOOKED_BALANCE = "booked_balance"
CONF_TRANSACTIONS = "transactions"
CONF_REQUISITIONS = "requisitions"
CONF_HISTORICAL_DAYS = "max_historical_days"
CONF_ICON = "icon"
CONF_REFRESH_RATE = "refresh_rate"
CONF_IGNORE_ACCOUNTS = "ignore_accounts"

LOGGER = logging.getLogger(__package__)

ICON = {
    "default": "mdi:currency-usd-circle",
    "GBP": "mdi:currency-gbp",
    "EUR": "mdi:currency-eur",
    "USD": "mdi:currency-usd",
}
