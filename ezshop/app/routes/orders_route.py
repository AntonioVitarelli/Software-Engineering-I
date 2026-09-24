from fastapi import APIRouter, Depends, status
from app.middleware.auth_middleware import authenticate_user
from app.controllers.orders_controller import OrderController
from app.models.user_type import UserType
from app.models.DTO.orders_dto import OrderDTO, OrderCreateDTO
from app.models.DTO.responses import BooleanResponse
from app.config.config import ROUTES

router = APIRouter(
    prefix=ROUTES["V1_ORDERS"],
    tags=["Orders"]
)
controller = OrderController()


# ---------------------------------------------------------
# CREATE ORDER (ISSUED)
# ---------------------------------------------------------
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=OrderDTO,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))],
)
async def issue_order(body: OrderCreateDTO):
    return await controller.create_order(body)


# ---------------------------------------------------------
# CREATE AND PAY ORDER (PAID)
# ---------------------------------------------------------
@router.post(
    "/payfor",
    status_code=status.HTTP_201_CREATED,
    response_model=OrderDTO,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))],
)
async def pay_order_for(body: OrderCreateDTO):
    return await controller.create_and_pay(body)


# ---------------------------------------------------------
# PAY EXISTING ORDER
# ---------------------------------------------------------
@router.patch(
    "/{order_id}/pay",
    status_code=status.HTTP_201_CREATED,
    response_model=BooleanResponse,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))],
)
async def pay_order(order_id: int):
    await controller.pay_order(order_id)
    return {"success": True}


# ---------------------------------------------------------
# RECORD ARRIVAL
# ---------------------------------------------------------
@router.patch(
    "/{order_id}/arrival",
    status_code=status.HTTP_201_CREATED,
    response_model=BooleanResponse,
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))],
)
async def record_arrival(order_id: int):

    await controller.record_arrival(order_id)
    return {"success": True}


# ---------------------------------------------------------
# LIST ORDERS
# ---------------------------------------------------------
@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[OrderDTO],
    dependencies=[Depends(authenticate_user([UserType.Administrator, UserType.ShopManager]))],
)
async def list_orders():
    return await controller.list_orders()
