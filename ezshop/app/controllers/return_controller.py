import datetime
from typing import List

from app.models.DAO.product_type_dao import ProductTypeDAO
from app.models.DAO.return_dao import ReturnDAO, ReturnLineDAO
from app.models.DAO.sale_dao import SaleDAO
from app.models.DTO.return_dto import ReturnDTO
from app.models.errors.bad_request import BadRequestError
from app.models.errors.invalid_state_error import InvalidStateError
from app.models.errors.notfound_error import NotFoundError
from app.models.return_status import ReturnStatus
from app.models.sale_status import SaleStatus
from app.repositories.balance_repository import BalanceRepository
from app.repositories.product_type_repository import ProductTypeRepository
from app.repositories.return_repository import ReturnRepository
from app.repositories.sale_repository import SaleRepository
from app.services.return_mapper_service import return_dao_to_dto


class ReturnController:
    def __init__(self):
        self.repo = ReturnRepository()
        self.sale_repo = SaleRepository()
        self.product_repo = ProductTypeRepository()
        self.balance_repo = BalanceRepository()

    async def create_return(self, sale_id: str) -> ReturnDTO:
        if not sale_id.isnumeric() or int(sale_id) <= 0:
            raise BadRequestError("Invalid sale id.")
        sale = await self.sale_repo.get_sale_by_id(int(sale_id))
        if not sale:
            raise NotFoundError(f"Sale {sale_id} not found.")
        if sale.status != SaleStatus.PAID:
            raise InvalidStateError("Cannot return an unpaid sale.")
        created_dao = await self.repo.create_return(int(sale_id))
        return return_dao_to_dto(created_dao)

    async def get_all_returns(self) -> List[ReturnDTO]:
        returns = await self.repo.get_all_returns()
        return [return_dao_to_dto(refund) for refund in returns]

    async def get_return_by_id(self, return_id: str) -> ReturnDTO:
        if not return_id.isnumeric() or int(return_id) <= 0:
            raise BadRequestError("Invalid return id.")
        return_dao = await self.repo.get_return_by_id(int(return_id))
        if not return_dao:
            raise NotFoundError(f"Return {return_id} not found.")
        return return_dao_to_dto(return_dao)

    async def delete_return(self, return_id: str) -> None:
        if not return_id.isnumeric() or int(return_id) <= 0:
            raise BadRequestError("Invalid return id.")
        refund = await self.repo.get_return_by_id(int(return_id))
        if not refund:
            raise NotFoundError(f"Return {return_id} not found.")
        if refund.status == ReturnStatus.REIMBURSED:
            raise InvalidStateError("Cannot delete a return that has already been reimbursed.")
        for line in refund.lines:
            product = await self.product_repo.get_product_type_by_barcode(line.product_barcode)
            if refund.status == ReturnStatus.CLOSED:
                await self.product_repo.update_product_type_quantity(product, -line.quantity)
            await self.product_repo.decrement_usage_count(line.product_barcode)
        await self.repo.delete_return(refund)

    async def get_returns_by_sale_id(self, sale_id: str) -> List[ReturnDTO]:
        if not sale_id.isnumeric() or int(sale_id) <= 0:
            raise BadRequestError("Invalid return id.")
        returns = await self.repo.get_returns_by_sale_id(int(sale_id))
        return [return_dao_to_dto(refund) for refund in returns]

    async def valid_return(self, return_id: str, status: ReturnStatus) -> ReturnDAO:
        if not return_id.isnumeric() or int(return_id) <= 0:
            raise BadRequestError("Invalid return id.")
        refund = await self.repo.get_return_by_id(int(return_id))
        if not refund:
            raise NotFoundError(f"Return {return_id} not found.")
        if refund.status != status:
            raise InvalidStateError("Cannot modify return.")
        return refund

    async def add_product_to_return(self, return_id: str, product_barcode: str, amount: str) -> bool:
        if len(product_barcode)<12 or len(product_barcode)>14:
            raise BadRequestError("Invalid barcode, it should be between 12 and 14 characters.")
        refund = await self.valid_return(return_id, ReturnStatus.OPEN)
        if not amount.isnumeric() or int(amount) <= 0:
            raise BadRequestError("Invalid quantity.")
        sale = await self.sale_repo.get_sale_by_id(refund.sale_id)
        quantity = 0
        for line in sale.lines:
            if line.product_barcode == product_barcode:
                quantity = line.quantity
        if int(amount) > quantity:
            raise BadRequestError("Invalid quantity.")
        product = await self.product_repo.get_product_type_by_barcode(product_barcode)
        already_in_return = await product_already_in_return(refund, product)
        await add_product_to_return(refund, product, int(amount))
        if not already_in_return:
            await self.product_repo.increment_usage_count(product_barcode)
        await self.repo.update_return(refund)
        return True

    async def delete_line(self, return_id: str, product_barcode: str, amount: str) -> bool:
        if len(product_barcode)<12 or len(product_barcode)>14:
            raise BadRequestError("Invalid barcode, it should be between 12 and 14 characters.")
        refund = await self.valid_return(return_id, ReturnStatus.OPEN)
        if not amount.isnumeric() or int(amount) <= 0:
            raise BadRequestError("Invalid quantity.")
        success = await self.delete_return_line(refund, product_barcode, int(amount))
        if not success:
            raise NotFoundError(f"Product {product_barcode} not found in return {return_id}")
        await self.repo.update_return(refund)
        return True

    async def close_return(self, return_id: str) -> bool:
        refund = await self.valid_return(return_id, ReturnStatus.OPEN)
        if not refund.lines:
            await self.repo.delete_return(refund)
        else:
            refund.status = ReturnStatus.CLOSED
            refund.closed_at = datetime.datetime.now()
            await self.repo.update_return(refund)
            for line in refund.lines:
                product = await self.product_repo.get_product_type_by_barcode(line.product_barcode)
                await self.product_repo.update_product_type_quantity(product, line.quantity)
        return True

    async def reimburse_return(self, return_id: str) -> float:
        refund = await self.valid_return(return_id, ReturnStatus.CLOSED)
        sale = await self.sale_repo.get_sale_by_id(refund.sale_id)
        refund_amount = await refund_sale(refund, sale)
        await self.repo.update_return(refund)
        await self.balance_repo.decrease_balance(refund_amount)
        return refund_amount

    async def delete_return_line(self, refund: ReturnDAO, product_barcode: str, amount: int) -> bool:
        if len(product_barcode) < 12 or len(product_barcode) > 14:
            raise BadRequestError("Invalid barcode, it should be between 12 and 14 characters.")
        for return_line in refund.lines:
            if return_line.product_barcode == product_barcode:
                return_line.quantity -= amount
                if return_line.quantity <= 0:
                    await self.product_repo.decrement_usage_count(product_barcode)
                    refund.lines.remove(return_line)
                return True
        return False

async def product_already_in_return(refund: ReturnDAO, product: ProductTypeDAO)->bool:
    for return_line in refund.lines:
        if return_line.product_barcode == product.barcode:
            return True
    return False

async def add_product_to_return(refund: ReturnDAO, product: ProductTypeDAO, quantity: int)->None:
    for return_line in refund.lines:
        if return_line.product_barcode == product.barcode:
            return_line.quantity += quantity
            return
    return_line_dao = ReturnLineDAO(product_barcode=product.barcode, quantity=quantity, price_per_unit=product.price_per_unit)
    refund.lines.append(return_line_dao)

#Used sale as well to access the sale and line discount rates
async def refund_sale(refund: ReturnDAO, sale: SaleDAO) -> float:
    total = 0
    for return_line in refund.lines:
        for sale_line in sale.lines:
            if return_line.product_barcode == sale_line.product_barcode:
                partial = return_line.price_per_unit * return_line.quantity * (1 - sale_line.discount_rate)
                total += partial
    total *= (1 - sale.discount_rate)
    refund.status = ReturnStatus.REIMBURSED
    return total