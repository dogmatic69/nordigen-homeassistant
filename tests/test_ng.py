import unittest
from unittest.mock import MagicMock

from parameterized import parameterized

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

details_fixture = {
    "id": "N26_NTSBDEB1",
    "name": "N26 Bank",
    "bic": "NTSBDEB1",
    "transaction_total_days": "730",
    "logo": "https://cdn.nordigen.com/ais/N26_NTSBDEB1.png",
}


class TestReference(unittest.TestCase):
    def test_basic(self):
        res = get_reference("user1", "aspsp1")
        self.assertEqual("user1-aspsp1", res)

    @parameterized.expand(
        [
            ({"iban": "iban-123"}, "iban-123"),
            ({"bban": "bban-123"}, "bban-123"),
            ({"resourceId": "resourceId-123"}, "resourceId-123"),
            ({"iban": "iban-123", "bban": "bban-123"}, "iban-123"),
            ({}, "id-123"),
        ]
    )
    def test_unique_ref(self, data, expected):
        res = unique_ref("id-123", data)
        self.assertEqual(expected, res)


class TestGetAccount(unittest.TestCase):
    def test_request_error(self):
        fn = MagicMock()

        fn.side_effect = requests.exceptions.HTTPError
        res = get_account(fn, "id", {}, logger=MagicMock())
        self.assertEqual(None, res)

    def test_debug_strange_accounts(self):
        fn = MagicMock()
        logger = MagicMock()
        fn.return_value = {"account": {}}
        get_account(fn=fn, id="id", requisition={}, logger=logger)

        logger.warn.assert_called_with("No iban: %s | %s", {}, {})

    def test_normal(self):
        fn = MagicMock()
        logger = MagicMock()
        fn.return_value = {"account": {"iban": 321}}
        res = get_account(fn=fn, id="id", requisition={"id": "req-id"}, logger=logger)

        self.assertEqual(321, res["iban"])


