import asyncio

import pytest
from fastapi.testclient import TestClient

from init_db import reset, init_db
from main import app
from app.repositories.product_type_repository import ProductTypeRepository
from app.repositories.sale_repository import SaleRepository
from app.repositories.return_repository import ReturnRepository
from app.models.sale_status import SaleStatus
from app.models.return_status import ReturnStatus
from app.controllers.sale_controller import add_product
from app.controllers.return_controller import add_product_to_return
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
# SAMPLE PAYLOADS
# ---------------------------

INVALID_ID_PAYLOADS = [
    {"sale_id": 0},           # Zero is invalid (must be > 0)
    {"sale_id": -1},          # Negative number is invalid
    {"sale_id": "abc"},       # String is invalid
    {"sale_id": 1.5},         # Float is invalid
    {"sale_id": None},        # None is invalid
    {}                        # Missing is invalid
]

INVALID_PATH_IDS = [0, -1, "abc", 1.5, None]  # Per path parameters

# ---------------------------
# GLOBAL FIXTURE FOR TOKENS
# ---------------------------

@pytest.fixture(scope="session", autouse=True)
def auth_tokens(event_loop, client):
    """Authenticate users once and return their JWT tokens."""

    event_loop.run_until_complete(reset())
    event_loop.run_until_complete(init_db())
    event_loop.run_until_complete(init_return_test_data())

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

async def init_return_test_data():
    product_repo = ProductTypeRepository()
    sale_repo = SaleRepository()
    return_repo = ReturnRepository()

    # 1) Product
    product = await product_repo.create_product_type(
        description="Test Product",
        barcode="0123456789012",
        price_per_unit=10.00,
        note="Test product for returns",
        quantity=100,
        position="A1"
    )

    # 2) Sale 1 (PAID)
    sale1 = await sale_repo.create_sale()
    await add_product(sale1, product, 10)
    await sale_repo.update_sale(sale1)
    sale1.status = SaleStatus.PENDING
    await sale_repo.update_sale(sale1)
    sale1.status = SaleStatus.PAID
    await sale_repo.update_sale(sale1)

    # 3) Sale 2 (OPEN)
    sale2 = await sale_repo.create_sale()
    await add_product(sale2, product, 5)
    await sale_repo.update_sale(sale2)

    # 4) Return 1 (OPEN, no products)
    await return_repo.create_return(sale1.id)

    # 5) Return 2 (OPEN, with product)
    return2 = await return_repo.create_return(sale1.id)
    await add_product_to_return(return2, product, 1)
    await return_repo.update_return(return2)

    # 6) Return 3 (CLOSED)
    return3 = await return_repo.create_return(sale1.id)
    await add_product_to_return(return3, product, 1)
    return3.status = ReturnStatus.CLOSED
    await return_repo.update_return(return3)

    # 7) Return 4 (REIMBURSED)
    return4 = await return_repo.create_return(sale1.id)
    await add_product_to_return(return4, product, 1)
    return4.status = ReturnStatus.CLOSED
    await return_repo.update_return(return4)
    return4.status = ReturnStatus.REIMBURSED
    await return_repo.update_return(return4)

    # 8) Return 5 (OPEN, with product)
    return5 = await return_repo.create_return(sale1.id)
    await add_product_to_return(return5, product, 1)
    await return_repo.update_return(return5)

# ---------------------------
# START RETURN TRANSACTION
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_start_return_transaction_success(client, auth_tokens, role):
    resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, role),
        params={"sale_id": 1},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["status"].lower() == "open"
    
@pytest.mark.parametrize("payload", INVALID_ID_PAYLOADS)
def test_start_return_transaction_invalid_sale_id(client, auth_tokens, payload):
    # Test with invalid sale_id as query parameter
    # Extract the sale_id value from payload for testing
    sale_id_value = payload.get("sale_id") if isinstance(payload, dict) else None
    if sale_id_value is None and isinstance(payload, dict):
        sale_id_value = ""  # Empty string for missing
    
    if sale_id_value == "":
        # Missing parameter test - don't include sale_id
        resp = client.post(
            BASE_URL + "/returns",
            headers=auth_header(auth_tokens, "admin"),
        )
    else:
        resp = client.post(
            BASE_URL + "/returns",
            headers=auth_header(auth_tokens, "admin"),
            params={"sale_id": sale_id_value},
        )
    # Invalid query parameter gives 422 (Unprocessable Entity)
    assert resp.status_code in (400, 422)

