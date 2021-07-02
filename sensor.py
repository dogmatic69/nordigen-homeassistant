"""Platform for sensor integration."""
from datetime import timedelta, datetime
import random

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_REFRESH_RATE,
    DOMAIN,
    LOGGER,
    ICON,
    CONF_AVAILABLE_BALANCE,
    CONF_BOOKED_BALANCE,
)


def random_balance(a):
    """Generate random balances for testing."""
    return {
        "balances": [
            {
                "balanceAmount": {
                    "amount": random.randrange(0, 100000, 1) / 100,
                    "currency": "SEK",
                },
                "balanceType": "interimAvailable",
                "creditLimitIncluded": True,
            },
            {
                "balanceAmount": {
                    "amount": random.randrange(0, 100000, 1) / 100,
                    "currency": "SEK",
                },
                "balanceType": "interimBooked",
            },
        ]
    }


def data_updater(hass, balance, account_id):
    """Fetch latest information."""

    async def update():
        LOGGER.debug("Getting balance for account :%s", account_id)
        try:
            data = await hass.async_add_executor_job(random_balance, account_id)
            # data = await hass.async_add_executor_job(balance, account_id)
        except Exception as err:
            raise UpdateFailed(f"Error updating Nordigen sensors: {err}")

        return {
            balance["balanceType"]: balance["balanceAmount"]["amount"]
            for balance in data.get("balances")
        }

    return update


async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform via discovery only."""
    LOGGER.debug("setup_platform called in nordigen :%s", discovery_info)

    if discovery_info is None:
        return

    entities = []
    for account in discovery_info.get("accounts"):
        LOGGER.debug("sensor :%s", account)

        balanceCoordinator = DataUpdateCoordinator(
            hass,
            LOGGER,
            name="nordigen-balance-{}".format(account.get("iban")),
            update_method=data_updater(
                hass=hass,
                balance=hass.data[DOMAIN]["client"].account.balances,
                account_id=account.get("account_id"),
            ),
            update_interval=timedelta(
                minutes=int(account["config"][CONF_REFRESH_RATE])
            ),
        )

        await balanceCoordinator.async_config_entry_first_refresh()

        if account["config"][CONF_AVAILABLE_BALANCE] is not False:
            entities.append(
                NordigenBalanceSensor(
                    balances=hass.data[DOMAIN]["client"].account.balances,
                    balance_type="interimAvailable",
                    coordinator=balanceCoordinator,
                    **account,
                )
            )

        if account["config"][CONF_BOOKED_BALANCE] is not False:
            entities.append(
                NordigenBalanceSensor(
                    balances=hass.data[DOMAIN]["client"].account.balances,
                    balance_type="interimBooked",
                    coordinator=balanceCoordinator,
                    **account,
                )
            )

        if len(entities):
            add_entities(entities)


class NordigenBalanceSensor(CoordinatorEntity):
    """Nordigen"""

    def __init__(
        self,
        coordinator,
        balances,
        account_id,
        iban,
        name,
        owner,
        currency,
        product,
        status,
        bic,
        requisition,
        balance_type,
        config,
    ):
        """Initialize the sensor."""
        self._balances = balances
        self._balance_type = balance_type
        self._account_id = account_id
        self._iban = iban
        self._name = name
        self._owner = owner
        self._currency = currency
        self._product = product
        self._status = status
        self._bic = bic
        self._requisition = requisition
        self._config = config

        super().__init__(coordinator)

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._requisition["id"])},
            "name": "{} {}".format(self._bic, self.name),
        }

    @property
    def unique_id(self):
        """Return the ID of the sensor."""
        return "{}-{}".format(self._iban, self.balance_type)

    @property
    def balance_type(self):
        """Return the balance type of the sensor."""
        return self._balance_type.replace("interim", "").lower()

    @property
    def name(self):
        """Return the name of the sensor."""
        return "{} {}".format(self._iban, self.balance_type)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self._balance_type]

    @property
    def state_attributes(self):
        """Return State attributes."""
        return {
            "balance_type": self.balance_type,
            "iban": self._iban,
            "name": self._name,
            "owner": self._owner,
            "product": self._product,
            "status": self._status,
            "bic": self._bic,
            "enduser_id": self._requisition["enduser_id"],
            "reference": self._requisition["reference"],
            "last_update": datetime.now(),
        }

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._currency

    @property
    def icon(self):
        """Return the entity icon."""
        return ICON.get(self._currency, ICON.get("default"))

    @property
    def available(self) -> bool:
        """Return True when account is enabled."""
        return self._status == "enabled"
