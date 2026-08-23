from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.auth_dependencies import get_current_user
from app.auth.auth_schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.auth.auth_service import AuthService
from app.auth.user_model import User
from app.auth.user_service import UserService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

auth_service = AuthService()
user_service = UserService()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(request: RegisterRequest):
    user = auth_service.register_user(
        email=request.email,
        full_name=request.full_name,
        password=request.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        workspace_ids=user.workspace_ids,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(request: LoginRequest):
    user = auth_service.authenticate_user(
        email=request.email,
        password=request.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = auth_service.create_token_for_user(user)

    return TokenResponse(
        access_token=token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        workspace_ids=current_user.workspace_ids,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
    )


@router.patch(
    "/users/{user_id}/workspaces/{workspace_id}",
    response_model=UserResponse,
)
def assign_workspace_to_user(
    user_id: str,
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to assign this workspace.",
        )

    user = user_service.assign_workspace(
        user_id=user_id,
        workspace_id=workspace_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        workspace_ids=user.workspace_ids,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
    )