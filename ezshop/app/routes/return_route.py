from typing import List

from fastapi import APIRouter, Depends, status, Response

from app.config.config import ROUTES
from app.controllers.return_controller import ReturnController
from app.middleware.auth_middleware import authenticate_user
from app.models.DTO.return_dto import ReturnDTO
from app.models.errors.bad_request import BadRequestError
from app.models.user_type import UserType

router = APIRouter(prefix=ROUTES['V1_RETURNS'], tags=["Returns"])
controller = ReturnController()
@router.post("/",
             response_model=ReturnDTO,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.Cashier, UserType.ShopManager]))])
async def create_return(sale_id: str):
    return await controller.create_return(sale_id)

@router.get("/",
             response_model=List[ReturnDTO],
             status_code=status.HTTP_200_OK,
             dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.Cashier, UserType.ShopManager]))])
async def get_all_returns():
    return await controller.get_all_returns()

@router.get("/{return_id}",
             response_model=ReturnDTO,
             dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.Cashier, UserType.ShopManager]))])
async def get_return_by_id(return_id: str):
    return await controller.get_return_by_id(return_id)

@router.delete("/{return_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.Cashier, UserType.ShopManager]))])
async def delete_return(return_id: str):
    await controller.delete_return(return_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/sale/{sale_id}",
             response_model=List[ReturnDTO],
             dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.Cashier, UserType.ShopManager]))])
async def get_return_by_id(sale_id: str):
    return await controller.get_returns_by_sale_id(sale_id)

@router.post("/{return_id}/items",
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.Cashier, UserType.ShopManager]))])
async def add_product_to_return(return_id: str, barcode: str, amount: str):
    await controller.add_product_to_return(return_id, barcode, amount)
    return {"success": True}

@router.delete("/{return_id}/items",
             status_code=status.HTTP_202_ACCEPTED,
             dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.Cashier, UserType.ShopManager]))])
async def delete_line(return_id: str, barcode: str, amount: str):
    await controller.delete_line(return_id, barcode, amount)
    return {"success": True}

@router.patch("/{return_id}/close",
             status_code=status.HTTP_200_OK,
             dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.Cashier, UserType.ShopManager]))])
async def close_return(return_id: str):
    await controller.close_return(return_id)
    return {"success": True}

@router.patch("/{return_id}/reimburse",
             status_code=status.HTTP_200_OK,
             dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))])
async def reimburse_return(return_id: str):
    refund_amount = await controller.reimburse_return(return_id)
    return {"refund_amount": refund_amount}