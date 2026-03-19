# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from loadtest_api_generated.apis.health_api_base import BaseHealthApi
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
from loadtest_api_generated.models.health_response import HealthResponse


router = APIRouter()

ns_pkg = loadtest_api_generated.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/health",
    responses={
        200: {"model": HealthResponse, "description": "OK"},
    },
    tags=["health"],
    summary="Health check endpoint",
    response_model_by_alias=True,
)
async def health_check(
) -> HealthResponse:
    if not BaseHealthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseHealthApi.subclasses[0]().health_check()
