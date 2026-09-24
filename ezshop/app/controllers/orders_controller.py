import re

from app.database.database import AsyncSessionLocal
from app.models.DAO.orders_dao import OrderStatus
from app.models.errors.bad_request import BadRequestError
from app.models.errors.balance_error import BalanceError
from app.models.errors.general_error import GeneralError
from app.models.errors.invalid_state_error import InvalidStateError
from app.models.errors.notfound_error import NotFoundError
from app.repositories.balance_repository import BalanceRepository
from app.repositories.orders_repository import OrderRepository
from app.repositories.product_type_repository import ProductTypeRepository
from app.services.mapper_service import (
    orderdao_to_responsedto,
)
from app.models.DTO.orders_dto import OrderDTO
from datetime import datetime

class OrderController:

    def __init__(self):
        self.repository = OrderRepository()

    # ---------------------------------------------------------
    # CREATE ORDER (ISSUED)
    # ---------------------------------------------------------
    async def create_order(self, dto: OrderDTO) -> OrderDTO:
        # 400
        if (
                not dto.product_barcode
                or not dto.product_barcode.isdigit()
                or len(dto.product_barcode) < 12
                or len(dto.product_barcode) > 14
                or dto.quantity <= 0
                or dto.price_per_unit <= 0
        ):            raise BadRequestError("Invalid barcode or quantity")

        # 404 prodotto
        async with AsyncSessionLocal() as session:
            product_repo = ProductTypeRepository(session)
            product = await product_repo.get_product_type_by_barcode(dto.product_barcode)
            if not product:
                raise NotFoundError("Product not found")

        order = await self.repository.create_order(
            dto.product_barcode,
            dto.quantity,
            dto.price_per_unit,
            OrderStatus.ISSUED,
            datetime.now()
        )

        async with AsyncSessionLocal() as session:
            product_repo = ProductTypeRepository(session)
            await product_repo.increment_usage_count(dto.product_barcode)

        return orderdao_to_responsedto(order)

    # ---------------------------------------------------------
    # PAY AN ORDER
    # ---------------------------------------------------------

    async def pay_order(self, order_id: int):

        #400
        if order_id <= 0:
            raise BadRequestError("Invalid order id")

        #404
        order = await self.repository.get_by_id(order_id)
        if not order:
            raise NotFoundError(f"Order {order_id} not found")

        # 420
        if order.status != OrderStatus.ISSUED:
            raise InvalidStateError("Order was not ISSUED")

        total = order.quantity * order.price_per_unit

        # 421 checked prima di chiamare la repo (faceva uguale se balance non c'era)
        async with AsyncSessionLocal() as session:
            balance_repo = BalanceRepository(session)
            balance = await balance_repo.get_balance()

        if balance.balance < total:
            raise BalanceError("Insufficient balance for the operation")

        order = await self.repository.pay_order(order_id)

        return orderdao_to_responsedto(order)

    # ---------------------------------------------------------
    # CREATE ORDER AND PAY
    # ---------------------------------------------------------
    async def create_and_pay(self, dto: OrderDTO) -> OrderDTO:

        # 400
        if (
                not dto.product_barcode
                or not dto.product_barcode.isdigit()
                or len(dto.product_barcode) < 12
                or len(dto.product_barcode) > 14
                or dto.quantity <= 0
                or dto.price_per_unit <= 0
        ):            raise BadRequestError("Invalid barcode or quantity")

        async with AsyncSessionLocal() as session:
            product_repo = ProductTypeRepository(session)
            balance_repo = BalanceRepository(session)

            product = await product_repo.get_product_type_by_barcode(dto.product_barcode)
            if not product:
                raise NotFoundError("Product not found")

            total = dto.quantity * product.price_per_unit
            balance = await balance_repo.get_balance()
            if balance.balance < total:
                raise BalanceError("Insufficient balance for the operation")

        order = await self.repository.create_and_pay(
            dto.product_barcode,
            dto.quantity,
            dto.price_per_unit,
            datetime.now()
        )

        async with AsyncSessionLocal() as session:
            product_repo = ProductTypeRepository(session)
            await product_repo.increment_usage_count(dto.product_barcode)

        return orderdao_to_responsedto(order)

    # ---------------------------------------------------------
    # RECORD ARRIVAL (PAID → COMPLETED)
    # ---------------------------------------------------------
    async def record_arrival(self, order_id: int):

        # 400
        if order_id <= 0:
            raise BadRequestError("Invalid order id")

        # 404
        order = await self.repository.get_by_id(order_id)
        if not order:
            raise NotFoundError(f"Order {order_id} not found")

        # 420
        if order.status != OrderStatus.PAID:
            raise InvalidStateError("Order is not PAID")

        async with AsyncSessionLocal() as session:
            product_repo = ProductTypeRepository(session)
            product = await product_repo.get_product_type_by_barcode(order.product_barcode)

            # 404 (product)
            if not product:
                raise NotFoundError("Product not found")

            # 500
            if not product.position:
                raise GeneralError("Product position not found")

            if not re.match(r"^[A-Za-z0-9]+-[A-Za-z0-9]+-[A-Za-z0-9]+$", product.position):
                raise GeneralError("Product position not found")

        result = await self.repository.complete_order(order_id)
        return orderdao_to_responsedto(result)

    # ---------------------------------------------------------
    # LIST ALL ORDERS
    # ---------------------------------------------------------
    async def list_orders(self):
        daos = await self.repository.list_all()
        return [orderdao_to_responsedto(o) for o in daos]
