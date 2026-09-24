from typing import List

from fastapi import APIRouter, Depends, Response, status

from app.config.config import ROUTES
from app.controllers.sale_controller import SaleController
from app.middleware.auth_middleware import authenticate_user
from app.models.DTO.sale_dto import SaleDTO
from app.models.user_type import UserType

router = APIRouter(prefix=ROUTES["V1_SALES"], tags=["Sales"])
controller = SaleController()


@router.post(
    "/",
    response_model=SaleDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            authenticate_user(
                [UserType.Administrator, UserType.Cashier, UserType.ShopManager]
            )
        )
    ],
)
async def create_sale():
    return await controller.create_sale()


@router.get(
    "/",
    response_model=List[SaleDTO],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            authenticate_user(
                [UserType.Administrator, UserType.Cashier, UserType.ShopManager]
            )
        )
    ],
)
async def get_all_sales():
    return await controller.get_all_sales()


@router.get(
    "/{sale_id}",
    response_model=SaleDTO,
    dependencies=[
        Depends(
            authenticate_user(
                [UserType.Administrator, UserType.Cashier, UserType.ShopManager]
            )
        )
    ],
)
async def get_sale_by_id(sale_id: str):
    return await controller.get_sale_by_id(sale_id)


@router.delete(
    "/{sale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            authenticate_user(
                [UserType.Administrator, UserType.Cashier, UserType.ShopManager]
            )
        )
    ],
)
async def delete_sale(sale_id: str):
    await controller.delete_sale(sale_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{sale_id}/discount",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            authenticate_user(
                [UserType.Administrator, UserType.Cashier, UserType.ShopManager]
            )
        )
    ],
)
async def discount_sale(sale_id: str, discount_rate: str):
    await controller.discount_sale(sale_id, discount_rate)
    return {"success": True}


@router.patch(
    "/{sale_id}/close",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            authenticate_user(
                [UserType.Administrator, UserType.Cashier, UserType.ShopManager]
            )
        )
    ],
)
async def close_sale(sale_id: str):
    await controller.close_sale(sale_id)
    return {"success": True}


@router.patch(
    "/{sale_id}/pay",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            authenticate_user(
                [UserType.Administrator, UserType.Cashier, UserType.ShopManager]
            )
        )
    ],
)
async def pay_sale(sale_id: str, cash_amount: str):
    change = await controller.pay_sale(sale_id, cash_amount)
    return {"change": change}


@router.get(
    "/{sale_id}/points",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            authenticate_user(
                [UserType.Administrator, UserType.Cashier, UserType.ShopManager]
            )
        )
    ],
)
async def compute_loyalty_points(sale_id: str):
    points = await controller.compute_loyalty_points(sale_id)
    return {"points": points}


@router.post(
    "/{sale_id}/items",
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            authenticate_user(
                [UserType.Administrator, UserType.Cashier, UserType.ShopManager]
            )
        )
    ],
)
async def add_product_to_sale(sale_id: str, barcode: str, amount: str):
    await controller.add_product_to_sale(sale_id, barcode, amount)
    return {"success": True}


@router.patch(
    "/{sale_id}/items/{product_barcode}/discount",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            authenticate_user(
                [UserType.Administrator, UserType.Cashier, UserType.ShopManager]
            )
        )
    ],
)
async def discount_line(sale_id: str, product_barcode: str, discount_rate: str):
    await controller.discount_product(sale_id, product_barcode, discount_rate)
    return {"success": True}


@router.delete(
    "/{sale_id}/items",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[
        Depends(
            authenticate_user(
                [UserType.Administrator, UserType.Cashier, UserType.ShopManager]
            )
        )
    ],
)
async def delete_line(sale_id: str, barcode: str, amount: str):
    await controller.delete_product(sale_id, barcode, amount)
    return {"success": True}