class TestRequisition(unittest.TestCase):
    def test_non_match(self):
        res = matched_requisition("ref", [])
        self.assertEqual({}, res)

    def test_first(self):
        res = matched_requisition(
            "ref",
            [
                {"reference": "ref"},
                {"reference": "fer"},
                {"reference": "erf"},
            ],
        )
        self.assertEqual({"reference": "ref"}, res)

    def test_last(self):
        res = matched_requisition(
            "erf",
            [
                {"reference": "ref"},
                {"reference": "fer"},
                {"reference": "erf"},
            ],
        )
        self.assertEqual({"reference": "erf"}, res)

    @unittest.mock.patch("custom_components.nordigen.ng.matched_requisition")
    def test_get_or_create_requisition_EX(self, mocked_matched_requisition):
        logger = MagicMock()
        fn_create = MagicMock()
        fn_remove = MagicMock()
        fn_info = MagicMock()
        mocked_matched_requisition.return_value = {
            "id": "req-id",
            "status": "EX",
        }

        fn_create.return_value = {
            "id": "foobar-id",
            "link": "https://example.com/whatever/1",
        }

        res = get_or_create_requisition(
            fn_create=fn_create,
            fn_remove=fn_remove,
            fn_info=fn_info,
            requisitions=[],
            reference="ref",
            institution_id="aspsp",
            logger=logger,
            config={},
        )

        fn_remove.assert_called_with(
            id="req-id",
        )

        fn_create.assert_called_with(
            redirect="https://127.0.0.1/",
            reference="ref",
            institution_id="aspsp",
        )

        self.assertEqual(
            {
                "id": "foobar-id",
                "link": "https://example.com/whatever/1",
                "config": {},
                "details": details_fixture,
            },
            res,
        )

    @unittest.mock.patch("custom_components.nordigen.ng.matched_requisition")
    def test_get_or_create_requisition_not_exist(self, mocked_matched_requisition):

        logger = MagicMock()
        fn_create = MagicMock()
        fn_remove = MagicMock()
        fn_info = MagicMock()
        mocked_matched_requisition.return_value = None

        fn_create.return_value = {
            "id": "foobar-id",
            "link": "https://example.com/whatever/2",
        }

        res = get_or_create_requisition(
            fn_create=fn_create,
            fn_remove=fn_remove,
            fn_info=fn_info,
            requisitions=[],
            reference="ref",
            institution_id="aspsp",
            logger=logger,
            config={},
        )

        fn_remove.assert_not_called()
        fn_create.assert_called_with(
            redirect="https://127.0.0.1/",
            reference="ref",
            institution_id="aspsp",
        )

        self.assertEqual(
            {
                "id": "foobar-id",
                "link": "https://example.com/whatever/2",
                "config": {},
                "details": details_fixture,
            },
            res,
        )

    @unittest.mock.patch("custom_components.nordigen.ng.matched_requisition")
    def test_get_or_create_requisition_not_linked(self, mocked_matched_requisition):

        logger = MagicMock()
        fn_create = MagicMock()
        fn_remove = MagicMock()
        fn_info = MagicMock()
        mocked_matched_requisition.return_value = {
            "id": "req-id",
            "status": "not-LN",
            "link": "https://example.com/whatever/3",
        }

        res = get_or_create_requisition(
            fn_create=fn_create,
            fn_remove=fn_remove,
            fn_info=fn_info,
            requisitions=[],
            reference="ref",
            institution_id="aspsp",
            logger=logger,
            config={},
        )

        fn_create.assert_not_called()
        fn_remove.assert_not_called()

        self.assertEqual(
            {
                "id": "req-id",
                "status": "not-LN",
                "link": "https://example.com/whatever/3",
                "config": {},
                "details": details_fixture,
            },
            res,
        )

    @unittest.mock.patch("custom_components.nordigen.ng.matched_requisition")
    def test_get_or_create_requisition_valid(self, mocked_matched_requisition):

        logger = MagicMock()
        fn_create = MagicMock()
        fn_remove = MagicMock()
        fn_info = MagicMock()
        mocked_matched_requisition.return_value = {
            "id": "req-id",
            "status": "LN",
        }

        res = get_or_create_requisition(
            fn_create=fn_create,
            fn_remove=fn_remove,
            fn_info=fn_info,
            requisitions=[],
            reference="ref",
            institution_id="aspsp",
            logger=logger,
            config={},
        )

        fn_create.assert_not_called()
        fn_remove.assert_not_called()

        self.assertEqual(
            {
                "id": "req-id",
                "status": "LN",
                "config": {},
                "details": details_fixture,
            },
            res,
        )


class TestGetAccounts(unittest.TestCase):
    def test_api_exception(self):
        client = MagicMock()
        logger = MagicMock()

        error = requests.exceptions.HTTPError()
        client.requisitions.list.side_effect = error

        res = get_requisitions(client=client, configs={}, logger=logger, const={})

        self.assertEqual([], res)
        logger.error.assert_called_with("Unable to fetch Nordigen requisitions: %s", error)

    def test_key_error(self):
        fn = MagicMock()
        client = MagicMock()
        logger = MagicMock()

        client.requisitions.list.return_value = {}

        res = get_accounts(fn=fn, requisition={}, logger=logger, ignored=[])

        self.assertEqual([], res)

    def test_ignored(self):
        fn = MagicMock()
        logger = MagicMock()

        get_accounts(fn=fn, requisition={"accounts": [123]}, logger=logger, ignored=[123])

        logger.info.assert_called_with("Account ignored due to configuration :%s", 123)

    @unittest.mock.patch("custom_components.nordigen.ng.get_account")
    def test_works(self, mocked_get_account):
        fn = MagicMock()

        logger = MagicMock()

        mocked_get_account.side_effect = [
            {"foobar": "account-1"},
            {"foobar": "account-2"},
            {"foobar": "account-3"},
        ]

        requisition = {
            "id": "req-1",
            "accounts": [1, 2],
            "config": {"ignore_accounts": []},
        }
        res = get_accounts(fn=fn, requisition=requisition, logger=logger, ignored=[])
        self.assertEqual(
            [
                {"foobar": "account-1"},
                {"foobar": "account-2"},
            ],
            res,
        )
