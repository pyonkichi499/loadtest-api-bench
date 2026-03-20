from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from loadtest_api.dependencies import get_db_accessor
from loadtest_api.models.user import StatsSchema, UserSchema
from loadtest_api.repositories.base import DBAccessor

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/users/search", response_model=list[UserSchema])
async def search_users(
    name: Annotated[str, Query(min_length=1)],
    db: DBAccessor = Depends(get_db_accessor),
) -> list[UserSchema]:
    return await db.search_users(name=name)


@router.get("/users/stats", response_model=StatsSchema)
async def get_user_stats(
    db: DBAccessor = Depends(get_db_accessor),
) -> StatsSchema:
    return await db.get_stats()


@router.get("/users/{user_id}", response_model=UserSchema)
async def get_user_by_id(
    user_id: str,
    db: DBAccessor = Depends(get_db_accessor),
) -> UserSchema:
    user = await db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users", response_model=list[UserSchema])
async def list_users(
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    db: DBAccessor = Depends(get_db_accessor),
) -> list[UserSchema]:
    return await db.list_users(limit=limit)
