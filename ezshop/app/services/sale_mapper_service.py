from app.models.DAO.sale_dao import SaleDAO, SaleLineDAO
from app.models.DTO.sale_dto import SaleDTO, SaleLineDTO

def sale_dao_to_dto(sale_dao: SaleDAO) -> SaleDTO | None:
    if not sale_dao:
        return None
    if sale_dao.lines:
        line_dtos = [
            sale_line_dao_to_dto(line)
            for line in sale_dao.lines
        ]
    else:
        line_dtos = []
    if sale_dao.closed_at is not None:
        closed_at = sale_dao.closed_at.strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        closed_at = None
    return SaleDTO(
        id=sale_dao.id,
        status=sale_dao.status,
        discount_rate=sale_dao.discount_rate,
        created_at=sale_dao.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
        closed_at=closed_at,
        lines=line_dtos,
    )

def sale_line_dao_to_dto(sale_line_dao: SaleLineDAO) -> SaleLineDTO:
    return SaleLineDTO(
        id=sale_line_dao.id,
        sale_id=sale_line_dao.sale_id,
        product_barcode=sale_line_dao.product_barcode,
        quantity=sale_line_dao.quantity,
        price_per_unit=sale_line_dao.price_per_unit,
        discount_rate=sale_line_dao.discount_rate,
    )

