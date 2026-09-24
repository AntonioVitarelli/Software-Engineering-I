import asyncio

import pytest
from fastapi.testclient import TestClient

from init_db import init_db, reset
from main import app


@pytest.fixture(scope="function")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c


BASE_URL = "http://127.0.0.1:8000/api/v1"

# ---------------------------
# GLOBAL FIXTURE FOR TOKENS
# ---------------------------


@pytest.fixture(scope="function", autouse=True)
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


@pytest.fixture(params=["admin", "cashier", "manager"])
def role(request):
    return request.param


@pytest.fixture
def customer_json(client, auth_tokens):
    card_resp = client.post(
        BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin")
    )
    assert card_resp.status_code == 201
    customer_resp = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_WITH_CARD_WITHOUT_POINTS,
        headers=auth_header(auth_tokens, "admin"),
    )
    return customer_resp.json()


@pytest.fixture
def cardless_customer_json(client, auth_tokens):
    customer_resp = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_NAME_ONLY,
        headers=auth_header(auth_tokens, "admin"),
    )
    return customer_resp.json()


@pytest.fixture
def card_01(client, auth_tokens):
    card_resp = client.post(
        BASE_URL + "/customers/cards",
        headers=auth_header(auth_tokens, "admin"),
    )
    return card_resp.json()


# ---------------------------
# SAMPLE PAYLOADS
# ---------------------------

CUSTOMER_SAMPLE_NAME_ONLY = {"name": "John"}

CUSTOMER_SAMPLE_NO_NAME = {"name": ""}

CUSTOMER_SAMPLE_EMPTY_BODY = {}

CUSTOMER_SAMPLE_WITH_ID = {
    "id": 100,
    "name": "John",
}

CUSTOMER_SAMPLE_WITH_CARD_WITHOUT_POINTS = {
    "name": "John",
    "card": {"card_id": "0000000001"},
}

CUSTOMER_SAMPLE_WITH_CARD_WITH_POINTS = {
    "name": "John",
    "card": {"card_id": "0000000001", "points": 100},
}

CUSTOMER_SAMPLE_WITH_INVALID_CARD_ID = {
    "name": "John",
    "card": {"card_id": "invalid"},
}

CUSTOMER_SAMPLE_WITH_NULL_CARD_ID = {
    "name": "John",
    "card": {"card_id": None},
}

# ---------------------------
# CREATE CARD TESTS
# ---------------------------


def test_create_loyalty_card(client, auth_tokens, role):
    resp = client.post(
        BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, role)
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["card_id"] == "0000000001"
    assert data["points"] == 0


def test_create_loyalty_card_unauthenticated_fail(client):
    resp = client.post(BASE_URL + "/customers/cards")
    assert resp.status_code == 401


# ---------------------------
# CREATE CUSTOMER TESTS
# ---------------------------


def test_create_customer_name_only(client, auth_tokens, role):
    resp = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_NAME_ONLY,
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == CUSTOMER_SAMPLE_NAME_ONLY["name"]
    assert data["card"] is None


def test_create_customer_name_only_unauthenticated_fail(client):
    resp = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_NAME_ONLY,
    )
    assert resp.status_code == 401


def test_create_customer_no_name_fail(client, auth_tokens, role):
    resp = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_NO_NAME,
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code in (400, 422)


def test_create_customer_empty_body_fail(client, auth_tokens, role):
    resp = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_EMPTY_BODY,
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code in (400, 422)


def test_create_customer_with_id(client, auth_tokens, role):
    resp = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_WITH_ID,
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == 1


def test_create_customer_with_card_without_points(client, auth_tokens, role):
    resp1 = client.post(
        BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, role)
    )
    assert resp1.status_code == 201
    resp2 = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_WITH_CARD_WITHOUT_POINTS,
        headers=auth_header(auth_tokens, role),
    )
    assert resp2.status_code == 201
    data = resp2.json()
    assert data["card"]["card_id"] == "0000000001"