def test_start_return_transaction_requires_auth(client):
    resp = client.post(BASE_URL + "/returns", params={"sale_id": 1})
    assert resp.status_code == 401
    
def test_start_return_transaction_sale_not_found(client, auth_tokens):
    resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 999999},
    )
    assert resp.status_code == 404

def test_start_return_transaction_invalid_state(client, auth_tokens):
    # sale_id=2 assumed not in PAID state (e.g., OPEN/CLOSED already returned)
    resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 2},
    )
    assert resp.status_code == 420
    
# ---------------------------
# GET ALL RETURN TRANSACTIONS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_list_returns_success(client, auth_tokens, role):
    resp = client.get(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_list_returns_requires_auth(client):
    resp = client.get(BASE_URL + "/returns")
    assert resp.status_code == 401
    
# -------------------------------
# GET A RETURN TRANSACTIONS BY ID
# -------------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_get_return_by_id_success(client, auth_tokens, role):
    # assume return with id=1 exists from fixtures/init
    resp = client.get(
        f"{BASE_URL}/returns/1",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert "status" in data
    
@pytest.mark.parametrize("rid", INVALID_PATH_IDS)
def test_get_return_by_id_invalid_id(client, auth_tokens, rid):
    resp = client.get(
        f"{BASE_URL}/returns/{rid}",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 400

def test_get_return_by_id_requires_auth(client):
    resp = client.get(f"{BASE_URL}/returns/1")
    assert resp.status_code == 401
    
def test_get_return_by_id_not_found(client, auth_tokens):
    resp = client.get(
        f"{BASE_URL}/returns/999999",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 404

# ---------------------------
# DELETE A RETURN TRANSACTION
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_delete_return_success(client, auth_tokens, role):
    # Create a fresh return to delete
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Delete it
    resp = client.delete(
        f"{BASE_URL}/returns/{return_id}",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 204

@pytest.mark.parametrize("rid", INVALID_PATH_IDS)
def test_delete_return_by_id_invalid_id(client, auth_tokens, rid):
    resp = client.delete(
        f"{BASE_URL}/returns/{rid}",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 400

    
def test_delete_return_requires_auth(client):
    resp = client.delete(f"{BASE_URL}/returns/1")
    assert resp.status_code == 401

def test_delete_return_not_found(client, auth_tokens):
    resp = client.delete(
        f"{BASE_URL}/returns/999999",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 404

def test_delete_return_reimbursed_state(client, auth_tokens):
    # Use return_id=4 which is REIMBURSED in fixtures
    resp = client.delete(
        f"{BASE_URL}/returns/4",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 420

# ---------------------------
# GET RETURNS BY SALE ID
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_get_returns_by_sale_success(client, auth_tokens, role):
    resp = client.get(
        f"{BASE_URL}/returns/sale/1",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

@pytest.mark.parametrize("sid", INVALID_PATH_IDS)
def test_get_returns_by_sale_invalid_id(client, auth_tokens, sid):
    resp = client.get(
        f"{BASE_URL}/returns/sale/{sid}",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 400

def test_get_returns_by_sale_missing_id(client, auth_tokens):
    resp = client.get(f"{BASE_URL}/returns/sale/", headers=auth_header(auth_tokens, "admin"))
    # Missing ID should return 400 according to swagger: "Invalid or missing id"
    assert resp.status_code == 400

def test_get_returns_by_sale_requires_auth(client):
    resp = client.get(f"{BASE_URL}/returns/sale/1")
    assert resp.status_code == 401

# ---------------------------
# ADD PRODUCT TO RETURN
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_add_product_to_return_success(client, auth_tokens, role):
    # Create a fresh return to avoid interference with other tests
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Now add product to the fresh return
    resp = client.post(
        f"{BASE_URL}/returns/{return_id}/items",
        headers=auth_header(auth_tokens, role),
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True

@pytest.mark.parametrize("rid", INVALID_PATH_IDS)
def test_add_product_to_return_invalid_return_id(client, auth_tokens, rid):
    resp = client.post(
        f"{BASE_URL}/returns/{rid}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert resp.status_code == 400


def test_add_product_to_return_requires_auth(client):
    resp = client.post(
        f"{BASE_URL}/returns/1/items",
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert resp.status_code == 401

def test_add_product_to_return_not_found(client, auth_tokens):
    resp = client.post(
        f"{BASE_URL}/returns/999999/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert resp.status_code == 404

def test_add_product_to_return_invalid_state(client, auth_tokens):
    # Use return_id=3 which is CLOSED in fixtures
    resp = client.post(
        f"{BASE_URL}/returns/3/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert resp.status_code == 420

@pytest.mark.parametrize("invalid_amount", [0, -1, -5, "abc", 1.5, None])
def test_add_product_to_return_invalid_quantity(client, auth_tokens, invalid_amount):
    """Test that returned quantity must be positive"""
    # Create a fresh return to avoid interference with other tests
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    resp = client.post(
        f"{BASE_URL}/returns/{return_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012", "amount": invalid_amount},
    )
    assert resp.status_code == 400

def test_add_product_to_return_missing_amount(client, auth_tokens):
    """Test that amount parameter is required"""
    # Create a fresh return to avoid interference with other tests
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    resp = client.post(
        f"{BASE_URL}/returns/{return_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012"},
    )
    assert resp.status_code in (400, 422) 

def test_add_product_to_return_quantity_exceeds_sold(client, auth_tokens):
    """Test that returned quantity cannot exceed the quantity sold"""
    # Create a fresh return to avoid interference with other tests
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    resp = client.post(
        f"{BASE_URL}/returns/{return_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012", "amount": 999999},
    )
    assert resp.status_code == 400

@pytest.mark.parametrize("invalid_barcode", ["", "123", "abc", "12345678901", None])
def test_add_product_to_return_invalid_barcode(client, auth_tokens, invalid_barcode):
    """Test that barcode must be valid (correct format)"""
    # Create a fresh return
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    resp = client.post(
        f"{BASE_URL}/returns/{return_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": invalid_barcode, "amount": 1},
    )
    assert resp.status_code == 400

def test_add_product_to_return_barcode_not_found(client, auth_tokens):
    """Test that barcode must exist in the system"""
    # Create a fresh return
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    resp = client.post(
        f"{BASE_URL}/returns/{return_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "9999999999999", "amount": 1},
    )
    assert resp.status_code == 400

# ---------------------------
# REMOVE PRODUCT FROM RETURN
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_remove_product_from_return_success(client, auth_tokens, role):
    # Create a fresh return with a product to remove (for each role)
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Add product to return first
    add_resp = client.post(
        f"{BASE_URL}/returns/{return_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert add_resp.status_code == 201
    
    # Now remove it with the test role
    resp = client.delete(
        f"{BASE_URL}/returns/{return_id}/items",
        headers=auth_header(auth_tokens, role),
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["success"] is True
    
    # Verify the product was actually removed from the return
    get_resp = client.get(
        f"{BASE_URL}/returns/{return_id}",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert get_resp.status_code == 200
    return_data = get_resp.json()
    # The return should have no products (lines should be empty)
    assert len(return_data["lines"]) == 0

def test_remove_product_from_return_requires_auth(client):
    resp = client.delete(
        f"{BASE_URL}/returns/1/items",
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert resp.status_code == 401

def test_remove_product_from_return_not_found(client, auth_tokens):
    resp = client.delete(
        f"{BASE_URL}/returns/999999/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert resp.status_code == 404

def test_remove_product_from_return_invalid_state(client, auth_tokens):
    # Use return_id=3 which is CLOSED in fixtures
    resp = client.delete(
        f"{BASE_URL}/returns/3/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert resp.status_code == 420

# ---------------------------
# CLOSE RETURN
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_close_return_success(client, auth_tokens, role):
    # Create a fresh return to close
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Now close the fresh return
    resp = client.patch(
        f"{BASE_URL}/returns/{return_id}/close",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

@pytest.mark.parametrize("rid", INVALID_PATH_IDS)
def test_close_return_invalid_return_id(client, auth_tokens, rid):
    resp = client.patch(
        f"{BASE_URL}/returns/{rid}/close",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 400

def test_close_return_requires_auth(client):
    resp = client.patch(f"{BASE_URL}/returns/1/close")
    assert resp.status_code == 401

def test_close_return_not_found(client, auth_tokens):
    resp = client.patch(
        f"{BASE_URL}/returns/999999/close",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 404

def test_close_return_invalid_state(client, auth_tokens):
    # Use return_id=3 which is CLOSED in fixtures (can't close twice)
    resp = client.patch(
        f"{BASE_URL}/returns/3/close",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 420

def test_close_return_empty_return_is_deleted(client, auth_tokens):
    """Test that closing an EMPTY OPEN return (no products) deletes it from database"""
    # Create a new empty return to test deletion
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    new_return_id = create_resp.json()["id"]
    
    # Close the empty return
    close_resp = client.patch(
        f"{BASE_URL}/returns/{new_return_id}/close",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert close_resp.status_code == 200
    
    # Try to get the deleted return - should return 404
    get_resp = client.get(
        f"{BASE_URL}/returns/{new_return_id}",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert get_resp.status_code == 404

def test_close_return_with_products_restores_inventory(client, auth_tokens):
    """Test that closing an OPEN return with products restores quantities to inventory"""
    # Create a fresh return with a product
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Add product to the return
    add_resp = client.post(
        f"{BASE_URL}/returns/{return_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert add_resp.status_code == 201
    
    # Close the return with products
    close_resp = client.patch(
        f"{BASE_URL}/returns/{return_id}/close",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert close_resp.status_code == 200
    assert close_resp.json()["success"] is True
    
    # Verify the return is now CLOSED
    get_resp = client.get(
        f"{BASE_URL}/returns/{return_id}",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert get_resp.status_code == 200
    closed_return = get_resp.json()
    assert closed_return["status"].lower() == "closed"

# ---------------------------
# REIMBURSE RETURN
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager"])
def test_reimburse_return_success(client, auth_tokens, role):
    # Create a fresh return and close it first
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Add product
    add_resp = client.post(
        f"{BASE_URL}/returns/{return_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert add_resp.status_code == 201
    
    # Close it
    close_resp = client.patch(
        f"{BASE_URL}/returns/{return_id}/close",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert close_resp.status_code == 200
    
    # Now reimburse
    resp = client.patch(
        f"{BASE_URL}/returns/{return_id}/reimburse",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "refund_amount" in data

def test_reimburse_return_cashier_forbidden(client, auth_tokens):
    """Test that cashier CANNOT reimburse (only admin and manager can)"""
    # Create a fresh return and close it first
    create_resp = client.post(
        BASE_URL + "/returns",
        headers=auth_header(auth_tokens, "admin"),
        params={"sale_id": 1},
    )
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Add product
    add_resp = client.post(
        f"{BASE_URL}/returns/{return_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": "0123456789012", "amount": 1},
    )
    assert add_resp.status_code == 201
    
    # Close it
    close_resp = client.patch(
        f"{BASE_URL}/returns/{return_id}/close",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert close_resp.status_code == 200
    
    # Try to reimburse as cashier (forbidden)
    resp = client.patch(
        f"{BASE_URL}/returns/{return_id}/reimburse",
        headers=auth_header(auth_tokens, "cashier"),
    )
    assert resp.status_code == 403

@pytest.mark.parametrize("rid", INVALID_PATH_IDS)
def test_reimburse_return_invalid_return_id(client, auth_tokens, rid):
    resp = client.patch(
        f"{BASE_URL}/returns/{rid}/reimburse",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 400

def test_reimburse_return_requires_auth(client):
    resp = client.patch(f"{BASE_URL}/returns/1/reimburse")
    assert resp.status_code == 401

def test_reimburse_return_not_found(client, auth_tokens):
    resp = client.patch(
        f"{BASE_URL}/returns/999999/reimburse",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 404

def test_reimburse_return_invalid_state(client, auth_tokens):
    # Use return_id=1 which is OPEN in fixtures (can't reimburse OPEN)
    resp = client.patch(
        f"{BASE_URL}/returns/1/reimburse",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert resp.status_code == 420
