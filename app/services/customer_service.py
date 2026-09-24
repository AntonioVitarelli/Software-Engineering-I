from app.models.DAO.customer_dao import CustomerDAO
from app.models.DTO.customer_dto import CustomerDTO
from app.models.DTO.loyalty_card_dto import LoyaltyCardDTO

def customerdao_to_responsedto(customer_dao: CustomerDAO) -> CustomerDTO:
    card_dto = None
    if customer_dao.loyalty_card:
        card_dto = LoyaltyCardDTO(
            card_id=customer_dao.loyalty_card.id,
            points=customer_dao.loyalty_card.points
        )
    
    return CustomerDTO(
        id=customer_dao.id,
        name=customer_dao.name,
        card=card_dto
    )
