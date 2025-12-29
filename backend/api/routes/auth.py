"""
Authentication routes and utilities
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

from api.models import Token, TokenData
from api.config import settings

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict):
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Verify JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return TokenData(username=username)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_current_user(token_data: TokenData = Depends(verify_token)):
    """Get current authenticated user"""
    # TODO: Fetch user from database
    return {"username": token_data.username}


@router.post("/login", response_model=Token)
async def login(username: str, password: str):
    """
    Login endpoint
    Returns JWT token
    """
    # TODO: Verify credentials against database
    # For now, simple demo
    if username == "admin" and password == "admin":
        access_token = create_access_token(data={"sub": username})
        return Token(access_token=access_token)
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )


@router.post("/register")
async def register(username: str, password: str, email: str):
    """
    Register new user
    """
    # TODO: Create user in database
    hashed_password = pwd_context.hash(password)
    return {"message": "User created successfully"}