def test_create_customer_with_card_with_points(client, auth_tokens, role):
    resp1 = client.post(
        BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, role)
    )
    assert resp1.status_code == 201
    resp2 = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_WITH_CARD_WITH_POINTS,
        headers=auth_header(auth_tokens, role),
    )
    assert resp2.status_code == 201
    data = resp2.json()
    assert data["card"]["card_id"] == "0000000001"
    assert data["card"]["points"] == 0


def test_create_customer_with_an_already_attached_card_fail(
    client, customer_json, auth_tokens, role
):
    customer_duplicate_card = {
        "name": "John",
        "card": {"card_id": customer_json["card"]["card_id"]},
    }
    resp = client.post(
        BASE_URL + "/customers",
        json=customer_duplicate_card,
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 409


def test_create_customer_with_nonexistent_card_fail(client, auth_tokens, role):
    resp = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_WITH_CARD_WITHOUT_POINTS,
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 404


def test_create_customer_with_invalid_card_id_fail(client, auth_tokens, role):
    resp = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_WITH_INVALID_CARD_ID,
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 400


# ---------------------------
# LIST ALL CUSTOMERS
# ---------------------------


def test_list_all_customers(client, auth_tokens, role):
    resp = client.get(BASE_URL + "/customers", headers=auth_header(auth_tokens, role))
    assert resp.status_code == 200


def test_list_all_customers_unauthenticated_fail(client):
    resp = client.get(BASE_URL + "/customers")
    assert resp.status_code == 401


def test_list_all_customers_after_creating_new_customer(client, auth_tokens, role):
    previous_length = len(
        client.get(
            BASE_URL + "/customers", headers=auth_header(auth_tokens, role)
        ).json()
    )
    client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_NAME_ONLY,
        headers=auth_header(auth_tokens, role),
    )
    post_length = len(
        client.get(
            BASE_URL + "/customers", headers=auth_header(auth_tokens, role)
        ).json()
    )
    assert post_length == previous_length + 1


def test_list_all_customers_after_deleting_customer(
    client, customer_json, auth_tokens, role
):
    previous_length = len(
        client.get(
            BASE_URL + "/customers", headers=auth_header(auth_tokens, role)
        ).json()
    )
    client.delete(
        BASE_URL + f"/customers/{customer_json['id']}",
        headers=auth_header(auth_tokens, role),
    )
    post_length = len(
        client.get(
            BASE_URL + "/customers", headers=auth_header(auth_tokens, role)
        ).json()
    )
    assert post_length == previous_length - 1


# ---------------------------
# GET A CUSTOMER BY ID
# ---------------------------


