import asyncio
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from init_db import reset, init_db
from main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


BASE_URL = "http://127.0.0.1:8000/api/v1"

# ---------------------------
# GLOBAL FIXTURE FOR TOKENS
# ---------------------------

@pytest.fixture(scope="session", autouse=True)
def auth_tokens(event_loop, client):
    """Authenticate users once and return their JWT tokens."""

    event_loop.run_until_complete(reset())
    event_loop.run_until_complete(init_db())
    users = {
        "admin": {"username": "admin", "password": "admin"},
        "manager": {"username": "ShopManager", "password": "ShManager"},
        "cashier": {"username": "Cashier", "password": "Cashier"},
    }

    tokens = {}
    for role, creds in users.items():
        response = client.post(BASE_URL + "/auth", json=creds)
        assert response.status_code == 200, f"Login failed for {role}"
        tokens[role] = f"Bearer {response.json()['token']}"

    return tokens


def auth_header(tokens, role: str):
    return {"Authorization": tokens[role]}

# ---------------------------
# RESET BALANCE TESTS
# ---------------------------

def test_reset_balance_as_admin_success(client, auth_tokens):
    resp = client.post(BASE_URL + "/balance/reset", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 205

def test_reset_balance_unauthenticated(client):
    resp = client.post(BASE_URL + "/balance/reset")
    assert resp.status_code == 401

def test_reset_balance_unauthorized(client, auth_tokens):
    resp = client.post(BASE_URL + "/balance/reset", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403

def test_internal_server_error_on_reset(client, auth_tokens):
    async def mock_return_false():
        return False

    with patch("app.controllers.balance_controller.BalanceRepository.reset_balance", side_effect=mock_return_false):
        resp = client.post(BASE_URL + "/balance/reset", headers=auth_header(auth_tokens, "admin"))
        assert resp.status_code == 500

# ---------------------------
# SET BALANCE TESTS
# ---------------------------

def test_set_balance_as_admin_success(client, auth_tokens):
    amount = 100
    resp = client.post(BASE_URL + "/balance/set?amount=" + str(amount), headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    assert resp.json() == {"success": True}

def test_set_balance_unauthorized(client, auth_tokens):
    amount = 100
    resp = client.post(BASE_URL + "/balance/set?amount=" + str(amount), headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403

def test_set_balance_unauthenticated(client):
    amount = 100
    resp = client.post(BASE_URL + "/balance/set?amount=" + str(amount))
    assert resp.status_code == 401

def test_set_balance_negative_amount(client, auth_tokens):
    amount = -50
    resp = client.post(BASE_URL + "/balance/set?amount=" + str(amount), headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 421

def test_set_balance_invalid_amount(client, auth_tokens):
    amount = "hello"
    resp = client.post(BASE_URL + "/balance/set?amount=" + amount, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code in (400, 422)

def test_internal_server_error_on_set(client, auth_tokens):
    async def mock_return_false(*args, **kwargs):
        return False

    with patch("app.controllers.balance_controller.BalanceRepository.set_balance", side_effect=mock_return_false):
        amount = 100
        resp = client.post(BASE_URL + "/balance/set?amount=" + str(amount), headers=auth_header(auth_tokens, "admin"))
        assert resp.status_code == 500

# ---------------------------
# GET BALANCE TESTS
# ---------------------------

def test_get_balance_as_admin_success(client, auth_tokens):
    resp = client.get(BASE_URL + "/balance", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 200

def test_get_balance_unauthenticated(client, auth_tokens):
    resp = client.get(BASE_URL + "/balance")
    assert resp.status_code == 401

def test_get_balance_unauthorized(client, auth_tokens):
    resp = client.get(BASE_URL + "/balance", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403
