import unittest
from unittest.mock import AsyncMock, MagicMock, call

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.update_coordinator import UpdateFailed
import pytest

from custom_components.nordigen.sensor import (
    BalanceSensor,
    RequisitionSensor,
    async_setup_platform,
    balance_update,
    build_account_sensors,
    build_coordinator,
    build_requisition_sensor,
    build_sensors,
    random_balance,
    requisition_update,
)
from . import AsyncMagicMock

case = unittest.TestCase()

device_fixture = {
    "manufacturer": "Nordigen",
    "name": "N26 Bank",
    "identifiers": {("domain", "req-id")},
    "model": "v2",
    "configuration_url": "https://ob.nordigen.com/api/docs",
    "entry_type": DeviceEntryType.SERVICE,
}


class TestSensorRandom(unittest.TestCase):
    def test_basic(self):
        res = random_balance()
        self.assertTrue(res["balances"][0]["balanceAmount"]["amount"] > 0)


class TestBuildCoordinator(unittest.TestCase):
    def test_basic(self):
        hass = MagicMock()
        logger = MagicMock()
        updater = MagicMock()
        interval = MagicMock()

        res = build_coordinator(hass=hass, logger=logger, updater=updater, interval=interval, reference="ref")

        self.assertEqual(res.hass, hass)
        self.assertEqual(res.logger, logger)
        self.assertEqual(res.update_method, updater)
        self.assertEqual(res.update_interval, interval)
        self.assertEqual(res.name, "nordigen-balance-ref")

    def test_listners(self):
        hass = MagicMock()
        logger = MagicMock()
        updater = MagicMock()
        interval = MagicMock()

        res = build_coordinator(hass=hass, logger=logger, updater=updater, interval=interval, reference="ref")

        self.assertEqual({}, res._listeners)


class TestRequisitionUpdate:
    @pytest.mark.asyncio
    async def test_return(self):
        executor = AsyncMagicMock()
        executor.return_value = {"id": "req-id"}

        fn = MagicMock()
        logger = MagicMock()
        res = requisition_update(logger=logger, async_executor=executor, fn=fn, requisition_id="id")
        res = await res()

        case.assertEqual(
            res,
            {"id": "req-id"},
        )

    @pytest.mark.asyncio
    async def test_exception(self):
        executor = AsyncMagicMock()
        executor.side_effect = Exception("whoops")

        balance = MagicMock()
        logger = MagicMock()
        res = requisition_update(logger=logger, async_executor=executor, fn=balance, requisition_id="id")

        with case.assertRaises(UpdateFailed):
            await res()


class TestBalanceUpdate:
    @pytest.mark.asyncio
    async def test_return(self):
        executor = AsyncMagicMock()
        executor.return_value = {
            "balances": [
                {
                    "balanceAmount": {
                        "amount": 123,
                        "currency": "SEK",
                    },
                    "balanceType": "interimAvailable",
                    "creditLimitIncluded": True,
                },
                {
                    "balanceAmount": {
                        "amount": 321,
                        "currency": "SEK",
                    },
                    "balanceType": "interimBooked",
                },
            ]
        }

        fn = MagicMock()
        logger = MagicMock()
        res = balance_update(logger=logger, async_executor=executor, fn=fn, account_id="id")
        res = await res()

        case.assertEqual(
            res,
            {
                "closingBooked": None,
                "expected": None,
                "openingBooked": None,
                "forwardAvailable": None,
                "nonInvoiced": None,
                "interimAvailable": 123,
                "interimBooked": 321,
            },
        )

    @pytest.mark.asyncio
    async def test_exception(self):
        executor = AsyncMagicMock()
        executor.side_effect = Exception("whoops")

        balance = MagicMock()
        logger = MagicMock()
        res = balance_update(logger=logger, async_executor=executor, fn=balance, account_id="id")

        with case.assertRaises(UpdateFailed):
            await res()


class TestBuildSensors:
    @unittest.mock.patch("custom_components.nordigen.sensor.build_requisition_sensor")
    @unittest.mock.patch("custom_components.nordigen.sensor.build_account_sensors")
    @pytest.mark.asyncio
    async def test_build_sensors_unconfirmed(self, mocked_build_account_sensors, mocked_build_requisition_sensor):
        args = {
            "hass": "hass",
            "logger": "logger",
            "account": {"requires_auth": True},
            "const": "const",
            "debug": "debug",
        }
        await build_sensors(**args)
        args["requisition"] = args["account"]
        del args["account"]

        mocked_build_account_sensors.assert_not_called()
        mocked_build_requisition_sensor.assert_called_with(**args)