def test_get_a_customer_found(client, auth_tokens, role, customer_json):
    resp = client.get(
        BASE_URL + f"/customers/{customer_json['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 200


def test_get_a_customer_unauthenticated_fail(client, customer_json):
    resp = client.get(BASE_URL + f"/customers/{customer_json['id']}")
    assert resp.status_code == 401


def test_get_a_customer_invalid_id_fail(client, auth_tokens, customer_json, role):
    invalid_id = "invalid" + str(customer_json["id"])
    resp = client.get(
        BASE_URL + f"/customers/{invalid_id}",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 400


def test_get_a_customer_not_found_fail(client, auth_tokens, customer_json, role):
    resp = client.get(
        BASE_URL + f"/customers/{customer_json['id'] + 1}",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 404


# ----------------------------
# UPDATE AN EXISTING CUSTOMER
# ----------------------------


def test_update_customer_name_only(client, auth_tokens, role, customer_json):
    updated_json = CUSTOMER_SAMPLE_WITH_ID
    updated_json["name"] = "Jacob"
    updated_json["id"] = "1234"

    update_resp = client.put(
        BASE_URL + f"/customers/{customer_json['id']}",
        json=updated_json,
        headers=auth_header(auth_tokens, role),
    )
    assert update_resp.status_code == 201

    get_resp = client.get(
        BASE_URL + f"/customers/{customer_json['id']}",
        headers=auth_header(auth_tokens, role),
    )

    updated_customer_json = get_resp.json()
    assert updated_customer_json["id"] == customer_json["id"]
    assert updated_customer_json["name"] == "Jacob"
    assert updated_customer_json["card"]["card_id"] == customer_json["card"]["card_id"]


def test_update_customer_empty_name(client, auth_tokens, customer_json, role):
    update_resp = client.put(
        BASE_URL + f"/customers/{customer_json['id']}",
        json=CUSTOMER_SAMPLE_NO_NAME,
        headers=auth_header(auth_tokens, role),
    )
    assert update_resp.status_code == 400

    get_resp = client.get(
        BASE_URL + f"/customers/{customer_json['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert get_resp.json()["name"] == customer_json["name"]


def test_update_customer_unauthenticated(client, customer_json):
    update_resp = client.put(
        BASE_URL + f"/customers/{customer_json['id']}",
        json={"name": "Jacob"},
    )
    assert update_resp.status_code == 401


def test_update_customer_null_card(client, auth_tokens, customer_json, role):
    update_resp = client.put(
        BASE_URL + f"/customers/{customer_json['id']}",
        json=CUSTOMER_SAMPLE_WITH_NULL_CARD_ID,
        headers=auth_header(auth_tokens, role),
    )
    assert update_resp.status_code == 201

    get_customer_resp = client.get(
        BASE_URL + f"/customers/{customer_json['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert get_customer_resp.json()["card"] is None

    get_card_resp = client.patch(
        BASE_URL + f"/customers/cards/{customer_json['card']['card_id']}?points=30",
        headers=auth_header(auth_tokens, role),
    )
    assert get_card_resp.status_code == 404


def test_update_customer_not_found(client, auth_tokens, customer_json, role):
    update_resp = client.put(
        BASE_URL + f"/customers/{customer_json['id'] + 1}",
        json=CUSTOMER_SAMPLE_WITH_NULL_CARD_ID,
        headers=auth_header(auth_tokens, role),
    )
    assert update_resp.status_code == 404


def test_update_customer_card_not_found(client, auth_tokens, customer_json, role):
    customer_json["card"]["card_id"] = "1234567890"
    update_resp = client.put(
        BASE_URL + f"/customers/{customer_json['id'] + 1}",
        json=customer_json,
        headers=auth_header(auth_tokens, role),
    )
    assert update_resp.status_code == 404


def test_update_customer_card_already_attached(
    client, auth_tokens, customer_json, role
):
    second_customer = client.post(
        BASE_URL + "/customers",
        json=CUSTOMER_SAMPLE_NAME_ONLY,
        headers=auth_header(auth_tokens, role),
    )
    client.put(
        BASE_URL + f"/customers/{second_customer.json()['id']}",
        json={
            "card": {"card_id": customer_json["card"]["card_id"]},
        },
        headers=auth_header(auth_tokens, role),
    )


# ------------------
# DELETE A CUSTOMER
# ------------------


def test_delete_customer(client, auth_tokens, customer_json, role):
    delete_response = client.delete(
        BASE_URL + f"/customers/{customer_json['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_response.status_code == 204

    get_card_resp = client.patch(
        BASE_URL + f"/customers/cards/{customer_json['card']['card_id']}?points=30",
        headers=auth_header(auth_tokens, role),
    )
    assert get_card_resp.status_code == 404


def test_delete_customer_unauthenticated(client, customer_json):
    delete_response = client.delete(
        BASE_URL + f"/customers/{customer_json['id']}",
    )
    assert delete_response.status_code == 401


def test_delete_customer_not_found(client, auth_tokens, customer_json, role):
    delete_response = client.delete(
        BASE_URL + f"/customers/{customer_json['id'] + 1}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_response.status_code == 404


# ------------------
# ATTACH A CARD
# ------------------


def test_attach_card(client, auth_tokens, cardless_customer_json, card_01, role):
    attach_response = client.patch(
        BASE_URL
        + f"/customers/{cardless_customer_json['id']}/attach-card/{card_01['card_id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert attach_response.status_code == 201


def test_attach_card_unauthenticated(client, cardless_customer_json, card_01):
    attach_response = client.patch(
        BASE_URL
        + f"/customers/{cardless_customer_json['id']}/attach-card/{card_01['card_id']}",
    )
    assert attach_response.status_code == 401


def test_attach_card_invalid_id(client, auth_tokens, cardless_customer_json, role):
    attach_response = client.patch(
        BASE_URL
        + f"/customers/{cardless_customer_json['id']}/attach-card/1234invalid_id",
        headers=auth_header(auth_tokens, role),
    )
    assert attach_response.status_code == 400

    get_resp = client.get(
        BASE_URL + f"/customers/{cardless_customer_json['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert get_resp.json()["card"] is None


def test_attach_card_empty_id(client, auth_tokens, cardless_customer_json, role):
    attach_response = client.patch(
        BASE_URL + f'/customers/{cardless_customer_json["id"]}/attach-card/""',
        headers=auth_header(auth_tokens, role),
    )
    assert attach_response.status_code == 400

    get_resp = client.get(
        BASE_URL + f"/customers/{cardless_customer_json['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert get_resp.json()["card"] is None


def test_attach_nonexistent_card(client, auth_tokens, cardless_customer_json, role):
    attach_response = client.patch(
        BASE_URL + f"/customers/{cardless_customer_json['id']}/attach-card/1000000001",
        headers=auth_header(auth_tokens, role),
    )
    assert attach_response.status_code == 404

    get_resp = client.get(
        BASE_URL + f"/customers/{cardless_customer_json['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert get_resp.json()["card"] is None


def test_attach_card_to_nonexistent_customer(client, auth_tokens, card_01, role):
    attach_response = client.patch(
        BASE_URL + f"/customers/105/attach-card/{card_01['card_id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert attach_response.status_code == 404


def test_attach_already_attached_card(
    client, auth_tokens, cardless_customer_json, customer_json, role
):
    attach_response = client.patch(
        BASE_URL
        + f"/customers/{cardless_customer_json['id']}/attach-card/{customer_json['card']['card_id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert attach_response.status_code == 409


# -----------------------------------
# MODIFY POINTS OF A CUSTOMER CARD
# -----------------------------------


def test_modify_card_points(client, auth_tokens, customer_json, role):
    new_points = 30
    modify_response = client.patch(
        BASE_URL
        + f"/customers/cards/{customer_json['card']['card_id']}?points={new_points}",
        headers=auth_header(auth_tokens, role),
    )
    assert modify_response.status_code == 201

    customer_get_response = client.get(
        BASE_URL + f"/customers/{customer_json['id']}",
        headers=auth_header(auth_tokens, role),
    )
    updated_customer_data = customer_get_response.json()
    assert updated_customer_data["card"]["card_id"] == customer_json["card"]["card_id"]
    assert updated_customer_data["card"]["points"] == new_points


def test_modify_card_points_unauthenticated(client, customer_json):
    new_points = 30
    modify_response = client.patch(
        BASE_URL
        + f"/customers/cards/{customer_json['card']['card_id']}?points={new_points}",
    )
    assert modify_response.status_code == 401


def test_modify_invalid_card_points(client, auth_tokens, customer_json, role):
    new_points = 30
    invalid_id = "12invalid234"
    modify_response = client.patch(
        BASE_URL + f"/customers/cards/{invalid_id}?points={new_points}",
        headers=auth_header(auth_tokens, role),
    )
    assert modify_response.status_code == 400

    customer_get_resp = client.get(
        BASE_URL + f"/customers/{customer_json['id']}",
        headers=auth_header(auth_tokens, role),
    )
    customer_get_resp.json()["card"]["points"] = customer_json["card"]["points"]


def test_modify_nonexistent_card_points(client, auth_tokens, role):
    new_points = 30
    nonexistent_card_id = "0000000002"
    modify_response = client.patch(
        BASE_URL + f"/customers/cards/{nonexistent_card_id}?points={new_points}",
        headers=auth_header(auth_tokens, role),
    )
    assert modify_response.status_code == 404


def test_modify_card_insufficient_points(client, auth_tokens, card_01, role):
    new_points = -5
    modify_response = client.patch(
        BASE_URL + f"/customers/cards/{card_01['card_id']}?points={new_points}",
        headers=auth_header(auth_tokens, role),
    )
    assert modify_response.status_code == 500
