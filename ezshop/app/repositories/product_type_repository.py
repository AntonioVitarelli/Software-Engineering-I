from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.DAO.product_type_dao import ProductTypeDAO
from app.database.database import AsyncSessionLocal


class ProductTypeRepository:

    def __init__ (self, session: Optional[AsyncSession] = None):
        self._session = session or AsyncSessionLocal()
    
    async def _get_session(self) -> AsyncSession:
        return self._session or AsyncSessionLocal()
    
    async def create_product_type(self, description: str, barcode: str, price_per_unit: float, note: str, quantity: int, position: str):
        async with await self._get_session() as session:
            
            product_type = ProductTypeDAO(description=description, barcode=barcode, price_per_unit=price_per_unit, note=note, quantity=quantity, position=position)
            session.add(product_type)

            await session.commit()
            await session.refresh(product_type)

            return product_type
        
    async def get_product_types(self) -> list[ProductTypeDAO]:
        async with await self._get_session() as session:

            result = await session.execute(select(ProductTypeDAO))
            product_types = result.scalars().all()

            return product_types
            
    async def get_product_type(self, product_type_id: int) -> ProductTypeDAO | None:
        async with await self._get_session() as session:

            product_type = await session.get(ProductTypeDAO, ident=product_type_id)

            return product_type

    async def find_another_product_with_same_barcode(self, product_type_id: int, barcode: str) -> ProductTypeDAO | None:
        async with await self._get_session() as session:

            result = await session.execute(
                select(ProductTypeDAO).where(
                    (ProductTypeDAO.barcode == barcode) & 
                    (ProductTypeDAO.id != product_type_id)
                )
            )
            product_type = result.scalars().first()

            return product_type
            
    # ! errore 420 non gestito - Issue aperta 
    async def update_product_type(self, product_type_dao: ProductTypeDAO, new_description: str, new_barcode: str, new_price_per_unit: float, new_note: str, new_quantity: int, new_position: str) -> dict:
        async with await self._get_session() as session:

            merged_session = await session.merge(product_type_dao)
            
            merged_session.description = new_description
            merged_session.barcode = new_barcode
            merged_session.price_per_unit = new_price_per_unit
            merged_session.note = new_note
            merged_session.quantity = new_quantity
            merged_session.position = new_position
        
            await session.commit()
            await session.refresh(merged_session)


            return {"success" : "true"}

    async def delete_product_type(self, product_type_dao: ProductTypeDAO) -> None:
        async with await self._get_session() as session:

            await session.delete(product_type_dao)
            await session.commit()
            return

    async def get_product_type_by_barcode(self, barcode:str) -> ProductTypeDAO | None:
        async with await self._get_session() as session:

            result = await session.execute(
                select(ProductTypeDAO).filter(ProductTypeDAO.barcode == barcode)
            )
            product_type = result.scalars().first()

            return product_type

    # ! la ricerca è exact o partial?
    async def get_product_type_by_description(self, description:str) -> ProductTypeDAO | None:
        async with await self._get_session() as session:

            result = await session.execute(
                select(ProductTypeDAO).filter(ProductTypeDAO.description.like(f"%{description}%"))
                
            )
            return result.scalars().all()
    
    async def get_products_position_conflict(self, position: str, product_type_id: int) -> ProductTypeDAO | None:
        async with await self._get_session() as session:

            result = await session.execute(
                select(ProductTypeDAO).filter(
                    (ProductTypeDAO.position == position) &
                    (ProductTypeDAO.id != product_type_id)
                )
            )

            return result.scalars().first()
        
    # Valid imput: "2-b-5",  "2-B-5",  "12-Cc-5", match mattern - -
    async def update_product_type_position(self, product_type_dao: ProductTypeDAO, new_position: str) -> dict:
        async with await self._get_session() as session:

            merged_session = await session.merge(product_type_dao)
            merged_session.position = new_position

            await session.commit()
            await session.refresh(merged_session)

            return {"success" : "true"} 
        
    async def update_product_type_quantity(self, product_type_dao: ProductTypeDAO, new_quantity: int) -> dict:
        async with await self._get_session() as session:

            merged_session = await session.merge(product_type_dao)
            merged_session.quantity += new_quantity

            await session.commit()
            await session.refresh(merged_session)         

            return {"success" : "true"}
    
    async def increment_usage_count(self, barcode: str) -> dict:
        async with await self._get_session() as session:
            result = await session.execute(
                select(ProductTypeDAO).filter(ProductTypeDAO.barcode == barcode)
            )
            product_type = result.scalars().first()
            
            if product_type:
                product_type.increment_usage_count()
                await session.commit()
                await session.refresh(product_type)
                return {"success": "true", "usage_count": product_type.get_usage_count()}
            
            return {"success": "false", "error": "Product not found"}
    
    async def decrement_usage_count(self, barcode: str) -> dict:
        async with await self._get_session() as session:
            result = await session.execute(
                select(ProductTypeDAO).filter(ProductTypeDAO.barcode == barcode)
            )
            product_type = result.scalars().first()
            
            if product_type:
                product_type.decrement_usage_count()
                await session.commit()
                await session.refresh(product_type)
                return {"success": "true", "usage_count": product_type.get_usage_count()}
            
            return {"success": "false", "error": "Product not found"}
    
    async def is_product_in_use(self, barcode: str) -> bool:
        async with await self._get_session() as session:
            result = await session.execute(
                select(ProductTypeDAO).filter(ProductTypeDAO.barcode == barcode)
            )
            product_type = result.scalars().first()
            
            if product_type:
                return product_type.is_in_use()
            
            return False