"""Test nordigen setup process."""
import unittest
from unittest.mock import MagicMock

from homeassistant.exceptions import ConfigEntryNotReady
from nordigen.client import AccountClient
from parameterized import parameterized
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

# from custom_components.nordigen import (
#     async_reload_entry,
#     async_setup_entry,
#     async_unload_entry,
# )
from custom_components.nordigen import DOMAIN, async_setup, const, get_client, get_config, setup as ha_setup
from custom_components.nordigen.ng import (
    get_account,
    get_accounts,
    get_or_create_requisition,
    get_reference,
    get_requisitions,
    matched_requisition,
    requests,
    unique_ref,
)

MOCK_CONFIG = {}


# async def test_setup_unload_and_reload_entry(hass, bypass_get_data):
#     # Create a mock entry so we don't have to go through config flow
#     config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")

#     assert await async_setup_entry(hass, config_entry)
#     assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
#     assert type(hass.data[DOMAIN][config_entry.entry_id]) == BlueprintDataUpdateCoordinator

#     # Reload the entry and assert that the data from above is still there
#     assert await async_reload_entry(hass, config_entry) is None
#     assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
#     assert type(hass.data[DOMAIN][config_entry.entry_id]) == BlueprintDataUpdateCoordinator

#     # Unload the entry and verify that the data has been removed
#     assert await async_unload_entry(hass, config_entry)
#     assert config_entry.entry_id not in hass.data[DOMAIN]


# async def test_setup_entry_exception(hass, error_on_get_data):
#     config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")

#     with pytest.raises(ConfigEntryNotReady):
#         assert await async_setup_entry(hass, config_entry)


class TestGetConfig(unittest.TestCase):
    def test_not_found(self):
        res = get_config([], {})

        self.assertEqual(None, res)

    def test_first(self):
        res = get_config(
            [
                {"enduser_id": "user1", "institution_id": "aspsp1"},
                {"enduser_id": "user2", "institution_id": "aspsp2"},
                {"enduser_id": "user3", "institution_id": "aspsp3"},
            ],
            {"reference": "user1-aspsp1"},
        )

        self.assertEqual({"enduser_id": "user1", "institution_id": "aspsp1"}, res)

    def test_last(self):
        res = get_config(
            [
                {"enduser_id": "user1", "institution_id": "aspsp1"},
                {"enduser_id": "user2", "institution_id": "aspsp2"},
                {"enduser_id": "user3", "institution_id": "aspsp3"},
            ],
            {"reference": "user3-aspsp3"},
        )

        self.assertEqual({"enduser_id": "user3", "institution_id": "aspsp3"}, res)


class TestGetClient(unittest.TestCase):
    def test_basic(self):
        res = get_client(
            **{
                "secret_id": "secret1",
                "secret_key": "secret2",
            }
        )

        self.assertIsInstance(res.account, AccountClient)


# class TestSetup(unittest.TestCase):
#     def test_not_installed(self):
#         ha_setup({}, {})


class TestEntry(unittest.TestCase):
    @unittest.mock.patch("custom_components.nordigen.logger")
    @unittest.mock.patch("custom_components.nordigen.ng.Client")
    def test_not_configured(self, mocked_client, mocked_logger):
        res = ha_setup(hass=None, config={})
        mocked_logger.warning.assert_called_with("Nordigen not configured")

        self.assertTrue(res)

    @unittest.mock.patch("custom_components.nordigen.logger")
    @unittest.mock.patch("custom_components.nordigen.get_requisitions")
    @unittest.mock.patch("custom_components.nordigen.get_client")
    def test_entry(self, mocked_get_client, mocked_get_requisitions, mocked_logger):
        hass = MagicMock()
        client = MagicMock()

        mocked_get_requisitions.return_value = ["requisition"]
        mocked_get_client.return_value = client

        config = {"nordigen": {"secret_id": "xxxx", "secret_key": "yyyy", "requisitions": "requisitions"}}

        res = ha_setup(hass=hass, config=config)

        mocked_get_client.assert_called_with(secret_id="xxxx", secret_key="yyyy")
        mocked_get_requisitions.assert_called_with(
            client=client,
            configs="requisitions",
            logger=mocked_logger,
            const=const,
        )
        hass.helpers.discovery.load_platform.assert_called_with(
            "sensor", "nordigen", {"requisitions": ["requisition"]}, config
        )

        self.assertTrue(res)


# class TestSetup(unittest.TestCase):
#     async def test_unload(self):
#         pass

#     async def test_reload(self):
#         pass


class TestAsyncSetup:
    @pytest.mark.asyncio
    async def test_basics(self):
        result = await async_setup(hass=None, config=None)
        assert result is True
