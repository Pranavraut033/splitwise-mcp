"""Tests for SplitwiseClient."""

import pytest
from splitwise_mcp_server.client import SplitwiseClient
from splitwise_mcp_server.auth import OAuth2Handler


@pytest.fixture
def auth_handler():
    return OAuth2Handler(
        consumer_key="test_key",
        consumer_secret="test_secret",
        access_token="test_token",
    )


@pytest.fixture
def sw_client(auth_handler):
    return SplitwiseClient(auth_handler, cache_ttl=3600)


class TestValidateWriteResponse:
    def test_create_expense_with_errors_raises(self, sw_client):
        response_data = {
            "expenses": [],
            "errors": {"base": ["The shares don't add up to the total cost"]},
        }
        with pytest.raises(Exception, match="shares don't add up"):
            sw_client._validate_write_response(response_data)

    def test_create_expense_success_passes(self, sw_client):
        response_data = {
            "expenses": [{"id": 1, "cost": "25.00"}],
            "errors": {},
        }
        sw_client._validate_write_response(response_data)

    def test_delete_with_success_false_raises(self, sw_client):
        response_data = {"success": False}
        with pytest.raises(Exception, match="did not succeed"):
            sw_client._validate_write_response(response_data)

    def test_delete_with_success_true_passes(self, sw_client):
        response_data = {"success": True}
        sw_client._validate_write_response(response_data)

    def test_errors_as_list_raises(self, sw_client):
        response_data = {"errors": ["Invalid input"]}
        with pytest.raises(Exception, match="Invalid input"):
            sw_client._validate_write_response(response_data)

    def test_empty_errors_dict_passes(self, sw_client):
        response_data = {"errors": {}}
        sw_client._validate_write_response(response_data)

    def test_no_errors_key_passes(self, sw_client):
        response_data = {"id": 1, "cost": "25.00"}
        sw_client._validate_write_response(response_data)

    def test_errors_as_string_raises(self, sw_client):
        response_data = {"errors": "Something went wrong"}
        with pytest.raises(Exception, match="Something went wrong"):
            sw_client._validate_write_response(response_data)

    def test_errors_none_passes(self, sw_client):
        response_data = {"errors": None}
        sw_client._validate_write_response(response_data)