class TestBuildAccountSensors:
    def build_sensors_helper(self, account, const, debug=False):
        hass = MagicMock()
        logger = MagicMock()

        return dict(hass=hass, logger=logger, account=account, const=const, debug=debug, device="device-123")

    @unittest.mock.patch("custom_components.nordigen.sensor.random_balance")
    @unittest.mock.patch("custom_components.nordigen.sensor.build_coordinator")
    @unittest.mock.patch("custom_components.nordigen.sensor.balance_update")
    @pytest.mark.asyncio
    async def test_balance_debug(self, mocked_balance_update, mocked_build_coordinator, mocked_random_balance):
        account = {
            "config": {
                "refresh_rate": 1,
                "disable": False,
                "balance_types": [],
            },
            "id": "foobar-id",
            "iban": "iban",
            "bban": "bban",
            "unique_ref": "unique_ref",
            "name": "name",
            "owner": "owner",
            "currency": "currency",
            "product": "product",
            "status": "status",
            "bic": "bic",
            "requisition": {
                "id": "xyz-123",
                "details": {
                    "id": "req-id",
                    "name": "req-name",
                },
            },
        }
        const = {
            "REFRESH_RATE": "refresh_rate",
            "BALANCE_TYPES": "balance_types",
            "DOMAIN": "domain",
            "ICON": {"FOO": "foo"},
        }

        mocked_balance_coordinator = MagicMock()
        mocked_build_coordinator.return_value = mocked_balance_coordinator

        mocked_balance_coordinator.async_config_entry_first_refresh = AsyncMock()

        args = self.build_sensors_helper(account=account, const=const, debug=True)
        await build_account_sensors(**args)

        mocked_balance_update.assert_called_with(
            logger=args["logger"],
            async_executor=args["hass"].async_add_executor_job,
            fn=mocked_random_balance,
            account_id="foobar-id",
        )

    @unittest.mock.patch("custom_components.nordigen.sensor.build_coordinator")
    @unittest.mock.patch("custom_components.nordigen.sensor.balance_update")
    @pytest.mark.asyncio
    async def test_balance(self, mocked_balance_update, mocked_build_coordinator):
        account = {
            "config": {
                "refresh_rate": 1,
                "disable": False,
            },
            "id": "foobar-id",
            "iban": "iban",
            "bban": "bban",
            "unique_ref": "unique_ref",
            "name": "name",
            "owner": "owner",
            "currency": "currency",
            "product": "product",
            "status": "status",
            "bic": "bic",
            "requisition": {
                "id": "xyz-123",
                "details": {
                    "id": "req-id",
                    "name": "req-name",
                },
            },
        }
        const = {
            "DOMAIN": "domain",
            "REFRESH_RATE": "refresh_rate",
            "ICON": {"FOO": "foo"},
            "BALANCE_TYPES": "balance_types",
        }

        mocked_balance_coordinator = MagicMock()
        mocked_build_coordinator.return_value = mocked_balance_coordinator

        mocked_balance_coordinator.async_config_entry_first_refresh = AsyncMock()

        args = self.build_sensors_helper(account=account, const=const)
        await build_account_sensors(**args)

        mocked_balance_update.assert_called_with(
            logger=args["logger"],
            async_executor=args["hass"].async_add_executor_job,
            fn=args["hass"].data["domain"]["client"].account.balances,
            account_id="foobar-id",
        )

    @unittest.mock.patch("custom_components.nordigen.sensor.BalanceSensor")
    @unittest.mock.patch("custom_components.nordigen.sensor.random_balance")
    @unittest.mock.patch("custom_components.nordigen.sensor.build_coordinator")
    @unittest.mock.patch("custom_components.nordigen.sensor.timedelta")
    @unittest.mock.patch("custom_components.nordigen.sensor.balance_update")
    @pytest.mark.asyncio
    async def test_available_entities(
        self,
        mocked_balance_update,
        mocked_timedelta,
        mocked_build_coordinator,
        mocked_random_balance,
        mocked_nordigen_balance_sensor,
    ):
        account = {
            "config": {
                "refresh_rate": 1,
                "balance_types": ["interimAvailable"],
            },
            "id": "foobar-id",
        }
        const = {
            "ICON": {
                "FOO": "icon_foo",
            },
            "DOMAIN": "domain",
            "REFRESH_RATE": "refresh_rate",
            "BALANCE_TYPES": "balance_types",
        }

        mocked_balance_coordinator = MagicMock()
        mocked_build_coordinator.return_value = mocked_balance_coordinator

        mocked_balance_coordinator.async_config_entry_first_refresh = AsyncMock()

        args = self.build_sensors_helper(account=account, const=const)
        res = await build_account_sensors(**args)

        assert 1 == len(res)
        mocked_nordigen_balance_sensor.assert_called_with(
            **{
                "id": "foobar-id",
                "balance_type": "interimAvailable",
                "config": {"refresh_rate": 1, "balance_types": ["interimAvailable"]},
                "coordinator": mocked_balance_coordinator,
                "domain": "domain",
                "device": "device-123",
                "icons": {
                    "FOO": "icon_foo",
                },
            }
        )

    @unittest.mock.patch("custom_components.nordigen.sensor.BalanceSensor")
    @unittest.mock.patch("custom_components.nordigen.sensor.random_balance")
    @unittest.mock.patch("custom_components.nordigen.sensor.build_coordinator")
    @unittest.mock.patch("custom_components.nordigen.sensor.timedelta")
    @unittest.mock.patch("custom_components.nordigen.sensor.balance_update")
    @pytest.mark.asyncio
    async def test_booked_entities(
        self,
        mocked_balance_update,
        mocked_timedelta,
        mocked_build_coordinator,
        mocked_random_balance,
        mocked_nordigen_balance_sensor,
    ):
        account = {
            "id": "foobar-id",
            "config": {
                "refresh_rate": 1,
                "balance_types": ["interimBooked"],
            },
        }
        const = {
            "ICON": {},
            "DOMAIN": "domain",
            "REFRESH_RATE": "refresh_rate",
            "BALANCE_TYPES": "balance_types",
        }

        mocked_balance_coordinator = MagicMock()
        mocked_build_coordinator.return_value = mocked_balance_coordinator

        mocked_balance_coordinator.async_config_entry_first_refresh = AsyncMock()

        args = self.build_sensors_helper(account=account, const=const)
        res = await build_account_sensors(**args)

        assert 1 == len(res)
        mocked_nordigen_balance_sensor.assert_called_with(
            **{
                "id": "foobar-id",
                "balance_type": "interimBooked",
                "config": {"refresh_rate": 1, "balance_types": ["interimBooked"]},
                "coordinator": mocked_balance_coordinator,
                "domain": "domain",
                "device": "device-123",
                "icons": {},
            }
        )


