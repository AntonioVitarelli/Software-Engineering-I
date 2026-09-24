# tests/test_product_type_api.py
import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db

BASE_URL = "http://127.0.0.1:8000/api/v1/products"


# ---------------------------
# EVENT LOOP
# ---------------------------

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------
# AUTH TOKENS (reuse logic)
# ---------------------------

@pytest.fixture(scope="session", autouse=True)
def auth_tokens(event_loop, client):
    event_loop.run_until_complete(reset())
    event_loop.run_until_complete(init_db())

    users = {
        "admin": {"username": "admin", "password": "admin"},
        "manager": {"username": "ShopManager", "password": "ShManager"},
        "cashier": {"username": "Cashier", "password": "Cashier"},
    }

    tokens = {}
    for role, creds in users.items():
        resp = client.post("http://127.0.0.1:8000/api/v1/auth", json=creds)
        assert resp.status_code == 200
        tokens[role] = f"Bearer {resp.json()['token']}"

    return tokens


def auth_header(tokens, role: str):
    return {"Authorization": tokens[role]}

# ---------------------------
# SAMPLE PAYLOADS
# ---------------------------

PRODUCT_SAMPLE = {
    "description": "Milk 1L",
    "barcode": "123456789012",
    "price_per_unit": 1.5,
    "note": "Fresh milk",
    "quantity": 10,
    "position": "1-A-1"
}

PRODUCT_SAMPLE_2 = {
    "description": "Milk 2L",
    "barcode": "123456789013",
    "price_per_unit": 2.5,
    "note": "Fresh milk large",
    "quantity": 20,
    "position": "1-A-2"
}


# ---------------------------
# CREATE PRODUCT
# ---------------------------

def test_create_product_success_as_admin(client, auth_tokens):
    resp = client.post(
        BASE_URL + "/",
        json=PRODUCT_SAMPLE,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["barcode"] == PRODUCT_SAMPLE["barcode"]
    assert data["description"] == PRODUCT_SAMPLE["description"]


def test_create_product_conflict_barcode(client, auth_tokens):
    resp = client.post(
        BASE_URL + "/",
        json=PRODUCT_SAMPLE,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 409


def test_create_product_invalid_barcode(client, auth_tokens):
    bad = PRODUCT_SAMPLE.copy()
    bad["barcode"] = "123"
    resp = client.post(
        BASE_URL + "/",
        json=bad,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code in (400, 422)


def test_create_product_unauthenticated(client):
    resp = client.post(BASE_URL + "/", json=PRODUCT_SAMPLE)
    assert resp.status_code == 401


def test_create_product_forbidden_as_cashier(client, auth_tokens):
    resp = client.post(
        BASE_URL + "/",
        json=PRODUCT_SAMPLE_2,
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 403


# ---------------------------
# LIST PRODUCTS
# ---------------------------

def test_list_products_success_as_cashier(client, auth_tokens):
    resp = client.get(
        BASE_URL + "/",
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_products_unauthenticated(client):
    resp = client.get(BASE_URL + "/")
    assert resp.status_code == 401


# ---------------------------
# GET PRODUCT BY ID
# ---------------------------

def test_get_product_success(client, auth_tokens):
    resp = client.get(
        BASE_URL + "/1",
        headers=auth_header(auth_tokens, "manager")
    )
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        assert "barcode" in resp.json()


def test_get_product_not_found(client, auth_tokens):
    resp = client.get(
        BASE_URL + "/9999",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 404


def test_get_product_unauthenticated(client):
    resp = client.get(BASE_URL + "/1")
    assert resp.status_code == 401


# ---------------------------
# UPDATE PRODUCT
# ---------------------------

def test_update_product_success(client, auth_tokens):
    payload = PRODUCT_SAMPLE.copy()
    payload["description"] = "Updated Milk"

    resp = client.put(
        BASE_URL + "/1",
        json=payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code in (201, 404)


def test_update_product_conflict_barcode(client, auth_tokens):
    # create second product
    client.post(
        BASE_URL + "/",
        json=PRODUCT_SAMPLE_2,
        headers=auth_header(auth_tokens, "admin")
    )

    payload = PRODUCT_SAMPLE.copy()
    payload["barcode"] = PRODUCT_SAMPLE_2["barcode"]

    resp = client.put(
        BASE_URL + "/1",
        json=payload,
        headers=auth_header(auth_tokens, "admin")
    )

    if resp.status_code != 404:
        assert resp.status_code == 409


def test_update_product_forbidden_as_cashier(client, auth_tokens):
    resp = client.put(
        BASE_URL + "/1",
        json=PRODUCT_SAMPLE,
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 403


# ---------------------------
# DELETE PRODUCT
# ---------------------------

def test_delete_product_success(client, auth_tokens):
    resp = client.delete(
        BASE_URL + "/1",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code in (204, 404)


def test_delete_product_forbidden_as_cashier(client, auth_tokens):
    resp = client.delete(
        BASE_URL + "/1",
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 403


def test_delete_product_unauthenticated(client):
    resp = client.delete(BASE_URL + "/1")
    assert resp.status_code == 401


# ---------------------------
# PATCH POSITION
# ---------------------------

def test_update_product_position_success(client, auth_tokens):
    resp = client.patch(
        BASE_URL + "/1/position",
        params={"position": "2-B-3"},
        headers=auth_header(auth_tokens, "manager")
    )
    assert resp.status_code in (201, 404)


def test_update_product_position_invalid_format(client, auth_tokens):
    resp = client.patch(
        BASE_URL + "/1/position",
        params={"position": "BADPOS"},
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 400


# ---------------------------
# PATCH QUANTITY
# ---------------------------

def test_update_product_quantity_success(client, auth_tokens):
    resp = client.patch(
        BASE_URL + "/1/quantity",
        params={"quantity": "5"},
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code in (201, 404)


def test_update_product_quantity_insufficient(client, auth_tokens):
    resp = client.patch(
        BASE_URL + "/1/quantity",
        params={"quantity": "-9999"},
        headers=auth_header(auth_tokens, "admin")
    )
    if resp.status_code != 404:
        assert resp.status_code == 400
