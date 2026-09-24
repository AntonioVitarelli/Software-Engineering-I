import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db


BASE_URL = "http://127.0.0.1:8000/api/v1"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

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

ORDER_SAMPLE = {
    "id": 1,
    "product_barcode": "000000000011",
    "quantity": 100,
    "price_per_unit": 10.5,
    "status": "ISSUED",
    "issue_date": "2025-10-30T12:34:56"
}

ORDER_SAMPLE_MANAGER = {
    "id": 1,
    "product_barcode": "000000000001",
    "quantity": 100,
    "price_per_unit": 10.5,
    "status": "ISSUED",
    "issue_date": "2025-10-30T12:34:56"
}


# ---------------------------
# ISSUE NEW ORDER 
# --------------------------


def test_issue_order_success_as_admin(client, auth_tokens):
    product_payload = {
        "id": 1,
        "description": "Chocolate Bar",
        "barcode": "000000000011",
        "price_per_unit": 2.99,
        "note": "Imported from Belgium",
        "quantity": 0,
        "position": "1-A-3"
    }
    
    product_resp = client.post(
        BASE_URL + "/products",
        json=product_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    
    print(product_resp.json())
    assert product_resp.status_code == 201
    
    resp = client.post(
        BASE_URL + "/orders",
        json=ORDER_SAMPLE,
        headers=auth_header(auth_tokens, "admin")
    )

    print("\n\njson" + str(resp.json()))
    assert resp.status_code == 201
    data = resp.json()

    # I don't assert id because it is auto-generated, even if is provided in the payload it will be ignored
    # assert data["id"] == ORDER_SAMPLE["id"]
    assert data["product_barcode"] == ORDER_SAMPLE["product_barcode"]
    assert data["quantity"] == ORDER_SAMPLE["quantity"]
    assert data["price_per_unit"] == ORDER_SAMPLE["price_per_unit"]
    assert data["status"] == ORDER_SAMPLE["status"]

def test_issue_order_success_as_shop_manager(client, auth_tokens):
    product_payload = {
        "id": 1,
        "description": "Chocolate Bar",
        "barcode": "000000000001",
        "price_per_unit": 2.99,
        "note": "Imported from Belgium",
        "quantity": 0,
        "position": "1-A-3"
    }
    
    product_resp = client.post(
        BASE_URL + "/products",
        json=product_payload,
        headers=auth_header(auth_tokens, "manager")
    )
    
    print(product_resp.json())
    assert product_resp.status_code == 201
    
    resp = client.post(
        BASE_URL + "/orders",
        json=ORDER_SAMPLE_MANAGER,
        headers=auth_header(auth_tokens, "manager")
    )

    print("\n\njson" + str(resp.json()))
    assert resp.status_code == 201
    data = resp.json()

    # I don't assert id because it is auto-generated, even if is provided in the payload it will be ignored
    # assert data["id"] == ORDER_SAMPLE["id"]
    assert data["product_barcode"] == ORDER_SAMPLE_MANAGER["product_barcode"]
    assert data["quantity"] == ORDER_SAMPLE_MANAGER["quantity"]
    assert data["price_per_unit"] == ORDER_SAMPLE_MANAGER["price_per_unit"]
    assert data["status"] == ORDER_SAMPLE_MANAGER["status"]

def test_issue_order_forbidden_as_cashier(client, auth_tokens):
    resp = client.post(
        BASE_URL + "/orders",
        json=ORDER_SAMPLE,
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 403

def test_bad_request_missing_parameters(client, auth_tokens):
    product_payload = {
        "id": 1,
        "description": "Chocolate Bar",
        "barcode": "000000000002",
        "price_per_unit": 2.99,
        "note": "Imported from Belgium",
        "quantity": 0,
        "position": "1-A-3"
    }

    product_resp = client.post(
        BASE_URL + "/products",
        json=product_payload,
        headers=auth_header(auth_tokens, "admin")
    )

    print(product_resp.json())
    assert product_resp.status_code == 201

    bad_order = {
        "product_barcode": "000000000002",
        "quantity": 50
    }

    resp = client.post(
        BASE_URL + "/orders",
        json=bad_order,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code in (400, 422)


def test_issue_order_unauthenticated(client):
    resp = client.post(BASE_URL + "/orders", json=ORDER_SAMPLE)
    assert resp.status_code == 401

def test_issue_order_invalid_product_barcode(client, auth_tokens):
    invalid_product_barcode = {
        "id": 2,
        "product_barcode": "INVALID_BARCODE",
        "quantity": 50,
        "price_per_unit": 5.0,
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }

    resp = client.post(
        BASE_URL + "/orders",
        json=invalid_product_barcode,
        headers=auth_header(auth_tokens, "admin")
    )
    print("\n\njson" + str(resp.json()))
    assert resp.status_code == 400


# GET

def test_get_order_success_as_admin(client, auth_tokens):
    resp = client.get(
        BASE_URL + "/orders",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

def test_get_order_success_as_shop_manager(client, auth_tokens):
    resp = client.get(
        BASE_URL + "/orders",
        headers=auth_header(auth_tokens, "manager")
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

def test_get_order_forbidden_as_cashier(client, auth_tokens):
    resp = client.get(
        BASE_URL + "/orders",
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 403

def test_get_order_unauthenticated(client):
    resp = client.get(BASE_URL + "/orders")
    assert resp.status_code == 401

# POST /orders/payfor

def test_create_and_pay_order_as_admin(client, auth_tokens):
    # Create product
    product_payload = {
        "id": 5,
        "description": "Gummy Bears",
        "barcode": "000000000033",
        "price_per_unit": 1.99,
        "note": "Fruit flavored",
        "quantity": 0,
        "position": "2-B-4"
    }
    
    product_resp = client.post(
        BASE_URL + "/products",
        json=product_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert product_resp.status_code == 201
    
    # Issue order
    order_payload = {
            "id": 1,
            "product_barcode": "000000000001",
            "quantity": 1,
            "price_per_unit": 10.5,
            "status": "ISSUED",
            "issue_date": "2025-10-30T12:34:56"
            }
    
    set_balance = client.post(
        BASE_URL + "/balance/set?amount=10000",
        headers=auth_header(auth_tokens, "admin")
    )

    assert set_balance.status_code == 201
    
    order_resp = client.post(
        BASE_URL + "/orders/payfor",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    
    print("\n\njson" + str(order_resp.json()))

    assert order_resp.status_code == 201
    order_data = order_resp.json()
    assert order_data["status"] == "PAID"
    assert order_data["product_barcode"] == order_payload["product_barcode"]
    assert order_data["quantity"] == order_payload["quantity"]
    assert order_data["price_per_unit"] == order_payload["price_per_unit"]

def test_create_and_pay_order_as_shop_manager(client, auth_tokens):
    # Create product
    product_payload = {
        "id": 6,
        "description": "Gummy Bears",
        "barcode": "000000000004",
        "price_per_unit": 1.99,
        "note": "Fruit flavored",
        "quantity": 0,
        "position": "2-B-4"
    }
    
    product_resp = client.post(
        BASE_URL + "/products",
        json=product_payload,
        headers=auth_header(auth_tokens, "manager")
    )
    
    assert product_resp.status_code == 201
    
    # Issue order
    order_payload = {
            "id": 1,
            "product_barcode": "000000000001",
            "quantity": 1,
            "price_per_unit": 10.5,
            "status": "ISSUED",
            "issue_date": "2025-10-30T12:34:56"
            }
    
    set_balance = client.post(
        BASE_URL + "/balance/set?amount=10000",
        headers=auth_header(auth_tokens, "admin")
    )

    assert set_balance.status_code == 201
    
    order_resp = client.post(
        BASE_URL + "/orders/payfor",
        json=order_payload,
        headers=auth_header(auth_tokens, "manager")
    )
    
    print("\n\njson" + str(order_resp.json()))

    assert order_resp.status_code == 201
    order_data = order_resp.json()
    assert order_data["status"] == "PAID"
    assert order_data["product_barcode"] == order_payload["product_barcode"]
    assert order_data["quantity"] == order_payload["quantity"]
    assert order_data["price_per_unit"] == order_payload["price_per_unit"]

def test_create_and_pay_order_forbidden_as_cashier(client, auth_tokens):
    order_payload = {
        "id": 2,
        "product_barcode": "000000000011",
        "quantity": 50,
        "price_per_unit": 5.0,
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }

    resp = client.post(
        BASE_URL + "/orders/payfor",
        json=order_payload,
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 403

def test_create_and_pay_order_unauthenticated(client):
    order_payload = {
        "id": 2,
        "product_barcode": "000000000011",
        "quantity": 50,
        "price_per_unit": 5.0,
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }

    resp = client.post(
        BASE_URL + "/orders/payfor",
        json=order_payload
    )
    assert resp.status_code == 401

def test_create_and_pay_order_invalid_product_barcode(client, auth_tokens):
    invalid_product_barcode = {
        "id": 2,
        "product_barcode": "INVALID_BARCODE",
        "quantity": 50,
        "price_per_unit": 5.0,
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }

    resp = client.post(
        BASE_URL + "/orders/payfor",
        json=invalid_product_barcode,
        headers=auth_header(auth_tokens, "admin")
    )
    print("\n\njson" + str(resp.json()))
    assert resp.status_code == 400

def test_create_and_pay_order_insufficient_balance(client, auth_tokens):
    # Ensure balance is low
    set_balance = client.post(
        BASE_URL + "/balance/set?amount=1",
        headers=auth_header(auth_tokens, "admin")
    )

    assert set_balance.status_code == 201

    order_payload = {
        "id": 3,
        "product_barcode": "000000000011",
        "quantity": 100,
        "price_per_unit": 10.5,
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }

    resp = client.post(
        BASE_URL + "/orders/payfor",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    print("\n\njson" + str(resp.json()))
    assert resp.status_code == 421

def test_create_and_pay_order_bad_request_missing_parameters(client, auth_tokens):
    bad_order = {
        "id": 3,
        #"product_barcode": "000000000011",
        #"quantity": 100,
        "price_per_unit": 10.5,
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }

    resp = client.post(
        BASE_URL + "/orders/payfor",
        json=bad_order,
        headers=auth_header(auth_tokens, "admin")
    )

    # ! attenzione non è stato gestito l'errore 400 (missing values in body)
    assert resp.status_code == 400 or resp.status_code == 422

# PATCH /orders/{order_id}/pay

def test_pay_existing_order_success_as_admin(client, auth_tokens):
    # First, issue an order to be paid
    order_payload = {
        "id": 4,
        "product_barcode": "000000000011",
        "quantity": 10,
        "price_per_unit": 10.5,
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }

    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )

    assert issue_resp.status_code == 201
    order_id = issue_resp.json()["id"]
    # Ensure sufficient balance
    set_balance = client.post(
        BASE_URL + "/balance/set?amount=10000",
        headers=auth_header(auth_tokens, "admin")
    )
    assert set_balance.status_code == 201
    # Now, pay the issued order
    pay_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/pay",
        headers=auth_header(auth_tokens, "admin")
    )
    print("\n\njson" + str(pay_resp.json()))
    assert pay_resp.status_code == 201
    pay_data = pay_resp.json()
    assert pay_data["success"] is True

def test_pay_existing_order_success_as_shop_manager(client, auth_tokens):
    # First, issue an order to be paid
    order_payload = {
        "id": 4,
        "product_barcode": "000000000001",
        "quantity": 10,
        "price_per_unit": 10.5,
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }

    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "manager")
    )

    assert issue_resp.status_code == 201
    order_id = issue_resp.json()["id"]
    # Ensure sufficient balance
    set_balance = client.post(
        BASE_URL + "/balance/set?amount=10000",
        headers=auth_header(auth_tokens, "admin")
    )
    assert set_balance.status_code == 201
    # Now, pay the issued order
    pay_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/pay",
        headers=auth_header(auth_tokens, "manager")
    )
    print("\n\njson" + str(pay_resp.json()))
    assert pay_resp.status_code == 201
    pay_data = pay_resp.json()
    assert pay_data["success"] is True

def test_pay_existing_order_forbidden_as_cashier(client, auth_tokens):

    order_payload = {
        "id": 4,
        "product_barcode": "000000000011",
        "quantity": 10,
        "price_per_unit": 10.5,
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }
    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert issue_resp.status_code == 201
    order_id = issue_resp.json()["id"]

    pay_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/pay",
        headers=auth_header(auth_tokens, "cashier")
    )
    assert pay_resp.status_code == 403

def test_pay_existing_order_unauthenticated(client, auth_tokens):
    # First, issue an order to be paid
    order_payload = {
        "id": 4,
        "product_barcode": "000000000011",
        "quantity": 10,
        "price_per_unit": 10.5,
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }

    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )

    assert issue_resp.status_code == 201
    order_id = issue_resp.json()["id"]

    # Attempt to pay without authentication
    pay_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/pay"
    )
    assert pay_resp.status_code == 401

def test_pay_existing_order_not_found(client, auth_tokens):
    non_existent_order_id = 9999

    pay_resp = client.patch(
        f"{BASE_URL}/orders/{non_existent_order_id}/pay",
        headers=auth_header(auth_tokens, "admin")
    )
    print("\n\njson" + str(pay_resp.json()))
    assert pay_resp.status_code == 404

def test_pay_existing_order_invalid_id(client, auth_tokens):
    invalid_order_id = -1

    pay_resp = client.patch(
        f"{BASE_URL}/orders/{invalid_order_id}/pay",
        headers=auth_header(auth_tokens, "admin")
    )
    print("\n\njson" + str(pay_resp.json()))
    assert pay_resp.status_code == 400

def test_pay_existing_order_invalid_state(client, auth_tokens):
    # First, issue and pay an order
    order_payload = {
        "id": 4,
        "product_barcode": "000000000011",
        "quantity": 10,
        "price_per_unit": 10.5
    }
    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert issue_resp.status_code == 201
    order_id = issue_resp.json()["id"]
    # Ensure sufficient balance
    set_balance = client.post(
        BASE_URL + "/balance/set?amount=10000",
        headers=auth_header(auth_tokens, "admin")
    )

    assert set_balance.status_code == 201
    pay_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/pay",
        headers=auth_header(auth_tokens, "admin")
    )

    pay_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/pay",
        headers=auth_header(auth_tokens, "admin")
    )
    assert pay_resp.status_code == 420

