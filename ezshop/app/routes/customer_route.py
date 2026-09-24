from fastapi import APIRouter, status, Depends, Query
from typing import List
from app.models.DTO.customer_dto import CustomerDTO
from app.models.DTO.loyalty_card_dto import LoyaltyCardDTO
from app.controllers.customer_controller import CustomerController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES

# ===== CUSTOMER ROUTES =====

router = APIRouter(prefix=ROUTES['V1_CUSTOMERS'], tags=["Customers"])
controller = CustomerController()

@router.post("/", response_model=CustomerDTO, 
            status_code=status.HTTP_201_CREATED, 
            dependencies=[Depends(authenticate_user([]))])
async def create_customer(customer: CustomerDTO):
    return await controller.create_customer(customer)

@router.get("/{customer_id}", response_model=CustomerDTO,
            status_code=status.HTTP_200_OK, 
            dependencies=[Depends(authenticate_user([]))])
async def get_customer(customer_id: str):
    return await controller.get_customer(customer_id)

@router.get("/", response_model=List[CustomerDTO],
            status_code=status.HTTP_200_OK, 
            dependencies=[Depends(authenticate_user([]))])
async def list_customers():
    return await controller.list_customer()

@router.put("/{customer_id}", response_model=CustomerDTO,
            status_code=status.HTTP_201_CREATED,
            dependencies=[Depends(authenticate_user([]))])
async def update_customer(customer_id: str, customer: CustomerDTO):
    return await controller.update_customer(customer_id, customer)
      
@router.delete("/{customer_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(authenticate_user([]))])
async def delete_customer(customer_id: str):
   return await controller.delete_customer(customer_id)

# ===== LOYALTY CARD ROUTES =====

@router.post("/cards", response_model=LoyaltyCardDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([]))])
async def create_card():
    return await controller.create_card()

@router.patch("/{customer_id}/attach-card/{card_id}", response_model=CustomerDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([]))])
async def attach_card(customer_id: str, card_id: str):
    return await controller.attach_card_to_customer(customer_id, card_id)

@router.patch("/cards/{card_id}", response_model=LoyaltyCardDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([]))])
async def update_card_points(card_id: str, points: int = Query(..., description="Points to add/subtract")):
    return await controller.update_card_points(card_id, points)