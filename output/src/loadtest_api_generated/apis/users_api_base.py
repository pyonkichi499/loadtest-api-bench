# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field
from typing import List, Optional
from typing_extensions import Annotated
from uuid import UUID
from loadtest_api_generated.models.error_response import ErrorResponse
from loadtest_api_generated.models.user import User
from loadtest_api_generated.models.user_stats import UserStats


class BaseUsersApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseUsersApi.subclasses = BaseUsersApi.subclasses + (cls,)
    async def get_user_by_id(
        self,
        user_id: UUID,
    ) -> User:
        ...


    async def list_users(
        self,
        limit: Optional[Annotated[int, Field(le=1000, strict=True, ge=1)]],
    ) -> List[User]:
        ...


    async def search_users(
        self,
        name: Annotated[str, Field(min_length=1, strict=True)],
    ) -> List[User]:
        ...


    async def get_user_stats(
        self,
    ) -> UserStats:
        ...
