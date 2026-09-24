import asyncio

import pytest
from fastapi.testclient import TestClient

from init_db import init_db, reset
from main import app
from tests.product_type_test import PRODUCT_SAMPLE, PRODUCT_SAMPLE_2


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
def open_empty_sale(client, auth_tokens):
    sale_resp = client.post(
        BASE_URL + "/sales",
        headers=auth_header(auth_tokens, "admin"),
    )
    return sale_resp.json()


@pytest.fixture
def open_sale(client, auth_tokens, open_empty_sale):
    product = client.post(
        BASE_URL + "/products",
        json=PRODUCT_SAMPLE,
        headers=auth_header(auth_tokens, "admin"),
    ).json()
    client.post(
        BASE_URL
        + f"/sales/{open_empty_sale['id']}/items?barcode={product['barcode']}&amount=2",
        headers=auth_header(auth_tokens, "admin"),
    )
    non_empty_sale_resp = client.get(
        BASE_URL + f"/sales/{open_empty_sale['id']}",
        headers=auth_header(auth_tokens, "admin"),
    )
    return non_empty_sale_resp.json()


@pytest.fixture
def pending_sale(client, auth_tokens, open_sale):
    client.patch(
        BASE_URL + f"/sales/{open_sale['id']}/close",
        headers=auth_header(auth_tokens, "admin"),
    )
    pending_sale_resp = client.get(
        BASE_URL + f"/sales/{open_sale['id']}",
        headers=auth_header(auth_tokens, "admin"),
    )
    return pending_sale_resp.json()