def test_pay_existing_order_insufficient_balance(client, auth_tokens):
    # First, issue an order to be paid
    order_payload = {
        "id": 4,
        "product_barcode": "000000000011",
        "quantity": 10,
        "price_per_unit": 10.5, 
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }

    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert issue_resp.status_code == 201
    order_id = issue_resp.json()["id"]

    # Set low balance
    set_balance = client.post(
        BASE_URL + "/balance/set?amount=1",
        headers=auth_header(auth_tokens, "admin")
    )

    assert set_balance.status_code == 201
    pay_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/pay",
        headers=auth_header(auth_tokens, "admin")
    )
    print("\n\njson" + str(pay_resp.json()))
    assert pay_resp.status_code == 421

# PATCH /orders/{order_id}/arrival

def test_record_arrival_success_as_admin(client, auth_tokens):
    # First, issue and pay an order
    order_payload = {
        "id": 10,
        "product_barcode": "000000000011",
        "quantity": 10,
        "price_per_unit": 10.5
    }

    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert issue_resp.status_code == 201
    order_id = issue_resp.json()["id"]

    set_balance = client.post(
        BASE_URL + "/balance/set?amount=10000",
        headers=auth_header(auth_tokens, "admin")
    )
    assert set_balance.status_code == 201

    pay_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/pay",
        headers=auth_header(auth_tokens, "admin")
    )
    assert pay_resp.status_code == 201

    arrival_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/arrival",
        headers=auth_header(auth_tokens, "admin")
    )

    print("\n\njson" + str(arrival_resp.json()))
    assert arrival_resp.status_code == 201
    arrival_data = arrival_resp.json()  
    assert arrival_data["success"] is True

