import unittest
from unittest.mock import MagicMock, patch

from custom_components.nordigen import setup as ha_setup
from custom_components.nordigen.ng import get_client


class TestIntegration(unittest.TestCase):
    @patch("custom_components.nordigen.get_client")
    def test_new_install(self, mocked_get_client):
        hass = MagicMock()

        config = {
            "nordigen": {
                "secret_id": "xxxx",
                "secret_key": "yyyy",
                "requisitions": [
                    {
                        "institution_id": "aspsp_123",
                        "enduser_id": "user_123",
                        "ignore": [],
                    }
                ],
            },
        }

        client = get_client(secret_id="xxxx", secret_key="xxxx")
        client.requisitions.get = MagicMock(
            side_effect=[
                {"results": []},  # call 1: first call has no requisitions
            ]
        )
        client.requisitions.post = MagicMock(
            side_effect=[
                {
                    "id": "req-123",
                    "status": "CR",
                    "link": "https://example.com/whoohooo",
                },  # call 2: initiate requisition
            ]
        )
        mocked_get_client.return_value = client

        with self.assertWarns(DeprecationWarning):
            ha_setup(hass=hass, config=config)

        client.requisitions.post.assert_called_once()
        client.requisitions.get.assert_called_once()

    @unittest.mock.patch("custom_components.nordigen.get_client")
    def test_existing_install(self, mocked_get_client):
        hass = MagicMock()

        clinet_instance = MagicMock()
        mocked_get_client.return_value = clinet_instance

        config = {
            "nordigen": {
                "secret_id": "xxxx",
                "secret_key": "yyyy",
                "requisitions": [
                    {
                        "institution_id": "aspsp_123",
                        "enduser_id": "user_123",
                        "ignore": [
                            "resourceId-123",
                        ],
                    },
                    {
                        "institution_id": "aspsp_321",
                        "enduser_id": "user_321",
                        "ignore": [],
                    },
                ],
            },
        }

        clinet_instance.requisitions.list.side_effect = [
            {
                "results": [
                    {
                        "id": "req-123",
                        "status": "LN",
                        "reference": "user_123-aspsp_123",
                        "accounts": [
                            "account-1",
                            "account-2",
                            "account-3",
                        ],
                    },
                    {
                        "id": "req-321",
                        "status": "LN",
                        "reference": "user_321-aspsp_321",
                        "accounts": [
                            "account-a",
                        ],
                    },
                ]
            },
        ]

        clinet_instance.account.details.side_effect = [
            {
                "account": {
                    "iban": "iban-123",
                }
            },
            {
                "account": {
                    "bban": "bban-123",
                }
            },
            {
                "account": {
                    "resourceId": "resourceId-123",
                }
            },
            {
                "account": {
                    "iban": "yee-haa",
                }
            },
        ]

        ha_setup(hass=hass, config=config)

        clinet_instance.requisitions.create.assert_not_called()
        clinet_instance.requisitions.initiate.assert_not_called()

        # TODO: some how assert sensors are loaded too
        # clinet_instance.account.details.assert_has_calls(
        #     [
        #         call("account-1"),
        #         call("account-2"),
        #         call("account-3"),
        #         call("account-a"),
        #     ]
        # )

        details_fixture = {
            "id": "N26_NTSBDEB1",
            "name": "N26 Bank",
            "bic": "NTSBDEB1",
            "transaction_total_days": "730",
            "logo": "https://cdn.nordigen.com/ais/N26_NTSBDEB1.png",
        }
        hass.helpers.discovery.load_platform.assert_called_once_with(
            "sensor",
            "nordigen",
            {
                "requisitions": [
                    {
                        "config": {
                            "enduser_id": "user_123",
                            "ignore": ["resourceId-123"],
                            "institution_id": "aspsp_123",
                        },
                        "accounts": [
                            "account-1",
                            "account-2",
                            "account-3",
                        ],
                        "details": details_fixture,
                        "id": "req-123",
                        "reference": "user_123-aspsp_123",
                        "status": "LN",
                    },
                    {
                        "config": {
                            "enduser_id": "user_321",
                            "ignore": [],
                            "institution_id": "aspsp_321",
                        },
                        "accounts": ["account-a"],
                        "details": details_fixture,
                        "id": "req-321",
                        "reference": "user_321-aspsp_321",
                        "status": "LN",
                    },
                ],
            },
            {
                "nordigen": {
                    "requisitions": [
                        {"institution_id": "aspsp_123", "enduser_id": "user_123", "ignore": ["resourceId-123"]},
                        {"institution_id": "aspsp_321", "enduser_id": "user_321", "ignore": []},
                    ],
                    "secret_id": "xxxx",
                    "secret_key": "yyyy",
                }
            },
        )