class TestSensors(unittest.TestCase):
    data = {
        "coordinator": MagicMock(),
        "id": "account_id",
        "domain": "domain",
        "device": device_fixture,
        "balance_type": "interimWhatever",
        "iban": "iban",
        "bban": "bban",
        "unique_ref": "unique_ref",
        "name": "name",
        "owner": "owner",
        "currency": "currency",
        "product": "product",
        "status": "status",
        "bic": "bic",
        "requisition": {
            "id": "req-id",
            "enduser_id": "req-user-id",
            "reference": "req-ref",
            "details": {
                "id": "N29_NTSBDEB1",
                "name": "N29 Bank",
                "bic": "NTSBDEB1",
                "transaction_total_days": "730",
                "logo": "https://cdn.nordigen.com/ais/N26_NTSBDEB1.png",
            },
        },
        "config": "config",
        "icons": {
            "foobar": "something",
            "default": "something-else",
        },
    }

    def test_init(self):
        sensor = BalanceSensor(**self.data)
        for k in self.data:
            if k in ["coordinator"]:
                continue
            self.assertEqual(getattr(sensor, f"_{k}"), self.data[k])

    def test_device_info(self):
        sensor = BalanceSensor(**self.data)

        self.assertEqual(
            device_fixture,
            sensor.device_info,
        )

    def test_unique_id(self):
        sensor = BalanceSensor(**self.data)

        self.assertEqual("unique_ref-interim_whatever", sensor.unique_id)

    def test_balance_type(self):
        sensor = BalanceSensor(**self.data)

        self.assertEqual("interim_whatever", sensor.balance_type)

    def test_name_owner_and_name(self):
        sensor = BalanceSensor(**self.data)

        self.assertEqual("owner name (interim_whatever)", sensor.name)

    def test_name_no_owner_but_has_name(self):
        sensor = BalanceSensor(**{**self.data, "owner": None})

        self.assertEqual("name unique_ref (interim_whatever)", sensor.name)

    def test_name_no_owner_or_name(self):
        sensor = BalanceSensor(**{**self.data, "owner": None, "name": None})

        self.assertEqual("unique_ref (interim_whatever)", sensor.name)

    def test_state(self):
        ret = {"interimWhatever": "123.990"}
        self.data["coordinator"].data.__getitem__.side_effect = ret.__getitem__

        sensor = BalanceSensor(**self.data)

        self.assertEqual(123.99, sensor.state)

    def test_unused_balance_type_state(self):
        ret = {"interimWhatever": None}
        self.data["coordinator"].data.__getitem__.side_effect = ret.__getitem__

        sensor = BalanceSensor(**self.data)

        self.assertEqual(None, sensor.state)

    def test_unit_of_measurement(self):
        sensor = BalanceSensor(**self.data)

        self.assertEqual("currency", sensor.unit_of_measurement)

    def test_icon_default(self):
        sensor = BalanceSensor(**self.data)

        self.assertEqual("something-else", sensor.icon)

    def test_icon_custom(self):
        data = dict(self.data)
        data["currency"] = "foobar"
        sensor = BalanceSensor(**data)

        self.assertEqual("something", sensor.icon)

    def test_available_true(self):
        data = dict(self.data)
        data["status"] = "enabled"
        sensor = BalanceSensor(**data)

        self.assertEqual(True, sensor.available)

    @unittest.mock.patch("custom_components.nordigen.sensor.datetime")
    def test_state_attributes(self, mocked_datatime):
        mocked_datatime.now.return_value = "last_update"
        sensor = BalanceSensor(**self.data)

        self.assertEqual(
            {
                "balance_type": "interimWhatever",
                "iban": "iban",
                "unique_ref": "unique_ref",
                "name": "name",
                "owner": "owner",
                "product": "product",
                "status": "status",
                "bic": "bic",
                "reference": "req-ref",
                "last_update": "last_update",
            },
            sensor.state_attributes,
        )


