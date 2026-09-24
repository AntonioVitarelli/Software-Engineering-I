from app.models.DAO.product_type_dao import ProductTypeDAO
from app.models.DTO.error_dto import ErrorDTO
from app.models.DTO.product_type_dto import ProductTypeDTO

# ? attenzione ho aggiunto al DAO un nuovo campo "already_used", va gestito anche qui?
def product_type_dto_to_dao(product_type_dto: ProductTypeDTO) -> ProductTypeDAO:
    return ProductTypeDAO(
        id  = product_type_dto.id,
        description = product_type_dto.description,
        barcode = product_type_dto.barcode,
        price_per_unit = product_type_dto.price_per_unit,
        note = product_type_dto.note,   
        quantity = product_type_dto.quantity,
        position = product_type_dto.position
    )

def product_type_dao_to_dto(product_type_dao: ProductTypeDAO) -> ProductTypeDTO:
    return ProductTypeDTO(
        id = product_type_dao.id,
        description= product_type_dao.description,
        barcode= product_type_dao.barcode,
        price_per_unit= product_type_dao.price_per_unit,
        note= product_type_dao.note,
        quantity= product_type_dao.quantity,
        position= product_type_dao.position
    )

def product_type_error_dto(code: int, message: str, name: str) -> ErrorDTO:
    return ErrorDTO(code=code, message=message, name=name)