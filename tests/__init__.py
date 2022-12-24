"""Tests for nordigen integration."""
from unittest.mock import MagicMock, Mock

from apiclient.request_strategies import BaseRequestStrategy
from nordigen import wrapper as Client


class AsyncMagicMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMagicMock, self).__call__(*args, **kwargs)


def test_client(
    request_strategy=Mock(spec=BaseRequestStrategy),
    secret_id="secret-id",
    secret_key="secret-key",
):
    return Client(request_strategy=request_strategy, secret_id=secret_id, secret_key=secret_key)
