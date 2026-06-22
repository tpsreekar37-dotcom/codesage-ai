from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import datetime as dt

from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.api.deps import get_current_user
from app.models.user import User
from app.models.session import UserSession
from app.models.audit import AuditLog
from app.schemas.user import UserCreate, UserResponse, Token
from app.repositories.user import UserRepository
from app.repositories.session import UserSessionRepository
from app.repositories.audit import AuditLogRepository

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user_repo = UserRepository(db)
    audit_repo = AuditLogRepository(db)
    
    existing_user = await user_repo.get_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
        
    hashed_password = get_password_hash(user_in.password)
    # Determine role (first user is admin, others standard users)
    # To keep it robust, standard default role is 'user'
    db_users = await user_repo.get_multi(limit=1)
    role = "admin" if len(db_users) == 0 else "user"
    
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        role=role
    )
    
    user = await user_repo.create(new_user)
    
    # Audit log
    audit_log = AuditLog(
        user_id=user.id,
        action="REGISTER",
        details={"email": user.email, "role": user.role},
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    await audit_repo.create(audit_log)
    
    return user

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user_repo = UserRepository(db)
    session_repo = UserSessionRepository(db)
    audit_repo = AuditLogRepository(db)
    
    user = await user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated."
        )
        
    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Expiration datetime for session record
    expires_at = dt.datetime.utcnow() + timedelta(days=7)
    
    # Record user session
    user_session = UserSession(
        user_id=user.id,
        refresh_token=refresh_token,
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent", "Unknown"),
        expires_at=expires_at
    )
    await session_repo.create(user_session)
    
    # Audit log
    audit_log = AuditLog(
        user_id=user.id,
        action="LOGIN",
        details={"email": user.email},
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    await audit_repo.create(audit_log)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token_in: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    session_repo = UserSessionRepository(db)
    
    # Validate refresh token
    payload = decode_token(refresh_token_in)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
        
    db_session = await session_repo.get_by_token(refresh_token_in)
    if not db_session or db_session.expires_at < dt.datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Revoked or expired refresh token"
        )
        
    # Generate new tokens
    access_token = create_access_token(subject=db_session.user_id)
    new_refresh_token = create_refresh_token(subject=db_session.user_id)
    
    # Revoke old session and create a new session
    db_session.is_revoked = True
    await session_repo.update(db_session, {"is_revoked": True})
    
    expires_at = dt.datetime.utcnow() + timedelta(days=7)
    new_session = UserSession(
        user_id=db_session.user_id,
        refresh_token=new_refresh_token,
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent", "Unknown"),
        expires_at=expires_at
    )
    await session_repo.create(new_session)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    session_repo = UserSessionRepository(db)
    audit_repo = AuditLogRepository(db)
    
    # Revoke all sessions for this user
    await session_repo.revoke_all_by_user(current_user.id)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="LOGOUT",
        details={"email": current_user.email},
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    await audit_repo.create(audit_log)
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
