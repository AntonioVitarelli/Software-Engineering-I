from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import AsyncSessionLocal
from app.models.DAO.system_dao import SystemInfoDAO


class BalanceRepository:
    def __init__(self, session: AsyncSession | None = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        return self._session or AsyncSessionLocal()

    async def reset_balance(self) -> bool:
        return await self.set_balance(0)

    async def set_balance(self, amount: float) -> bool:
        async with await self._get_session() as session:
            try:
                query_result = await session.execute(select(SystemInfoDAO))
                system_info = query_result.scalar_one()

                system_info.balance = amount

                await session.commit()
                await session.refresh(system_info)
                return True
            except SQLAlchemyError:
                await session.rollback()
                return False

    async def increase_balance(self, amount: float) -> bool:
        system_info = await self.get_balance()
        return await self.set_balance(system_info.balance + amount)

    async def decrease_balance(self, amount: float) -> bool:
        system_info = await self.get_balance()
        return await self.set_balance(system_info.balance - amount)

    async def get_balance(self) -> SystemInfoDAO:
        async with await self._get_session() as session:
            query_result = await session.execute(select(SystemInfoDAO))
            return query_result.scalar_one()
