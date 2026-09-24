from app.models.DAO.system_dao import SystemInfoDAO
from app.models.DAO.user_dao import UserDAO
from app.models.DTO.error_dto import ErrorDTO
from app.models.DAO.orders_dao import OrderDAO
from app.models.DTO.orders_dto import OrderDTO
from app.models.DTO.system_dto import SystemDTO
from app.models.DTO.token_dto import TokenDTO
from app.models.DTO.user_dto import UserDTO


def create_error_dto(code: int, message: str, name: str) -> ErrorDTO:
    """Create an ErrorDTO instance"""
    return ErrorDTO(code=code, message=message, name=name)


def create_token_dto(token: str) -> TokenDTO:
    return TokenDTO(token=token)


def userdao_to_dto(user_dao: UserDAO) -> UserDTO:
    return UserDTO(
        id=user_dao.id,
        username=user_dao.username,
        password=user_dao.password,
        type=user_dao.type,
    )


def userdao_to_responsedto(user_dao: UserDAO) -> UserDTO:
    return UserDTO(
        id=user_dao.id,
        username=user_dao.username,
        type=user_dao.type
    )

def orderdao_to_responsedto(order_dao: OrderDAO) -> OrderDTO:
    return OrderDTO(
        id=order_dao.id,
        product_barcode=order_dao.product_barcode,
        quantity=order_dao.quantity,
        price_per_unit=order_dao.price_per_unit,
        status=order_dao.status,
        issue_date=order_dao.issue_date,
    )

def systemdao_to_responsedto(system_dao: SystemInfoDAO) -> SystemDTO:
    return SystemDTO(id=system_dao.id, balance=system_dao.balance)