def test_record_arrival_success_as_shop_manager(client, auth_tokens):
    # First, issue and pay an order
    order_payload = {
        "id": 11,
        "product_barcode": "000000000001",
        "quantity": 10,
        "price_per_unit": 10.5
    }

    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "manager")
    )   
    assert issue_resp.status_code == 201
    order_id = issue_resp.json()["id"]

    set_balance = client.post(
        BASE_URL + "/balance/set?amount=10000",
        headers=auth_header(auth_tokens, "admin")
    )

    assert set_balance.status_code == 201

    pay_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/pay",
        headers=auth_header(auth_tokens, "admin")
    )
    assert pay_resp.status_code == 201

    arrival_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/arrival",
        headers=auth_header(auth_tokens, "manager")
    )

    print("\n\njson" + str(arrival_resp.json()))
    assert arrival_resp.status_code == 201
    arrival_data = arrival_resp.json()  
    assert arrival_data["success"] is True

def test_record_arrival_forbidden_as_cashier(client, auth_tokens):
    # First, issue and pay an order
    order_payload = {
        "id": 12,
        "product_barcode": "000000000011",
        "quantity": 10,
        "price_per_unit": 10.5,
        "status": "PAID",
        "issue_date": "2025-10-30T12:34:56"
    }

    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert issue_resp.status_code == 201
    order_id = issue_resp.json()["id"]
    arrival_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/arrival",
        headers=auth_header(auth_tokens, "cashier")
    )
    assert arrival_resp.status_code == 403

