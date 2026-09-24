from app.models.DTO.system_dto import SystemDTO
from app.models.errors.bad_request import BadRequestError
from app.models.errors.balance_error import BalanceError
from app.models.errors.internal_server_error import InternalServerError
from app.repositories.balance_repository import BalanceRepository
from app.services.mapper_service import systemdao_to_responsedto


class BalanceController:
    def __init__(self):
        self.repo = BalanceRepository()

    async def reset_balance(self) -> bool:
        success = await self.repo.reset_balance()
        if not success:
            raise InternalServerError("Internal server error during balance reset")

        return success

    async def set_balance(self, amount: float) -> bool:
        if amount < 0:
            raise BalanceError("The inserted amount cannot be negative.")

        success = await self.repo.set_balance(amount)
        if not success:
            raise InternalServerError("Internal server error during balance reset")

        return success

    async def increase_balance(self, amount: float) -> bool:
        if amount < 0:
            raise BadRequestError("The inserted amount cannot be negative.")

        success = await self.repo.increase_balance(amount)
        if not success:
            raise InternalServerError("Internal server error during balance reset")

        return success

    async def decrease_balance(self, amount: float) -> bool:
        if amount < 0:
            raise BadRequestError("The inserted amount cannot be negative.")

        success = await self.repo.decrease_balance(amount)
        if not success:
            raise InternalServerError("Internal server error during balance reset")

        return success

    async def get_balance(self) -> SystemDTO:
        dao = await self.repo.get_balance()
        return systemdao_to_responsedto(dao)