@pytest.fixture
def closed_sale(client, auth_tokens, pending_sale):
    client.patch(
        BASE_URL + f"/sales/{pending_sale['id']}/pay?cash_amount=50",
        headers=auth_header(auth_tokens, "admin"),
    )
    get_resp = client.get(
        BASE_URL + f"/sales/{pending_sale['id']}",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert get_resp.json()["status"] == "PAID"
    return get_resp.json()


@pytest.fixture
def product_sample(client, auth_tokens):
    return client.post(
        BASE_URL + "/products",
        json=PRODUCT_SAMPLE_2,
        headers=auth_header(auth_tokens, "admin"),
    ).json()


# ---------------------------
# SAMPLE PAYLOADS
# ---------------------------

# ---------------------------
# CREATE SALE
# ---------------------------


def test_create_sale(client, auth_tokens, role):
    resp = client.post(BASE_URL + "/sales", headers=auth_header(auth_tokens, role))
    assert resp.status_code == 201
    resp.json()["status"] = "OPEN"


def test_create_sale_unauthenticated(client):
    resp = client.post(BASE_URL + "/sales")
    assert resp.status_code == 401


# ---------------------------
# GET ALL SALE TRANSACTIONS
# ---------------------------


def test_get_all_sale_transactions(client, auth_tokens, role, open_empty_sale):
    resp = client.get(BASE_URL + "/sales", headers=auth_header(auth_tokens, role))
    assert resp.status_code == 200
    sales_list = resp.json()
    assert len(sales_list) == 1
    assert sales_list[0] == open_empty_sale


def test_get_all_sale_transactions_unauthenticated(client):
    resp = client.get(BASE_URL + "/sales")
    assert resp.status_code == 401


# ---------------------------
# GET SALE BY ID
# ---------------------------


def test_get_sale_by_id(client, auth_tokens, role, open_empty_sale):
    resp = client.get(
        BASE_URL + f"/sales/{open_empty_sale['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 200
    sale = resp.json()
    assert sale == open_empty_sale


def test_get_sale_by_invalid_id(client, auth_tokens, role):
    invalid_id = "123invalid234"
    resp = client.get(
        BASE_URL + f"/sales/{invalid_id}",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 400


def test_get_sale_by_missing_id(client, auth_tokens, role):
    missing_id = None
    resp = client.get(
        BASE_URL + f"/sales/{missing_id}",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 400


def test_get_sale_by_id_unauthenticated(client, open_empty_sale):
    resp = client.get(
        BASE_URL + f"/sales/{open_empty_sale['id']}",
    )
    assert resp.status_code == 401


def test_get_sale_by_nonexistent_id(client, open_empty_sale, auth_tokens, role):
    nonexistent_id = int(open_empty_sale["id"]) + 1
    resp = client.get(
        BASE_URL + f"/sales/{nonexistent_id}",
        headers=auth_header(auth_tokens, role),
    )
    assert resp.status_code == 404


# ---------------------------
# DELETE SALE BY ID
# ---------------------------


def test_delete_sale_by_id(client, open_sale, auth_tokens, role):
    # save the quantity of the products associated with the sale before it is deleted
    prev_stocked_product_qty = dict()
    for sold_product in open_sale["lines"]:
        stocked_product = client.get(
            BASE_URL + f"/products/{sold_product['id']}",
            headers=auth_header(auth_tokens, role),
        ).json()
        prev_stocked_product_qty[stocked_product["id"]] = stocked_product["quantity"]

    # delete the sale
    delete_resp = client.delete(
        BASE_URL + f"/sales/{open_sale['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 204

    # check that the products associated with the sale have been restocked
    for sold_product in open_sale["lines"]:
        stocked_product = client.get(
            BASE_URL + f"/products/{sold_product['id']}",
            headers=auth_header(auth_tokens, role),
        ).json()
        assert (
            stocked_product["quantity"]
            == prev_stocked_product_qty[stocked_product["id"]]
            + sold_product["quantity"]
        )


def test_delete_sale_by_invalid_id(client, auth_tokens, role):
    invalid_id = "123invalid_id"
    delete_resp = client.delete(
        BASE_URL + f"/sales/{invalid_id}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 400


def test_delete_sale_by_missing_id(client, auth_tokens, role):
    missing_id = None
    delete_resp = client.delete(
        BASE_URL + f"/sales/{missing_id}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 400


def test_delete_sale_by_id_unauthenticated(client, open_empty_sale):
    delete_resp = client.delete(
        BASE_URL + f"/sales/{open_empty_sale['id']}",
    )
    assert delete_resp.status_code == 401


def test_delete_sale_by_nonexistent_id(client, auth_tokens, role, open_empty_sale):
    nonexistent_id = int(open_empty_sale["id"]) + 1
    delete_resp = client.delete(
        BASE_URL + f"/sales/{nonexistent_id}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 404


def test_delete_paid_sale_by_id(client, auth_tokens, role, closed_sale):
    delete_resp = client.delete(
        BASE_URL + f"/sales/{closed_sale['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 420

    get_resp = client.get(
        BASE_URL + f"/sales/{closed_sale['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert get_resp.status_code == 200


# -----------------------------------------------------
# ADD A PRODUCT TO THE SALE WITH A SPECIFIED QUANTITY
# -----------------------------------------------------


def test_add_product_to_open_sale(client, auth_tokens, role, open_sale, product_sample):
    prev_product_sample_qty = product_sample["quantity"]

    product_sample_added_amount = 2
    add_resp = client.post(
        BASE_URL
        + f"/sales/{open_sale['id']}/items?barcode={product_sample['barcode']}&amount={product_sample_added_amount}",
        headers=auth_header(auth_tokens, role),
    )
    assert add_resp.status_code == 201
    assert add_resp.json()["success"]

    post_stocked_product_sample = client.get(
        BASE_URL + f"/products/{product_sample['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()

    assert (
        post_stocked_product_sample["quantity"]
        == prev_product_sample_qty - product_sample_added_amount
    )


def test_add_invalid_barcode_product_to_open_sale(client, auth_tokens, role, open_sale):
    invalid_barcode = "123invalid_barcode"
    add_resp = client.post(
        BASE_URL + f"/sales/{open_sale['id']}/items?barcode={invalid_barcode}&amount=2",
        headers=auth_header(auth_tokens, role),
    )
    assert add_resp.status_code == 400


def test_add_empty_barcode_product_to_open_sale(client, auth_tokens, role, open_sale):
    empty_barcode = None
    add_resp = client.post(
        BASE_URL + f"/sales/{open_sale['id']}/items?barcode={empty_barcode}&amount=2",
        headers=auth_header(auth_tokens, role),
    )
    assert add_resp.status_code == 400


def test_add_nonexistent_product_to_open_sale(
    client, auth_tokens, role, open_sale, product_sample
):
    nonexistent_product_barcode = int(product_sample["barcode"]) + 1
    add_resp = client.post(
        BASE_URL
        + f"/sales/{open_sale['id']}/items?barcode={nonexistent_product_barcode}&amount=2",
        headers=auth_header(auth_tokens, role),
    )
    assert add_resp.status_code == 404


def test_add_product_to_invalid_sale_id(client, auth_tokens, role, product_sample):
    invalid_sale_id = "1234sale"
    add_resp = client.post(
        BASE_URL
        + f"/sales/{invalid_sale_id}/items?barcode={product_sample['barcode']}&amount=2",
        headers=auth_header(auth_tokens, role),
    )
    assert add_resp.status_code == 400


def test_add_product_to_empty_sale_id(client, auth_tokens, role, product_sample):
    empty_sale_id = None
    add_resp = client.post(
        BASE_URL
        + f"/sales/{empty_sale_id}/items?barcode={product_sample['barcode']}&amount=2",
        headers=auth_header(auth_tokens, role),
    )
    assert add_resp.status_code == 400


def test_add_product_to_open_sale_unauthenticated(
    client, auth_tokens, role, open_sale, product_sample
):
    prev_product_sample_qty = product_sample["quantity"]

    add_resp = client.post(
        BASE_URL
        + f"/sales/{open_sale['id']}/items?barcode={product_sample['barcode']}&amount=2",
    )
    assert add_resp.status_code == 401

    post_stocked_product_sample = client.get(
        BASE_URL + f"/products/{product_sample['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()

    assert post_stocked_product_sample["quantity"] == prev_product_sample_qty


def test_add_product_to_open_sale_insufficient_stock(
    client, auth_tokens, role, open_sale, product_sample
):
    add_resp = client.post(
        BASE_URL
        + f"/sales/{open_sale['id']}/items?barcode={product_sample['barcode']}&amount={product_sample['quantity'] + 1}",
        headers=auth_header(auth_tokens, role),
    )
    assert add_resp.status_code == 400


def test_add_product_to_nonexistent_sale_id(
    client, auth_tokens, role, open_sale, product_sample
):
    nonexistent_id = int(open_sale["id"]) + 1
    add_resp = client.post(
        BASE_URL
        + f"/sales/{nonexistent_id}/items?barcode={product_sample['barcode']}&amount=2",
        headers=auth_header(auth_tokens, role),
    )
    assert add_resp.status_code == 404


def test_add_product_to_pending_sale_id(
    client, auth_tokens, role, pending_sale, product_sample
):
    add_resp = client.post(
        BASE_URL
        + f"/sales/{pending_sale['id']}/items?barcode={product_sample['barcode']}&amount=2",
        headers=auth_header(auth_tokens, role),
    )
    assert add_resp.status_code == 420


def test_add_product_to_closed_sale_id(
    client, auth_tokens, role, closed_sale, product_sample
):
    add_resp = client.post(
        BASE_URL
        + f"/sales/{closed_sale['id']}/items?barcode={product_sample['barcode']}&amount=2",
        headers=auth_header(auth_tokens, role),
    )
    assert add_resp.status_code == 420


# ------------------------------
# REMOVE A PRODUCT FROM A SALE
# ------------------------------


def test_reduce_product_quantity_from_open_sale(client, auth_tokens, role, open_sale):
    sale_product = open_sale["lines"][0]
    prev_product_sample_qty = client.get(
        BASE_URL + f"/products/{sale_product['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()["quantity"]

    product_sample_removed_amount = 1
    delete_resp = client.delete(
        BASE_URL
        + f"/sales/{open_sale['id']}/items?barcode={sale_product['product_barcode']}&amount={product_sample_removed_amount}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 202
    assert delete_resp.json()["success"]

    post_stocked_product_sample = client.get(
        BASE_URL + f"/products/{sale_product['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()

    assert (
        post_stocked_product_sample["quantity"]
        == prev_product_sample_qty + product_sample_removed_amount
    )


def test_remove_product_quantity_from_open_sale(client, auth_tokens, role, open_sale):
    # choose the first product in "open_sale"
    sale_product = open_sale["lines"][0]
    prev_product_sample_qty = client.get(
        BASE_URL + f"/products/{sale_product['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()["quantity"]

    # completely remove the product from "open_sale"
    product_sample_removed_amount = sale_product["quantity"]
    delete_resp = client.delete(
        BASE_URL
        + f"/sales/{open_sale['id']}/items?barcode={sale_product['product_barcode']}&amount={product_sample_removed_amount}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 202
    assert delete_resp.json()["success"]

    # ensure that the inventory has been restocked by the correct amount
    post_stocked_product_sample = client.get(
        BASE_URL + f"/products/{sale_product['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()

    assert (
        post_stocked_product_sample["quantity"]
        == prev_product_sample_qty + product_sample_removed_amount
    )

    # ensure that the product has been removed from the sale
    updated_open_sale = client.get(
        BASE_URL + f"/sales/{open_sale['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()
    assert len(updated_open_sale["lines"]) == 0


def test_remove_product_quantity_from_open_sale_unauthenticated(client, open_sale):
    sale_product = open_sale["lines"][0]

    product_sample_removed_amount = 1
    delete_resp = client.delete(
        BASE_URL
        + f"/sales/{open_sale['id']}/items?barcode={sale_product['product_barcode']}&amount={product_sample_removed_amount}",
    )
    assert delete_resp.status_code == 401


def test_remove_product_invalid_quantity_from_open_sale(
    client, auth_tokens, role, open_sale
):
    sale_product = open_sale["lines"][0]

    product_sample_removed_amount = int(sale_product["quantity"]) + 1
    delete_resp = client.delete(
        BASE_URL
        + f"/sales/{open_sale['id']}/items?barcode={sale_product['product_barcode']}&amount={product_sample_removed_amount}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 400


def test_remove_product_invalid_sale_id_from_open_sale(
    client, auth_tokens, role, open_sale
):
    sale_product = open_sale["lines"][0]

    invalid_sale_id = "invalid_sale_id"
    delete_resp = client.delete(
        BASE_URL
        + f"/sales/{invalid_sale_id}/items?barcode={sale_product['product_barcode']}&amount=2",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 400


def test_remove_product_from_nonexistent_sale(client, auth_tokens, role, open_sale):
    sale_product = open_sale["lines"][0]

    nonexistent_sale_id = int(open_sale["id"]) + 1
    delete_resp = client.delete(
        BASE_URL
        + f"/sales/{nonexistent_sale_id}/items?barcode={sale_product['product_barcode']}&amount=2",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 404


def test_remove_product_not_found_from_open_sale(client, auth_tokens, role, open_sale):
    sale_product = open_sale["lines"][0]
    nonexistent_product_barcode = int(sale_product["product_barcode"]) + 1
    delete_resp = client.delete(
        BASE_URL
        + f"/sales/{open_sale['id']}/items?barcode={nonexistent_product_barcode}&amount=2",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 404


def test_reduce_product_quantity_from_pending_sale(
    client, auth_tokens, role, pending_sale
):
    sale_product = pending_sale["lines"][0]

    product_sample_removed_amount = 1
    delete_resp = client.delete(
        BASE_URL
        + f"/sales/{pending_sale['id']}/items?barcode={sale_product['product_barcode']}&amount={product_sample_removed_amount}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 420


def test_reduce_product_quantity_from_closed_sale(
    client, auth_tokens, role, closed_sale
):
    sale_product = closed_sale["lines"][0]

    product_sample_removed_amount = 1
    delete_resp = client.delete(
        BASE_URL
        + f"/sales/{closed_sale['id']}/items?barcode={sale_product['product_barcode']}&amount={product_sample_removed_amount}",
        headers=auth_header(auth_tokens, role),
    )
    assert delete_resp.status_code == 420


# -------------------------------------
# APPLY A DISCOUNT TO THE ENTIRE SALE
# -------------------------------------


def test_apply_discount_to_open_sale(client, auth_tokens, role, open_sale):
    applied_discount_rate = 0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{open_sale['id']}/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 200
    assert discount_resp.json()["success"]

    updated_open_sale = client.get(
        BASE_URL + f"/sales/{open_sale['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()
    updated_open_sale["discount_rate"] = applied_discount_rate


def test_apply_discount_to_invalid_sale_id(client, auth_tokens, role):
    invalid_sale_id = "1234sale"
    applied_discount_rate = 0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{invalid_sale_id}/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 400


def test_apply_invalid_discount_to_open_sale(client, auth_tokens, role, open_sale):
    applied_discount_rate = -0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{open_sale['id']}/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 400

    updated_open_sale = client.get(
        BASE_URL + f"/sales/{open_sale['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()
    assert updated_open_sale["discount_rate"] == open_sale["discount_rate"]


def test_apply_discount_unauthenticated(client, auth_tokens, role, open_sale):
    applied_discount_rate = -0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{open_sale['id']}/discount?discount_rate={applied_discount_rate}",
    )
    assert discount_resp.status_code == 401

    updated_open_sale = client.get(
        BASE_URL + f"/sales/{open_sale['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()
    assert updated_open_sale["discount_rate"] == open_sale["discount_rate"]


def test_apply_discount_to_nonexistent_sale(client, auth_tokens, role, open_sale):
    nonexistent_sale_id = int(open_sale["id"]) + 1
    applied_discount_rate = 0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{nonexistent_sale_id}/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 404


def test_apply_discount_to_pending_sale(client, auth_tokens, role, pending_sale):
    applied_discount_rate = 0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{pending_sale['id']}/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 420


def test_apply_discount_to_closed_sale(client, auth_tokens, role, closed_sale):
    applied_discount_rate = 0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{closed_sale['id']}/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 420


# ---------------------------------------------------
# APPLY A DISCOUNT TO A SPECIFIC PRODUCT IN A SALE
# ---------------------------------------------------


def test_apply_discount_to_product_in_open_sale(client, auth_tokens, role, open_sale):
    applied_discount_rate = 0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{open_sale['id']}/items/{open_sale['lines'][0]['product_barcode']}/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 200

    updated_open_sale = client.get(
        BASE_URL + f"/sales/{open_sale['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()
    assert updated_open_sale["lines"][0]["discount_rate"] == applied_discount_rate


def test_apply_discount_to_product_in_invalid_sale(client, auth_tokens, role):
    applied_discount_rate = 0.1
    invalid_sale_id = "1234sale"
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{invalid_sale_id}/items/1/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 400


def test_apply_invalid_discount_to_product_in_open_sale(
    client, auth_tokens, role, open_sale
):
    applied_discount_rate = -0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{open_sale['id']}/items/{open_sale['lines'][0]['product_barcode']}/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 400

    updated_open_sale = client.get(
        BASE_URL + f"/sales/{open_sale['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()
    assert (
        updated_open_sale["lines"][0]["discount_rate"]
        == open_sale["lines"][0]["discount_rate"]
    )


def test_apply_discount_to_product_in_open_sale_unauthenticated(
    client, auth_tokens, role, open_sale
):
    applied_discount_rate = 0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{open_sale['id']}/items/{open_sale['lines'][0]['product_barcode']}/discount?discount_rate={applied_discount_rate}",
    )
    assert discount_resp.status_code == 401

    updated_open_sale = client.get(
        BASE_URL + f"/sales/{open_sale['id']}",
        headers=auth_header(auth_tokens, role),
    ).json()
    assert (
        updated_open_sale["lines"][0]["discount_rate"]
        == open_sale["lines"][0]["discount_rate"]
    )


def test_apply_discount_to_product_in_nonexistent_sale(
    client, auth_tokens, role, open_sale
):
    applied_discount_rate = 0.1
    nonexistent_sale_id = int(open_sale["id"]) + 1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{nonexistent_sale_id}/items/{open_sale['lines'][0]['product_barcode']}/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 404


def test_apply_discount_to_product_to_pending_sale(
    client, auth_tokens, role, pending_sale
):
    applied_discount_rate = 0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{pending_sale['id']}/items/{pending_sale['lines'][0]['product_barcode']}/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 420


def test_apply_discount_to_product_to_closed_sale(
    client, auth_tokens, role, closed_sale
):
    applied_discount_rate = 0.1
    discount_resp = client.patch(
        BASE_URL
        + f"/sales/{closed_sale['id']}/items/{closed_sale['lines'][0]['product_barcode']}/discount?discount_rate={applied_discount_rate}",
        headers=auth_header(auth_tokens, role),
    )
    assert discount_resp.status_code == 420


# --------------------------
# CLOSE A SALE TRANSACTION
# --------------------------


def test_close_open_sale_transaction(client, auth_tokens, role, open_sale):
    close_resp = client.patch(
        BASE_URL + f"/sales/{open_sale['id']}/close",
        headers=auth_header(auth_tokens, role),
    )
    assert close_resp.status_code == 200

    get_resp = client.get(
        BASE_URL + f"/sales/{open_sale['id']}",
        headers=auth_header(auth_tokens, role),
    )
    pending_sale = get_resp.json()
    pending_sale["status"] = "PENDING"


def test_close_open_empty_sale_transaction(client, auth_tokens, role, open_empty_sale):
    close_resp = client.patch(
        BASE_URL + f"/sales/{open_empty_sale['id']}/close",
        headers=auth_header(auth_tokens, role),
    )
    assert close_resp.status_code == 200

    get_resp = client.get(
        BASE_URL + f"/sales/{open_empty_sale['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert get_resp.status_code == 404


def test_close_sale_transaction_invalid_id(client, auth_tokens, role):
    invalid_id = "123invalid_id"
    close_resp = client.patch(
        BASE_URL + f"/sales/{invalid_id}/close",
        headers=auth_header(auth_tokens, role),
    )
    assert close_resp.status_code == 400


def test_close_sale_transaction_empty_id(client, auth_tokens, role):
    empty_id = None
    close_resp = client.patch(
        BASE_URL + f"/sales/{empty_id}/close",
        headers=auth_header(auth_tokens, role),
    )
    assert close_resp.status_code == 400


def test_close_open_sale_unauthenticated(client, open_sale):
    close_resp = client.patch(
        BASE_URL + f"/sales/{open_sale['id']}/close",
    )
    assert close_resp.status_code == 401


def test_close_nonexistent_sale(client, auth_tokens, role, open_sale):
    nonexistent_sale_id = int(open_sale["id"]) + 1
    close_resp = client.patch(
        BASE_URL + f"/sales/{nonexistent_sale_id}/close",
        headers=auth_header(auth_tokens, role),
    )
    assert close_resp.status_code == 404


def test_close_pending_sale(client, auth_tokens, role, pending_sale):
    close_resp = client.patch(
        BASE_URL + f"/sales/{pending_sale['id']}/close",
        headers=auth_header(auth_tokens, role),
    )
    assert close_resp.status_code == 420


def test_close_already_closed_sale(client, auth_tokens, role, closed_sale):
    close_resp = client.patch(
        BASE_URL + f"/sales/{closed_sale['id']}/close",
        headers=auth_header(auth_tokens, role),
    )
    assert close_resp.status_code == 420


# --------------------
# PAY A SALE IN CASH
# --------------------


def test_pay_pending_sale(client, auth_tokens, role, pending_sale):
    balance_pre_payment = client.get(
        BASE_URL + "/balance/",
        headers=auth_header(auth_tokens, "admin"),
    ).json()["balance"]

    cash_amount = 50.0
    pay_resp = client.patch(
        BASE_URL + f"/sales/{pending_sale['id']}/pay?cash_amount={cash_amount}",
        headers=auth_header(auth_tokens, role),
    )
    assert pay_resp.status_code == 200
    change = pay_resp.json()["change"]
    sale_total_amount = 0
    for product in pending_sale["lines"]:
        sale_total_amount += float(product["quantity"]) * float(
            product["price_per_unit"]
        ) - (float(product["price_per_unit"]) * product["discount_rate"])

    assert change == cash_amount - sale_total_amount

    balance_post_payment = client.get(
        BASE_URL + "/balance/",
        headers=auth_header(auth_tokens, "admin"),
    ).json()["balance"]

    assert balance_post_payment == balance_pre_payment + sale_total_amount


def test_pay_invalid_id_sale(client, auth_tokens, role):
    invalid_id = "123invalid234"
    pay_resp = client.patch(
        BASE_URL + f"/sales/{invalid_id}/pay?cash_amount=50",
        headers=auth_header(auth_tokens, role),
    )
    assert pay_resp.status_code == 400


def test_pay_missing_id_sale(client, auth_tokens, role):
    missing_id = None
    pay_resp = client.patch(
        BASE_URL + f"/sales/{missing_id}/pay?cash_amount=50",
        headers=auth_header(auth_tokens, role),
    )
    assert pay_resp.status_code == 400


def test_pay_sale_unauthenticated(client, auth_tokens, role, pending_sale):
    pay_resp = client.patch(
        BASE_URL + f"/sales/{pending_sale['id']}/pay?cash_amount=50",
    )
    assert pay_resp.status_code == 401
    get_resp = client.get(
        BASE_URL + f"/sales/{pending_sale['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert get_resp.json()["status"] == "PENDING"


def test_pay_sale_not_found(client, auth_tokens, role, pending_sale):
    nonexistent_sale_id = int(pending_sale["id"]) + 1
    pay_resp = client.patch(
        BASE_URL + f"/sales/{nonexistent_sale_id}/pay?cash_amount=50",
        headers=auth_header(auth_tokens, role),
    )
    pay_resp.status_code = 404


def test_pay_open_sale(client, auth_tokens, role, open_sale):
    pay_resp = client.patch(
        BASE_URL + f"/sales/{open_sale['id']}/pay?cash_amount=50",
        headers=auth_header(auth_tokens, role),
    )
    pay_resp.status_code = 420
    get_resp = client.get(
        BASE_URL + f"/sales/{open_sale['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert get_resp.json()["status"] == "OPEN"


def test_pay_closed_sale(client, auth_tokens, role, closed_sale):
    pay_resp = client.patch(
        BASE_URL + f"/sales/{closed_sale['id']}/pay?cash_amount=50",
        headers=auth_header(auth_tokens, role),
    )
    pay_resp.status_code = 420
    get_resp = client.get(
        BASE_URL + f"/sales/{closed_sale['id']}",
        headers=auth_header(auth_tokens, role),
    )
    assert get_resp.json()["status"] == "PAID"


# ------------------------------------
# COMPUTE LOYALTY POINTS FOR A SALE
# ------------------------------------


def test_compute_points_sale(client, auth_tokens, role, closed_sale):
    points_resp = client.get(
        BASE_URL + f"/sales/{closed_sale['id']}/points",
        headers=auth_header(auth_tokens, role),
    )
    assert points_resp.status_code == 200

    computed_points = points_resp.json()["points"]
    expected_points = 0
    for product in closed_sale["lines"]:
        expected_points += float(product["quantity"]) * float(product["price_per_unit"])
    expected_points = round(expected_points / 10.0)

    assert computed_points == expected_points


def test_compute_points_invalid_id_sale(client, auth_tokens, role):
    invalid_id = "123invalid234"
    pay_resp = client.get(
        BASE_URL + f"/sales/{invalid_id}/points",
        headers=auth_header(auth_tokens, role),
    )
    assert pay_resp.status_code == 400


def test_compute_points_missing_id_sale(client, auth_tokens, role):
    missing_id = None
    pay_resp = client.get(
        BASE_URL + f"/sales/{missing_id}/points",
        headers=auth_header(auth_tokens, role),
    )
    assert pay_resp.status_code == 400


def test_compute_points_sale_unauthenticated(client, closed_sale):
    pay_resp = client.get(
        BASE_URL + f"/sales/{closed_sale['id']}/points",
    )
    assert pay_resp.status_code == 401


def test_compute_points_sale_not_found(client, auth_tokens, role, closed_sale):
    nonexistent_sale_id = int(closed_sale["id"]) + 1
    pay_resp = client.get(
        BASE_URL + f"/sales/{nonexistent_sale_id}/points",
        headers=auth_header(auth_tokens, role),
    )
    pay_resp.status_code = 404


def test_compute_points_open_sale(client, auth_tokens, role, open_sale):
    pay_resp = client.get(
        BASE_URL + f"/sales/{open_sale['id']}/points",
        headers=auth_header(auth_tokens, role),
    )
    pay_resp.status_code = 420


def test_compute_points_pending_sale(client, auth_tokens, role, pending_sale):
    pay_resp = client.get(
        BASE_URL + f"/sales/{pending_sale['id']}/points",
        headers=auth_header(auth_tokens, role),
    )
    pay_resp.status_code = 420