class TestRequisitionSensor(unittest.TestCase):
    mocked_client = MagicMock()
    mocked_logger = MagicMock()
    data = {
        "domain": "domain",
        "coordinator": MagicMock(),
        "id": "req_id",
        "enduser_id": "enduser_id",
        "reference": "reference",
        "link": "link",
        "icons": {
            "auth": "something",
            "default": "something-else",
        },
        "config": "config",
        "client": mocked_client,
        "logger": mocked_logger,
        "ignored_accounts": ["ignore_accounts"],
        "const": {},
        "debug": "debug",
        "details": {
            "id": "N21_NTSBDEB1",
            "name": "N21 Bank",
        },
        "device": device_fixture,
    }

    def test_unconfirmed_device_info(self):
        sensor = RequisitionSensor(**self.data)
        self.assertEqual(
            device_fixture,
            sensor.device_info,
        )

    @unittest.mock.patch("custom_components.nordigen.sensor.get_accounts")
    def test_job(self, mocked_get_accounts):
        sensor = RequisitionSensor(**self.data)

        res = sensor.do_job(foo="bar", fizz="buzz")
        res()

        mocked_get_accounts.assert_called_with(foo="bar", fizz="buzz")

    def test_unique_id(self):
        sensor = RequisitionSensor(**self.data)

        self.assertEqual("reference", sensor.unique_id)

    def test_unconfirmed_name(self):
        sensor = RequisitionSensor(**self.data)

        self.assertEqual("reference", sensor.name)

    def test_state_on(self):
        mocked_coordinator = MagicMock()
        mocked_coordinator.data = {"status": "LN"}

        sensor = RequisitionSensor(**{**self.data, "coordinator": mocked_coordinator})

        self.assertEqual(True, sensor.state)

    def test_state_off(self):
        mocked_coordinator = MagicMock()
        mocked_coordinator.data = {"status": "Not LN"}

        sensor = RequisitionSensor(**{**self.data, "coordinator": mocked_coordinator})

        self.assertEqual(False, sensor.state)

    def test_unconfirmed_icon(self):
        sensor = RequisitionSensor(**self.data)

        self.assertEqual("something", sensor.icon)

    def test_unconfirmed_available_true(self):
        sensor = RequisitionSensor(**self.data)

        self.assertEqual(True, sensor.available)

    @unittest.mock.patch("custom_components.nordigen.sensor.datetime")
    def test_state_attributes_not_linked(self, mocked_datatime):
        mocked_datatime.now.return_value = "last_update"
        mocked_coordinator = MagicMock()
        mocked_coordinator.data = {"accounts": ["account-1", "account-2"], "status": "Foo"}
        sensor = RequisitionSensor(**{**self.data, "coordinator": mocked_coordinator})

        sensor.hass = MagicMock()

        self.assertEqual(
            {
                "link": "link",
                "info": (
                    "Authenticate to your bank with this link. This sensor will "
                    "monitor the requisition every few minutes and update once "
                    "authenticated. Once authenticated this sensor will be replaced "
                    "with the actual account sensor. If you will not authenticate "
                    "this service consider removing the config entry."
                ),
                "accounts": ["account-1", "account-2"],
                "last_update": "last_update",
                "status": "Foo",
            },
            sensor.state_attributes,
        )

    @unittest.mock.patch("custom_components.nordigen.sensor.build_account_sensors")
    @unittest.mock.patch("custom_components.nordigen.sensor.datetime")
    def test_unconfirmed_state_attributes_linked(self, mocked_datatime, mocked_build_account_sensors):
        mocked_datatime.now.return_value = "last_update"
        mocked_build_account_sensors.return_value = []
        mocked_coordinator = MagicMock()
        mocked_coordinator.data = {"accounts": ["account-1", "account-2"], "status": "LN"}
        sensor = RequisitionSensor(**{**self.data, "coordinator": mocked_coordinator})
        sensor.hass = MagicMock()
        sensor._setup_account_sensors = MagicMock()

        self.assertEqual(
            {
                "accounts": ["account-1", "account-2"],
                "last_update": "last_update",
                "status": "LN",
            },
            sensor.state_attributes,
        )


