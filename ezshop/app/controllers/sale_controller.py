import datetime
from typing import List

from app.models.DAO.product_type_dao import ProductTypeDAO
from app.models.DAO.sale_dao import SaleDAO, SaleLineDAO
from app.models.DTO.sale_dto import SaleDTO
from app.models.errors.bad_request import BadRequestError
from app.models.errors.invalid_state_error import InvalidStateError
from app.models.errors.notfound_error import NotFoundError
from app.models.sale_status import SaleStatus
from app.repositories.balance_repository import BalanceRepository
from app.repositories.product_type_repository import ProductTypeRepository
from app.repositories.sale_repository import SaleRepository
from app.services.sale_mapper_service import sale_dao_to_dto
from app.utils import is_float


class SaleController:
    def __init__(self):
        self.repo = SaleRepository()
        self.product_repo = ProductTypeRepository()
        self.balance_repo = BalanceRepository()

    async def create_sale(self) -> SaleDTO:
        created_dao = await self.repo.create_sale()
        return sale_dao_to_dto(created_dao)

    async def get_all_sales(self) -> List[SaleDTO]:
        sales = await self.repo.get_all_sales()
        return [sale_dao_to_dto(sale) for sale in sales]

    async def get_sale_by_id(self, sale_id: str) -> SaleDTO:
        if not sale_id.isnumeric() or int(sale_id) <= 0:
            raise BadRequestError("Invalid sale id.")
        sale = await self.repo.get_sale_by_id(int(sale_id))
        if not sale:
            raise NotFoundError(f"Sale {sale_id} not found.")
        return sale_dao_to_dto(sale)

    async def delete_sale(self, sale_id: str) -> None:
        if not sale_id.isnumeric() or int(sale_id) <= 0:
            raise BadRequestError("Invalid sale id.")
        sale = await self.repo.get_sale_by_id(int(sale_id))
        if not sale:
            raise NotFoundError(f"Sale {sale_id} not found.")
        if sale.status == SaleStatus.PAID:
            raise InvalidStateError("Cannot delete a sale that has already been paid.")
        await self.repo.delete_sale(sale)
        for line in sale.lines:
            product = await self.product_repo.get_product_type_by_barcode(line.product_barcode)
            await self.product_repo.update_product_type_quantity(product, line.quantity)
            await self.product_repo.decrement_usage_count(line.product_barcode)

    async def valid_sale_discount(self, sale_id: str, discount_rate: str) -> SaleDAO:
        if not sale_id.isnumeric() or int(sale_id) <= 0:
            raise BadRequestError("Invalid sale id.")
        if not is_float(discount_rate) or not 0 <= float(discount_rate) < 1:
            raise BadRequestError("Invalid discount rate. Must be between 0 and 1.")
        sale = await self.repo.get_sale_by_id(int(sale_id))
        if not sale:
            raise NotFoundError(f"Sale {sale_id} not found.")
        if sale.status != SaleStatus.OPEN:
            raise InvalidStateError("Cannot modify sale.")
        return sale

    async def discount_sale(self, sale_id: str, discount_rate: str) -> bool:
        sale = await self.valid_sale_discount(sale_id, discount_rate)
        sale.discount_rate = float(discount_rate)
        await self.repo.update_sale(sale)
        return True

    async def close_sale(self, sale_id: str) -> bool:
        if not sale_id.isnumeric() or int(sale_id) <= 0:
            raise BadRequestError("Invalid sale id.")
        sale = await self.repo.get_sale_by_id(int(sale_id))
        if not sale:
            raise NotFoundError(f"Sale {sale_id} not found.")
        if sale.status != SaleStatus.OPEN:
            raise InvalidStateError("Cannot modify sale.")
        if not sale.lines:
            await self.repo.delete_sale(sale)
        else:
            sale.status = SaleStatus.PENDING
            sale.closed_at = datetime.datetime.now()
            await self.repo.update_sale(sale)
        return True

    async def pay_sale(self, sale_id: str, cash_amount: str) -> float:
        if not sale_id.isnumeric() or int(sale_id) <= 0:
            raise BadRequestError("Invalid sale id.")
        if not is_float(cash_amount) or float(cash_amount) <= 0:
            raise BadRequestError("Invalid cash amount.")
        sale = await self.repo.get_sale_by_id(int(sale_id))
        if not sale:
            raise NotFoundError(f"Sale {sale_id} not found.")
        if sale.status != SaleStatus.PENDING:
            raise InvalidStateError("Cannot modify sale.")
        change = await compute_change_and_pay(sale, float(cash_amount))
        if change < 0:
            raise BadRequestError("Cannot pay sale. Insufficient cash amount.")
        await self.repo.update_sale(sale)
        profit = float(cash_amount) - change
        await self.balance_repo.increase_balance(profit)
        return change

    async def compute_loyalty_points(self, sale_id: str) -> int:
        if not sale_id.isnumeric() or int(sale_id) <= 0:
            raise BadRequestError("Invalid sale id.")
        sale = await self.repo.get_sale_by_id(int(sale_id))
        if not sale:
            raise NotFoundError(f"Sale {sale_id} not found.")
        if sale.status != SaleStatus.PAID:
            raise InvalidStateError("Cannot compute loyalty points for an unpaid sale.")
        points = await compute_sale_loyalty_points(sale)
        return points

    async def valid_sale_details(self, sale_id: str, amount: str) -> SaleDAO:
        if not sale_id.isnumeric() or int(sale_id) <= 0:
            raise BadRequestError("Invalid sale id.")
        if not amount.isnumeric() or int(amount) <= 0:
            raise BadRequestError("Invalid quantity.")
        sale = await self.repo.get_sale_by_id(int(sale_id))
        if not sale:
            raise NotFoundError(f"Sale {sale_id} not found.")
        if sale.status != SaleStatus.OPEN:
            raise InvalidStateError("Cannot modify sale.")
        return sale

    async def add_product_to_sale(self, sale_id: str, product_barcode: str, amount: str) -> bool:
        sale = await self.valid_sale_details(sale_id, amount)
        if len(product_barcode)<12 or len(product_barcode)>14:
            raise BadRequestError("Invalid barcode, it should be between 12 and 14 characters.")
        product = await self.product_repo.get_product_type_by_barcode(product_barcode)
        if not product:
            raise NotFoundError(f"Product {product_barcode} not found.")
        if int(amount) > product.quantity:
            raise BadRequestError("Invalid quantity.")
        already_in_sale = await product_already_in_sale(sale, product)
        await add_product(sale, product, int(amount))
        await self.product_repo.update_product_type_quantity(product, -int(amount))
        if not already_in_sale:
            await self.product_repo.increment_usage_count(product_barcode)
        await self.repo.update_sale(sale)
        return True

    async def discount_product(self, sale_id: str, product_barcode: str, discount_rate: str) -> bool:
        if len(product_barcode)<12 or len(product_barcode)>14:
            raise BadRequestError("Invalid barcode, it should be between 12 and 14 characters.")
        sale = await self.valid_sale_discount(sale_id, discount_rate)
        success = await discount_line(sale, product_barcode, float(discount_rate))
        if not success:
            raise NotFoundError(f"Product {product_barcode} not found in sale {sale_id}.")
        await self.repo.update_sale(sale)
        return True

    async def delete_product(self, sale_id: str, product_barcode: str, amount: str) -> bool:
        if len(product_barcode)<12 or len(product_barcode)>14:
            raise BadRequestError("Invalid barcode, it should be between 12 and 14 characters.")
        sale = await self.valid_sale_details(sale_id, amount)
        success = await self.delete_line(sale, product_barcode, int(amount))
        if not success:
            raise NotFoundError(f"Product {product_barcode} not found in sale {sale_id}")
        await self.repo.update_sale(sale)
        product = await self.product_repo.get_product_type_by_barcode(product_barcode)
        await self.product_repo.update_product_type_quantity(product, int(amount))
        return True

    async def delete_line(self, sale: SaleDAO, product_barcode: str, amount: int) -> bool:
        for sale_line in sale.lines:
            if sale_line.product_barcode == product_barcode:
                if sale_line.quantity < amount:
                    raise BadRequestError("Invalid quantity.")
                sale_line.quantity -= amount
                if sale_line.quantity <= 0:
                    sale.lines.remove(sale_line)
                    await self.product_repo.decrement_usage_count(product_barcode)
                return True
        return False


