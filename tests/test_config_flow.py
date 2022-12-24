"""Test nordigen config flow."""
import unittest
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from voluptuous.error import Invalid

from custom_components.nordigen.config_flow import NordigenConfigFlow, create_req, get_institutions, valid_country
from . import AsyncMagicMock


class TestHelpers(unittest.TestCase):
    def test_valid_country(self):
        assert valid_country("SE") == "SE"
        assert valid_country("se") == "SE"
        assert valid_country("sE") == "SE"

    def test_valid_country_not(self):
        with self.assertRaises(Invalid):
            valid_country("zz")

    def test_get_institutions(self):
        fn = MagicMock()
        fn.return_value = "test"
        assert get_institutions(fn, "SE")() == "test"

    def test_create_req(self):
        fn = MagicMock()
        fn.return_value = "test"
        assert create_req(fn, a=1, b=2)() == "test"


class TestConfigFlowGetRequisition:
    @unittest.mock.patch("custom_components.nordigen.config_flow.create_req")
    @pytest.mark.asyncio
    async def test_get_requisition_ex(self, mocked_create_req):
        """Requisition exists but is expired, rejected or similar."""
        mocked_hass = AsyncMagicMock()
        mocked_requisitions = AsyncMagicMock()

        inst = NordigenConfigFlow()
        inst.hass = mocked_hass

        inst.hass.async_add_executor_job.side_effect = [
            {
                "results": [
                    {"reference": "test-1", "status": "EX", "id": 321},
                    {"reference": "bob-smith-institute-123", "status": "EX", "id": 123},
                ]
            },
            None,
            {"reference": "bob-smith-institute-123", "status": "CR"},
        ]

        result = await inst.get_requisition(
            requisitions=mocked_requisitions, institution_id="institute-123", account_holder="bob-smith"
        )

        mocked_create_req.assert_called_once_with(
            mocked_requisitions.create,
            redirect="https://127.0.0.1",
            institution_id="institute-123",
            reference="bob-smith-institute-123",
        )

        assert inst.hass.async_add_executor_job.mock_calls == [
            call(mocked_requisitions.list),
            call(mocked_requisitions.remove, 123),
            call(mocked_create_req()),
        ]
        assert result == {"reference": "bob-smith-institute-123", "status": "CR"}

    @unittest.mock.patch("custom_components.nordigen.config_flow.create_req")
    @pytest.mark.asyncio
    async def test_get_requisition_cr(self, mocked_create_req):
        """Requisition exists and is valid."""
        mocked_hass = AsyncMagicMock()
        mocked_requisitions = AsyncMagicMock()

        inst = NordigenConfigFlow()
        inst.hass = mocked_hass

        inst.hass.async_add_executor_job.side_effect = [
            {
                "results": [
                    {"reference": "test-1", "status": "CR", "id": 321},
                    {"reference": "bob-smith-institute-333", "status": "CR", "id": 123},
                ]
            },
            None,
            {"reference": "no", "status": "CR"},
        ]

        result = await inst.get_requisition(
            requisitions=mocked_requisitions, institution_id="institute-333", account_holder="bob-smith"
        )

        mocked_create_req.assert_not_called()

        assert inst.hass.async_add_executor_job.mock_calls == [
            call(mocked_requisitions.list),
        ]
        assert result == {"reference": "bob-smith-institute-333", "status": "CR", "id": 123}

    @unittest.mock.patch("custom_components.nordigen.config_flow.create_req")
    @pytest.mark.asyncio
    async def test_get_requisition_none(self, mocked_create_req):
        """Requisition does not exist."""
        mocked_hass = AsyncMagicMock()
        mocked_requisitions = AsyncMagicMock()

        inst = NordigenConfigFlow()
        inst.hass = mocked_hass

        inst.hass.async_add_executor_job.side_effect = [
            {
                "results": [
                    {"reference": "test-1", "status": "CR", "id": 321},
                ]
            },
            {"reference": "bob-smith-institute-333", "status": "CR", "id": 123},
        ]

        result = await inst.get_requisition(
            requisitions=mocked_requisitions, institution_id="institute-333", account_holder="bob-smith"
        )

        mocked_create_req.assert_called_once_with(
            mocked_requisitions.create,
            redirect="https://127.0.0.1",
            institution_id="institute-333",
            reference="bob-smith-institute-333",
        )

        assert inst.hass.async_add_executor_job.mock_calls == [
            call(mocked_requisitions.list),
            call(mocked_create_req()),
        ]
        assert result == {"reference": "bob-smith-institute-333", "status": "CR", "id": 123}


class TestConfigFlow:
    @pytest.mark.asyncio
    async def test_init_initial(self):
        """Test init."""
        inst = NordigenConfigFlow()
        schema, user_input, errors = await inst.flow({})

        assert errors == {}
        assert user_input == {}
