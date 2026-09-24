from sqlalchemy import select
from app.database.database import AsyncSessionLocal
from app.models.DAO.orders_dao import OrderDAO, OrderStatus
from typing import Optional
from app.database.database import AsyncSession
from app.repositories.balance_repository import BalanceRepository
from app.repositories.product_type_repository import ProductTypeRepository
from datetime import datetime

class OrderRepository:

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        return self._session or AsyncSessionLocal()


    # ---------------------------------------------------------
    # CREATE ORDER
    # ---------------------------------------------------------

    async def create_order(self, product_barcode: str, quantity: int, price_per_unit: int, status: str, issue_date: datetime) -> OrderDAO:
        async with AsyncSessionLocal() as session:
            product_repo = ProductTypeRepository(session)

            product = await product_repo.get_product_type_by_barcode(product_barcode)

            order = OrderDAO(
                product_barcode=product.barcode,
                quantity=quantity,
                price_per_unit=price_per_unit,
                status=status,
                issue_date = issue_date
            )

            session.add(order)
            await session.commit()
            await session.refresh(order)
            return order

    # ---------------------------------------------------------
    # LIST ORDERS
    # ---------------------------------------------------------

    async def list_all(self) -> list[OrderDAO]:
        async with await self._get_session() as session:
            result = await session.execute(select(OrderDAO))
            return result.scalars().all()

    # ---------------------------------------------------------
    # PAY ORDER
    # ---------------------------------------------------------

    async def pay_order(self, order_id: int) -> OrderDAO:
        async with AsyncSessionLocal() as session:
            order = await session.get(OrderDAO, order_id)

            total = order.quantity * order.price_per_unit
            order.status = OrderStatus.PAID

            balance_repo = BalanceRepository(self._session)
            await balance_repo.decrease_balance(total)

            await session.commit()
            await session.refresh(order)
            return order

    # ---------------------------------------------------------
    # CREATE+PAY ORDER
    # ---------------------------------------------------------

    async def create_and_pay(self, product_barcode: str, quantity: int, price_per_unit: int, issue_date: datetime) -> OrderDAO:
        async with AsyncSessionLocal() as session:
            product_repo = ProductTypeRepository(session)
            balance_repo = BalanceRepository(session)

            product = await product_repo.get_product_type_by_barcode(product_barcode)

            order = OrderDAO(
                product_barcode=product.barcode,
                quantity=quantity,
                price_per_unit=price_per_unit,
                status=OrderStatus.PAID,
                issue_date=issue_date
            )

            total = order.quantity * price_per_unit
            await balance_repo.decrease_balance(total)

            session.add(order)
            await session.commit()
            await session.refresh(order)
            return order

    # ---------------------------------------------------------
    # COMPLETE ORDER
    # ---------------------------------------------------------

    async def complete_order(self, order_id: int) -> OrderDAO:
        async with AsyncSessionLocal() as session:
            product_repo = ProductTypeRepository(session)

            order = await session.get(OrderDAO, order_id)

            product = await product_repo.get_product_type_by_barcode(order.product_barcode)

            if product.quantity is None:
                product.quantity = 0

            product.quantity += order.quantity
            order.status = OrderStatus.COMPLETED

            await session.commit()
            return order

    async def get_by_id(self, order_id: int) -> OrderDAO | None:
        async with await self._get_session() as session:
            return await session.get(OrderDAO, order_id)