from app.repositories.product_type_repository import ProductTypeRepository
from app.services.product_type_mapper import product_type_dao_to_dto
from app.utils import find_or_throw_not_found, throw_bad_request_if, throw_conflict_if_found, throw_invalid_state_if


class ProductTypeController:
    def __init__(self):
        self.repo = ProductTypeRepository()

    # ! attenzione c'è da verificare il barcode con la libreria gtin https://pypi.org/project/gtin/
    async def create_product_type(self, description: str, barcode: str, price_per_unit: float, note: str, quantity: int, position: str):
        
        existing_product_type_with_same_barcode = await self.repo.get_product_type_by_barcode(barcode)
        throw_conflict_if_found(
            [existing_product_type_with_same_barcode] if existing_product_type_with_same_barcode else [],
            lambda _: True,
            f"Barcode already in use"
        )
        
        created = await self.repo.create_product_type(description, barcode, price_per_unit, note, quantity, position)

        return product_type_dao_to_dto(created)
    
    async def list_product_types(self):
        products = await self.repo.get_product_types()
        return [product_type_dao_to_dto(product) for product in products]

    async def get_product_type(self, product_type_id: int):
        product = await self.repo.get_product_type(product_type_id)
        
        find_or_throw_not_found(
                [product] if product else [],
                lambda _: True,
                f"Product not found"
            )
        
        return product_type_dao_to_dto(product)
    
    async def update_product_type(self, product_type_id: int, description: str = None, barcode: str = None, price_per_unit: float = None, note: str = None, quantity: int = None, position: str = None):
        
        product = await self.repo.get_product_type(product_type_id)
        
        find_or_throw_not_found(
                [product] if product else [],
                lambda _: True,
                f"Product not found"
            )
        
        # Usa i valori esistenti se non vengono forniti nuovi valori
        new_description = description if description is not None else product.description
        new_barcode = barcode if barcode is not None else product.barcode
        new_price_per_unit = price_per_unit if price_per_unit is not None else product.price_per_unit
        new_note = note if note is not None else product.note
        new_quantity = quantity if quantity is not None else product.quantity
        new_position = position if position is not None else product.position
        
        # Verifica barcode solo se è stato modificato
        if barcode is not None and barcode != product.barcode:
            exists_another_product_with_same_barcode = await self.repo.find_another_product_with_same_barcode(product_type_id, barcode)
            
            throw_conflict_if_found(
                    [exists_another_product_with_same_barcode] if exists_another_product_with_same_barcode else [],
                    lambda _: True,
                    f"Barcode already in use"
                )
        
        if product.is_in_use() and barcode != product.barcode:
            throw_invalid_state_if(True)
        
        return await self.repo.update_product_type(product, new_description, new_barcode, new_price_per_unit, new_note, new_quantity, new_position)
    
    async def delete_product_type(self, product_type_id: int):

        exists_product = await self.repo.get_product_type(product_type_id)
        find_or_throw_not_found(
                [exists_product] if exists_product else [],
                lambda _: True,
                f"Product not found"
            )
        
        if exists_product.is_in_use():
            throw_invalid_state_if(True)

        return await self.repo.delete_product_type(exists_product)
    
    async def get_product_type_by_barcode(self, barcode: str):
        product = await self.repo.get_product_type_by_barcode(barcode)
        find_or_throw_not_found(
               [product] if product else [],
               lambda _: True,
               f"Product not found"
            )
        
        return product_type_dao_to_dto(product)
    
    async def search_product_type_by_description(self, description: str):
        products = await self.repo.get_product_type_by_description(description)
        return [product_type_dao_to_dto(product) for product in products]
    
    async def update_product_type_position(self, product_type_id: int, position: str):
        
        product = await self.repo.get_product_type(product_type_id)

        find_or_throw_not_found(
                [product] if product else [],
                lambda _: True,
                f"Product not found"
            )
        
        product_conflict = await self.repo.get_products_position_conflict(position, product_type_id)
        throw_conflict_if_found(
            [product_conflict] if product_conflict else [],
            lambda _: True,
            f"Position already in use"
        )

        
        return await self.repo.update_product_type_position(product, position)

    async def update_product_type_quantity(self, product_type_id: int, quantity: int):
        
        product = await self.repo.get_product_type(product_type_id)
        find_or_throw_not_found(
                [product] if product else [],
                lambda _: True,
                f"Product not found"
            )
        
        if ( product.quantity + quantity ) < 0:
                throw_bad_request_if( True, "Insufficient quantity" )
        
        return await self.repo.update_product_type_quantity(product, quantity)