class TestAccountSensorSetup:
    mocked_client = AsyncMagicMock()
    mocked_logger = MagicMock()
    data = {
        "domain": "foobar",
        "coordinator": AsyncMagicMock(),
        "id": "account_id",
        "enduser_id": "enduser_id",
        "reference": "reference",
        "link": "link",
        "icons": {
            "auth": "something",
            "default": "something-else",
        },
        "config": "config",
        "client": mocked_client,
        "logger": mocked_logger,
        "ignored_accounts": ["ignore_accounts"],
        "const": {},
        "debug": "debug",
        "details": {
            "id": "N16_NTSBDEB1",
            "name": "N16 Bank",
        },
        "device": device_fixture,
    }

    @unittest.mock.patch("custom_components.nordigen.sensor.build_account_sensors")
    @unittest.mock.patch("custom_components.nordigen.sensor.datetime")
    @pytest.mark.asyncio
    async def test_setup_account_sensors_new(self, mocked_datatime, mocked_build_account_sensors):
        mocked_datatime.now.return_value = "last_update"
        mocked_build_account_sensors.return_value = [
            "account-sensor-1",
        ]
        mocked_coordinator = AsyncMagicMock()
        mocked_coordinator.data = {"accounts": ["account-1", "account-2"], "status": "LN"}
        sensor = RequisitionSensor(**{**self.data, "coordinator": mocked_coordinator})
        sensor.hass = AsyncMagicMock()
        sensor.platform = AsyncMagicMock()
        sensor._account_sensors = {"zzz": True}

        mocked_client = AsyncMagicMock()
        sensor.hass.async_add_executor_job.return_value = [
            {
                "balance_type": "whatever",
                "iban": "iban",
                "unique_ref": "unique_ref",
                "name": "name",
                "owner": "owner",
                "product": "product",
                "status": "status",
                "bic": "bic",
                "enduser_id": "req-user-id",
                "reference": "req-ref",
                "last_update": "last_update",
            }
        ]
        await sensor._setup_account_sensors(client=mocked_client, accounts=["account-1"], ignored=[])

        build_call = {
            "account": {
                "balance_type": "whatever",
                "iban": "iban",
                "unique_ref": "unique_ref",
                "name": "name",
                "owner": "owner",
                "product": "product",
                "status": "status",
                "bic": "bic",
                "enduser_id": "req-user-id",
                "reference": "req-ref",
                "last_update": "last_update",
                "config": "config",
                "requisition": {
                    "details": {"id": "N16_NTSBDEB1", "name": "N16 Bank"},
                    "id": "account_id",
                    "reference": "reference",
                },
            },
            "const": {},
            "debug": "debug",
            "hass": sensor.hass,
            "logger": self.mocked_logger,
            "device": device_fixture,
        }
        mocked_build_account_sensors.assert_called_once_with(**build_call)
        sensor.platform.async_add_entities.assert_called_once_with(["account-sensor-1"])

    @unittest.mock.patch("custom_components.nordigen.sensor.get_accounts")
    @unittest.mock.patch("custom_components.nordigen.sensor.build_account_sensors")
    @unittest.mock.patch("custom_components.nordigen.sensor.datetime")
    @pytest.mark.asyncio
    async def test_setup_account_sensors_existing(
        self, mocked_datatime, mocked_build_account_sensors, mocked_get_accounts
    ):
        mocked_datatime.now.return_value = "last_update"
        mocked_build_account_sensors.return_value = [
            "account-sensor-1",
        ]
        mocked_coordinator = AsyncMagicMock()
        mocked_coordinator.data = {"accounts": ["account-1", "account-2"], "status": "LN"}
        sensor = RequisitionSensor(**{**self.data, "coordinator": mocked_coordinator})
        sensor.hass = AsyncMagicMock()
        sensor.platform = AsyncMagicMock()

        sensor._account_sensors = {"zzz": True}

        sensor.hass.async_add_executor_job.return_value = [
            {
                "balance_type": "whatever",
                "iban": "iban",
                "unique_ref": "zzz",
                "name": "name",
                "owner": "owner",
                "product": "product",
                "status": "status",
                "bic": "bic",
                "enduser_id": "req-user-id",
                "reference": "req-ref",
                "last_update": "last_update",
            }
        ]
        mocked_client = AsyncMagicMock()
        await sensor._setup_account_sensors(client=mocked_client, accounts=["account-1"], ignored=[])

        mocked_build_account_sensors.assert_not_called()
        sensor.platform.async_add_entities.assert_not_called()


