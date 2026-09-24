from app.models.DAO.return_dao import ReturnDAO, ReturnLineDAO
from app.models.DTO.return_dto import ReturnDTO, ReturnLineDTO


def return_dao_to_dto(return_dao: ReturnDAO) -> ReturnDTO | None:
    if not return_dao:
        return None
    if return_dao.lines:
        line_dtos = [
            return_line_dao_to_dto(line)
            for line in return_dao.lines
        ]
    else:
        line_dtos = []
    if return_dao.closed_at is not None:
        closed_at = return_dao.closed_at.strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        closed_at = None
    return ReturnDTO(
        id=return_dao.id,
        sale_id=return_dao.sale_id,
        status=return_dao.status,
        created_at=return_dao.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
        closed_at=closed_at,
        lines=line_dtos,
    )

def return_line_dao_to_dto(return_line_dao: ReturnLineDAO) -> ReturnLineDTO:
    return ReturnLineDTO(
        id=return_line_dao.id,
        return_id=return_line_dao.return_id,
        product_barcode=return_line_dao.product_barcode,
        quantity=return_line_dao.quantity,
        price_per_unit=return_line_dao.price_per_unit,
    )