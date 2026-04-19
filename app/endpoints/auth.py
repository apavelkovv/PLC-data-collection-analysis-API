from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas import UserCreate, UserResponse, TokenResponse, LoginRequest
from app.service.auth_service import register_user, authenticate_user, get_current_user
from app.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """FR-01: Register new user."""
    user = await register_user(db, data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    return await authenticate_user(db, form_data.username, form_data.password)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user
