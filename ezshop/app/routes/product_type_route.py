import re
from fastapi import APIRouter, Depends
from typing import List, Optional
from app.config.config import ROUTES
from app.controllers.product_type_controller import ProductTypeController
from app.middleware.auth_middleware import authenticate_user
from app.models.DTO.product_type_dto import ProductTypeDTO, ProductTypeUpdateDTO
from app.models.user_type import UserType
from app.utils import throw_bad_request_if


router = APIRouter(prefix=ROUTES['V1_PRODUCTS'], tags=["Products"])
controller = ProductTypeController()

@router.post("/", 
            response_model=ProductTypeDTO, 
            status_code=201, 
            dependencies=[
                Depends(
                    authenticate_user([
                        UserType.Administrator, 
                        UserType.ShopManager
                        ])
            )])
# ! attenzione c'è da verificare il barcode con la libreria gtin https://pypi.org/project/gtin/    
async def create_product_type(product_type: ProductTypeDTO):
    #throw_bad_request_if( (len(product_type.barcode) < 12 or len(product_type.barcode) > 14), "Invalid barcode, should be between 12 and 14 characters" )
    throw_bad_request_if(not re.match(r"^\d{12,14}$", product_type.barcode), "Invalid barcode, should be between 12 and 14 numeric characters")
    throw_bad_request_if( product_type.description is None or product_type.description == "" or product_type.price_per_unit is None or product_type.price_per_unit <= 0)
    
    return await controller.create_product_type(product_type.description, product_type.barcode, product_type.price_per_unit, product_type.note, product_type.quantity, product_type.position)

@router.get("/", 
            response_model=List[ProductTypeDTO],
            status_code=200,
            dependencies=[
                Depends(
                    authenticate_user([
                        UserType.Administrator, 
                        UserType.ShopManager, 
                        UserType.Cashier
                        ])
                )
            ])
async def list_product_types():
    print("Listing product types")
    return await controller.list_product_types()

@router.get("/search",
            response_model=List[ProductTypeDTO],
            status_code=200,
            dependencies=[
                Depends(
                    authenticate_user([
                        UserType.Administrator, 
                        UserType.ShopManager, 
                        ])
                )
            ])
async def search_product_types_by_description(query: Optional[str] = None):
    print("query:", query)
    return await controller.search_product_type_by_description(query or "")


@router.get("/{product_type_id}",
            response_model=ProductTypeDTO,
            status_code=200,
            dependencies=[
                Depends(
                    authenticate_user([
                        UserType.Administrator, 
                        UserType.ShopManager, 
                        UserType.Cashier
                        ])
                )
            ])
async def get_product_type(product_type_id: int):
    throw_bad_request_if( product_type_id < 0 or product_type_id is None )

    return await controller.get_product_type(product_type_id)

@router.put("/{product_type_id}",
            response_model=dict,
            status_code=201,
            dependencies=[
                Depends(
                    authenticate_user([
                        UserType.Administrator, 
                        UserType.ShopManager
                        ])
                )
            ])
async def update_product_type(product_type_id: int, product_type: ProductTypeUpdateDTO):
    throw_bad_request_if( product_type_id < 0 or product_type_id is None )
    
    # Validazioni solo sui campi forniti
    if product_type.barcode is not None:
        throw_bad_request_if(not re.match(r"^\d{12,14}$", product_type.barcode), "Invalid barcode, should be between 12 and 14 numeric characters")
    
    if product_type.description is not None:
        throw_bad_request_if(product_type.description == "", "Description cannot be empty")
    
    if product_type.price_per_unit is not None:
        throw_bad_request_if(product_type.price_per_unit <= 0, "Price must be greater than 0")
    
    if product_type.quantity is not None:
        throw_bad_request_if(product_type.quantity <= 0, "Quantity cannot be negative")
    
    return await controller.update_product_type(product_type_id, product_type.description, product_type.barcode, product_type.price_per_unit, product_type.note, product_type.quantity, product_type.position)

@router.delete("/{product_type_id}",
                response_model=None,
                status_code=204,
                dependencies=[
                    Depends(
                        authenticate_user([
                            UserType.Administrator, 
                            UserType.ShopManager
                            ])
                    )
                ])
async def delete_product_type(product_type_id: int):
    throw_bad_request_if( ( product_type_id < 0 or product_type_id is None), "Invalid product id" )

    await controller.delete_product_type(product_type_id)
    return None

@router.get("/barcode/{barcode}",
            response_model=ProductTypeDTO,
            status_code=200,
            dependencies=[
                Depends(
                    authenticate_user([
                        UserType.Administrator, 
                        UserType.ShopManager, 
                        ])
                )
            ])
async def get_product_type_by_barcode(barcode: str):
    throw_bad_request_if( len(barcode) < 12 or len(barcode) > 14 , "Invalid barcode")

    return await controller.get_product_type_by_barcode(barcode)



@router.patch("/{product_type_id}/position",
            response_model=dict,
            status_code=201,
            dependencies=[
                Depends(
                    authenticate_user([
                        UserType.Administrator, 
                        UserType.ShopManager
                        ])
                )
            ])

# ! attenzione c'è da verificare il barcode con la libreria gtin https://pypi.org/project/gtin/    
async def update_product_type_position(product_type_id: int, position: str):
    throw_bad_request_if( product_type_id <= 0, "Invalid product id" )
    throw_bad_request_if( position is None, "Position cannot be None" )

    if position != "" and not re.match(r"^[0-9]+-[A-Za-z]+-[0-9]+$", position):
        throw_bad_request_if( True, "Invalid position format" )
    
    return await controller.update_product_type_position(product_type_id, position)

@router.patch("/{product_type_id}/quantity",
            response_model=dict,
            status_code=201,
            dependencies=[
                Depends(
                    authenticate_user([
                        UserType.Administrator, 
                        UserType.ShopManager
                        ])
                )
            ])
async def update_product_type_quantity(product_type_id: int, quantity: Optional[str] = None):
    throw_bad_request_if( product_type_id < 0, "Invalid product id")
    throw_bad_request_if( quantity is None or quantity == "", "Invalid quantity")
    
    # Convert to int after validation
    try:
        quantity_int = int(quantity)
    except ValueError:
        throw_bad_request_if(True, "Quantity must be a valid integer")
    
    return await controller.update_product_type_quantity(product_type_id, quantity_int)