class TestBuildUnconfirmedSensor:
    @unittest.mock.patch("custom_components.nordigen.sensor.timedelta")
    @unittest.mock.patch("custom_components.nordigen.sensor.build_coordinator")
    @pytest.mark.asyncio
    async def test_build_requisition_sensor(self, mocked_build_coordinator, mocked_timedelta):
        hass = MagicMock()
        logger = MagicMock()
        requisition = {
            "id": "req-id",
            "enduser_id": "user-123",
            "reference": "ref-123",
            "link": "https://whatever.com",
            "config": {
                "ignore_accounts": [],
            },
            "details": {
                "id": "N25_NTSBDEB1",
                "name": "N25 Bank",
            },
        }

        const = {
            "DOMAIN": "foo",
            "ICON": {},
            "IGNORE_ACCOUNTS": "ignore_accounts",
        }

        mocked_coordinator = MagicMock()
        mocked_coordinator.async_config_entry_first_refresh = AsyncMagicMock()
        mocked_build_coordinator.return_value = mocked_coordinator

        sensors = await build_requisition_sensor(hass, logger, requisition, const, False)

        case.assertEqual(1, len(sensors))

        sensor = sensors[0]
        assert isinstance(sensor, RequisitionSensor)
        assert sensor.name == "ref-123"

        mocked_timedelta.assert_called_with(seconds=15)


class TestAsyncSetupPlatform:
    @unittest.mock.patch("custom_components.nordigen.sensor.logger")
    @pytest.mark.asyncio
    async def test_no_discovery_info(self, mocked_logger):
        await async_setup_platform(hass=None, config=None, add_entities=None, discovery_info=None)
        mocked_logger.info.assert_not_called()

    @unittest.mock.patch("custom_components.nordigen.sensor.logger")
    @pytest.mark.asyncio
    async def test_no_requisitions(self, mocked_logger):
        result = await async_setup_platform(
            hass=None,
            config=None,
            add_entities=None,
            discovery_info={
                "requisitions": [],
            },
        )

        mocked_logger.info.assert_called_with("Nordigen will attempt to configure [%s] requisitions", 0)
        mocked_logger.debug.assert_not_called()

        assert result is False

    @unittest.mock.patch("custom_components.nordigen.sensor.build_requisition_sensor")
    @unittest.mock.patch("custom_components.nordigen.sensor.logger")
    @pytest.mark.asyncio
    async def test_basic(self, mocked_logger, mocked_build):
        add_mock = MagicMock()

        mocked_build.return_value = ["req"]
        await async_setup_platform(
            hass="hass",
            config={"debug": "debug-123"},
            add_entities=add_mock,
            discovery_info={
                "requisitions": [
                    "req-1",
                    "req-2",
                ],
            },
        )

        mocked_logger.info.assert_has_calls(
            [
                call("Nordigen will attempt to configure [%s] requisitions", 2),
                call("Total of [%s] Nordigen account sensors configured", 2),
            ],
        )

        add_mock.assert_called_once_with(["req", "req"])
