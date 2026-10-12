from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.sales import router as sales_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(sales_router, prefix="/sales", tags=["sales"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