def test_record_arrival_unauthenticated(client, auth_tokens):
    # First, issue and pay an order
    order_payload = {
        "id": 13,
        "product_barcode": "000000000011",
        "quantity": 10,
        "price_per_unit": 10.5,
        "status": "PAID",
        "issue_date": "2025-10-30T12:34:56"
    }

    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert issue_resp.status_code == 201
    order_id = issue_resp.json()["id"]
    arrival_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/arrival"
    )
    assert arrival_resp.status_code == 401

def test_order_not_found(client, auth_tokens):
    non_existent_order_id = 9999

    arrival_resp = client.patch(
        f"{BASE_URL}/orders/{non_existent_order_id}/arrival",
        headers=auth_header(auth_tokens, "admin")
    )
    print("\n\njson" + str(arrival_resp.json()))
    assert arrival_resp.status_code == 404

def test_orders_invalid_id(client, auth_tokens):
    invalid_order_id = -1

    arrival_resp = client.patch(
        f"{BASE_URL}/orders/{invalid_order_id}/arrival",
        headers=auth_header(auth_tokens, "admin")
    )
    print("\n\njson" + str(arrival_resp.json()))
    assert arrival_resp.status_code == 400

def test_record_arrival_invalid_state(client, auth_tokens):
    # First, issue an order but do not pay it
    order_payload = {
        "id": 14,
        "product_barcode": "000000000011",
        "quantity": 10,
        "price_per_unit": 10.5,
        "status": "ISSUED",
        "issue_date": "2025-10-30T12:34:56"
    }

    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert issue_resp.status_code == 201
    order_id = issue_resp.json()["id"]

    arrival_resp = client.patch(
        f"{BASE_URL}/orders/{order_id}/arrival",
        headers=auth_header(auth_tokens, "admin")
    )
    print("\n\njson" + str(arrival_resp.json()))
    assert arrival_resp.status_code == 420

def test_product_not_found(client, auth_tokens):
    # First, issue and pay an order for a non-existent product
    order_payload = {
        "id": 15,
        "product_barcode": "111111111111",
        "quantity": 10,
        "price_per_unit": 10.5,
        "status": "PAID",
        "issue_date": "2025-10-30T12:34:56"
    }

    issue_resp = client.post(
        BASE_URL + "/orders",
        json=order_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert issue_resp.status_code == 404