async def compute_change_and_pay(sale: SaleDAO, cash_amount: float) -> float:
    total = 0
    for sale_line in sale.lines:
        partial = sale_line.price_per_unit * sale_line.quantity * (1 - sale_line.discount_rate)
        total += partial
    total *= (1 - sale.discount_rate)
    change = cash_amount - total
    if change >= 0:
        sale.status = SaleStatus.PAID
    return change

async def compute_sale_loyalty_points(sale: SaleDAO) -> int:
    points = 0
    for sale_line in sale.lines:
        points += sale_line.price_per_unit * sale_line.quantity / 10
    return round(points)

async def add_product(sale: SaleDAO, product: ProductTypeDAO, quantity: int)->None:
    for sale_line in sale.lines:
        if sale_line.product_barcode == product.barcode:
            sale_line.quantity += quantity
            return
    sale_line_dao = SaleLineDAO(product_barcode=product.barcode, quantity=quantity, price_per_unit=product.price_per_unit, discount_rate=0.0, sale_id=sale.id)
    sale.lines.append(sale_line_dao)

async def product_already_in_sale(sale: SaleDAO, product: ProductTypeDAO)->bool:
    for sale_line in sale.lines:
        if sale_line.product_barcode == product.barcode:
            return True
    return False

async def discount_line(sale: SaleDAO, product_barcode: str, discount_rate: float) -> bool:
    for sale_line in sale.lines:
        if sale_line.product_barcode == product_barcode:
            sale_line.discount_rate = discount_rate
            return True
    return False
