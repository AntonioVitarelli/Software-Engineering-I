from app.repositories.customer_repository import CustomerRepository
from app.services.customer_service import customerdao_to_responsedto
from app.models.DTO.customer_dto import CustomerDTO
from app.models.DTO.loyalty_card_dto import LoyaltyCardDTO
from typing import List
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.bad_request import BadRequestError
from app.models.errors.conflict_error import ConflictError
from app.models.errors.insufficient_points_error import InsufficientPointsError

class CustomerController:
    def __init__(self):
        self.repository = CustomerRepository()

    def _parse_customer_id(self, customer_id: str) -> int:
        """Convert and validate customer id coming in as string."""
        try:
            customer_id_int = int(customer_id)
            if customer_id_int <= 0:
                raise ValueError
            return customer_id_int
        except (ValueError, TypeError):
            raise BadRequestError("Invalid customer id")

    async def create_customer(self, customer: CustomerDTO) -> CustomerDTO:
        """
        Create a new customer with optional loyalty card.
        
        Note: 
            - If an ID is provided in the request, it will be ignored (DB auto-generates IDs)
            - If points are provided in the card, they are ignored (card's existing points are maintained)
        
        Raises:
            - 400 BadRequestError: if name is empty/missing
            - 400 BadRequestError: if card_id format is invalid (must be 10 digits)
            - 404 NotFoundError: if card_id does not exist in DB
            - 409 ConflictError: if card_id is already attached to another customer
        """
        # 1. Validate input
        if customer.name is None or customer.name.strip() == '':
            raise BadRequestError('Customer name is required')
        
        # 2. Extract only the fields we need (ignore id and card points if provided)
        name = customer.name.strip()
        cardId = customer.card.card_id if customer.card else None
        
        # 3. If cardId present, validate format and existence
        if cardId:
            if not cardId.isdigit() or len(cardId) != 10:
                raise BadRequestError('Invalid card ID')
            card_dao = await self.repository.get_card(cardId)
            if not card_dao:
                raise NotFoundError(f"Card with id '{cardId}' not found")
            # Check that card is not already attached
            if await self.repository.card_already_attached(cardId):
                raise ConflictError(f"Card with id '{cardId}' is already attached to another customer")
            # Note: card's existing points are maintained, not overwritten
        
        # 4. Create customer (ID will be auto-generated, ignoring any provided ID)
        customer_dao = await self.repository.create_customer(name=name, cardId=cardId)
        return customerdao_to_responsedto(customer_dao)
    
    async def get_customer(self, customer_id: str) -> CustomerDTO:
        """
        Retrieve a customer by ID.
        
        Raises:
            - 400 BadRequestError: if customer_id is not a positive integer
            - 404 NotFoundError: if customer not found in DB
        """
        customer_id_int = self._parse_customer_id(customer_id)
        customer_dao = await self.repository.get_customer(customer_id_int)
        if not customer_dao:
            raise NotFoundError("Customer not found")
        
        return customerdao_to_responsedto(customer_dao)

    async def list_customer(self) -> List[CustomerDTO]:
        """
        List all customers in the system.
        """
        customers_dao = await self.repository.list_customer()
        return [customerdao_to_responsedto(c) for c in customers_dao]

    async def update_customer(self, customer_id: str, customer: CustomerDTO) -> CustomerDTO:
        """
        Update a customer's name and/or card.
        - If card is None (not present): don't update card
        - If card is empty object {}: detach card from customer and delete it
        - If card has card_id: validate and attach new card
        
        Raises:
            - 400 BadRequestError: if customer_id is not a positive integer
            - 400 BadRequestError: if name is empty/missing
            - 400 BadRequestError: if card_id format is invalid (must be 10 digits)
            - 404 NotFoundError: if customer not found
            - 404 NotFoundError: if card_id does not exist in DB
            - 409 ConflictError: if card_id is already attached to another customer
        """
        # 1. Validate input
        customer_id_int = self._parse_customer_id(customer_id)
        if customer.name is None or customer.name.strip() == '':
            raise BadRequestError('Customer name is required')
        
        updated_name = customer.name.strip()
        
        # 2. Determine card update action
        # - None: don't update card (updated_cardId = None)
        # - Empty object {}: detach and delete card (updated_cardId = "")
        # - Has card_id: attach new card (updated_cardId = card_id value)
        if customer.card is None:
            # Card not provided → don't update
            updated_cardId = None
        elif customer.card.card_id is None or customer.card.card_id == "":
            # Empty card object → detach and delete
            updated_cardId = ""
        else:
            # Card with ID provided → attach
            updated_cardId = customer.card.card_id
        
        # 3. Check that customer exists
        customer_dao = await self.repository.get_customer(customer_id_int)
        if not customer_dao:
            raise NotFoundError("Customer not found")
        
        # 4. If cardId present (not None and not empty), validate and check conflicts
        if updated_cardId and updated_cardId != "":
            # Validate format
            if not updated_cardId.isdigit() or len(updated_cardId) != 10:
                raise BadRequestError('Invalid card ID')
            # Check that it exists
            card_dao = await self.repository.get_card(updated_cardId)
            if not card_dao:
                raise NotFoundError(f"Card with id '{updated_cardId}' not found")
            # Check that card is not already attached to another customer
            if await self.repository.card_already_attached(updated_cardId, customer_id_int):
                raise ConflictError(f"Card with id '{updated_cardId}' is already attached to another customer")
        
        # 5. Call repository (it handles None, "", or valid card_id)
        updated_customer = await self.repository.update_customer(
            customer_id=customer_id_int,
            updated_name=updated_name,
            updated_cardId=updated_cardId
        )
        return customerdao_to_responsedto(updated_customer)


    async def delete_customer(self, customer_id: str) -> None:
        """
        Delete a customer by id. If a card is attached, the card is deleted as well.
        
        Raises:
            - 400 BadRequestError: if customer_id is not a positive integer
            - 404 NotFoundError: if customer not found
        """
        # 1. Validate input
        customer_id_int = self._parse_customer_id(customer_id)
        
        # 2. Check that customer exists
        customer_dao = await self.repository.get_customer(customer_id_int)
        if not customer_dao:
            raise NotFoundError("Customer not found")
        
        # 3. Call repository
        await self.repository.delete_customer(customer_id_int)

  
    async def create_card(self) -> LoyaltyCardDTO:
        """
        Create a new loyalty card with auto-generated ID and 0 points.
        """
        card_dao = await self.repository.create_card()
        return LoyaltyCardDTO(card_id=card_dao.id, points=card_dao.points)

   
    async def attach_card_to_customer(self, customer_id: str, card_id: str) -> CustomerDTO:
        """
        Attach a loyalty card to a customer.
        
        Raises:
            - 400 BadRequestError: if customer_id is not a positive integer
            - 400 BadRequestError: if card_id format is invalid (must be 10 digits)
            - 404 NotFoundError: if customer not found
            - 404 NotFoundError: if card not found
            - 409 ConflictError: if card is already attached to another customer
        """
        # 1. Validate input
        customer_id_int = self._parse_customer_id(customer_id)
        if not card_id or not card_id.isdigit() or len(card_id) != 10:
            raise BadRequestError('Invalid card ID')
        
        # 2. Check that customer and card exist
        customer_dao = await self.repository.get_customer(customer_id_int)
        if not customer_dao:
            raise NotFoundError("Customer not found")
        
        card_dao = await self.repository.get_card(card_id)
        if not card_dao:
            raise NotFoundError("Card not found")
        
        # 3. Check that card is not already attached to another customer
        if await self.repository.card_already_attached(card_id, customer_id_int):
            raise ConflictError(f"Card with id '{card_id}' is already attached to another customer")
        
        # 4. Call repository
        updated_customer = await self.repository.attach_card_to_customer(customer_id_int, card_id)
        return customerdao_to_responsedto(updated_customer)


    async def update_card_points(self, card_id: str, points: int) -> LoyaltyCardDTO:
        """
        Update loyalty card points (add or subtract).
        
        Raises:
            - 400 BadRequestError: if card_id format is invalid (must be 10 digits)
            - 404 NotFoundError: if card not found in DB
            - 500 InsufficientPointsError: if points go negative (card would have < 0 points)
        """
        # 1. Validate input
        if not card_id or not card_id.isdigit() or len(card_id) != 10:
            raise BadRequestError('Invalid card ID')
        
        # 2. Check that card exists
        card_dao = await self.repository.get_card(card_id)
        if not card_dao:
            raise NotFoundError(f"Card with id '{card_id}' not found")
        
        # 3. Check that points don't go negative
        new_points = card_dao.points + points
        if new_points < 0:
            raise InsufficientPointsError('Insufficient points on the card')
        
        # 4. Call repository
        updated_card = await self.repository.update_card_points(card_id, points)
        return LoyaltyCardDTO(card_id=updated_card.id, points=updated_card.points)