from fastapi import APIRouter, Depends, Response, status

from app.config.config import ROUTES
from app.controllers.balance_controller import BalanceController
from app.middleware.auth_middleware import authenticate_user
from app.models.DTO.responses import BooleanResponse
from app.models.DTO.system_dto import SystemReponseDTO
from app.models.user_type import UserType

router = APIRouter(prefix=ROUTES["V1_BALANCE"], tags=["Accounting"])
controller = BalanceController()


@router.post(
    "/reset",
    status_code=status.HTTP_205_RESET_CONTENT,
    dependencies=[Depends(authenticate_user([UserType.Administrator]))],
    description="Resets the balance value to 0. "
    + "Accessible only by **Administrator** users.",
)
async def reset_balance():
    _ = await controller.reset_balance()
    return Response(status_code=status.HTTP_205_RESET_CONTENT)


@router.post(
    "/set",
    status_code=status.HTTP_201_CREATED,
    response_model=BooleanResponse,
    dependencies=[Depends(authenticate_user([UserType.Administrator]))],
    description="Sets the system balance to the provided amount. "
    + "Accessible only by **Administrator** users.",
)
async def set_balance(amount: float):
    _ = await controller.set_balance(amount)
    return BooleanResponse(success=True)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=SystemReponseDTO,
    dependencies=[Depends(authenticate_user([UserType.Administrator]))],
    description="Returns the current balance value of the system. "
    + "Accessible only by **Administrator** users.",
)
async def get_balance():
    return await controller.get_balance()
