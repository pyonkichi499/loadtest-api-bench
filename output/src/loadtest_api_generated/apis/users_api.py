# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from loadtest_api_generated.apis.users_api_base import BaseUsersApi
import loadtest_api_generated.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from loadtest_api_generated.models.extra_models import TokenModel  # noqa: F401
from pydantic import Field
from typing import List, Optional
from typing_extensions import Annotated
from uuid import UUID
from loadtest_api_generated.models.error_response import ErrorResponse
from loadtest_api_generated.models.user import User
from loadtest_api_generated.models.user_stats import UserStats


router = APIRouter()

ns_pkg = loadtest_api_generated.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/users/{user_id}",
    responses={
        200: {"model": User, "description": "User found"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
    tags=["users"],
    summary="Get a user by ID (PK lookup)",
    response_model_by_alias=True,
)
async def get_user_by_id(
    user_id: UUID = Path(..., description=""),
) -> User:
    if not BaseUsersApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUsersApi.subclasses[0]().get_user_by_id(user_id)


@router.get(
    "/users",
    responses={
        200: {"model": List[User], "description": "List of users"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    tags=["users"],
    summary="List users with limit",
    response_model_by_alias=True,
)
async def list_users(
    limit: Optional[Annotated[int, Field(le=1000, strict=True, ge=1)]] = Query(100, description="", alias="limit", ge=1, le=1000),
) -> List[User]:
    if not BaseUsersApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUsersApi.subclasses[0]().list_users(limit)


@router.get(
    "/users/search",
    responses={
        200: {"model": List[User], "description": "Search results"},
    },
    tags=["users"],
    summary="Search users by name (partial match, no index)",
    response_model_by_alias=True,
)
async def search_users(
    name: Annotated[str, Field(min_length=1, strict=True)] = Query(None, description="", alias="name", min_length=1),
) -> List[User]:
    if not BaseUsersApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUsersApi.subclasses[0]().search_users(name)


@router.get(
    "/users/stats",
    responses={
        200: {"model": UserStats, "description": "User statistics"},
    },
    tags=["users"],
    summary="Get user statistics (COUNT, AVG)",
    response_model_by_alias=True,
)
async def get_user_stats(
) -> UserStats:
    if not BaseUsersApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUsersApi.subclasses[0]().get_user_stats()
