import logging
from logging.handlers import TimedRotatingFileHandler
from functools import lru_cache
from typing import List

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from starlette.responses import JSONResponse
from starlette.status import HTTP_204_NO_CONTENT, HTTP_422_UNPROCESSABLE_ENTITY
from univention.config_registry import (
    ConfigRegistry,
    handler_search,
    handler_set,
    handler_unset,
)

from . import __version__

LOG_FILE_PATH = "/var/log/univention/ucr-api.log"
URL_PREFIX_ROOT = "/ucr-api"
URL_PREFIX_UCR_RESSOURCE = f"{URL_PREFIX_ROOT}/ucr"

app = FastAPI(
    title="UCR API",
    description="UCR HTTP API",
    version=__version__,
    docs_url=f"{URL_PREFIX_ROOT}/docs",
    redoc_url=f"{URL_PREFIX_ROOT}/redoc",
    openapi_url=f"{URL_PREFIX_ROOT}/openapi.json",
    default_response_class=JSONResponse,
)
router = APIRouter()


class UCRVar(BaseModel):
    key: str
    value: str = None


def get_ucr() -> ConfigRegistry:
    ucr = ConfigRegistry()
    ucr.load()
    return ucr


@lru_cache(maxsize=1)
def get_logger() -> logging.Logger:
    return logging.getLogger(__name__)


@app.on_event("startup")
def setup_logging() -> None:
    for name in (
        None,
        "fastapi",
        "univention",
        "uvicorn.access",
        "uvicorn.error",
    ):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-5s %(module)s.%(funcName)s:%(lineno)d  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler = TimedRotatingFileHandler(LOG_FILE_PATH, when="D", backupCount=9)
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logger = logging.getLogger("uvicorn.access")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


@router.get("/", tags=["ucr"], response_model=List[UCRVar])
async def search(
    pattern: str = Query(
        default="",
        description="Pattern to search UCR variables with. If empty, all UCR "
        "variables will be returned. '.*' will be prepended / "
        "appended, if the pattern does not start / end with '^' / "
        "'$'.",
        min_length=2,
    )
) -> List[UCRVar]:
    try:
        ucr_vars = list(handler_search([pattern]))
    except SystemExit:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid pattern provided.")
    result = list()
    for ucr_var in ucr_vars:
        key, value = ucr_var.split(":", 1)
        value = value[1:] if value != " <empty>" else None
        result.append(UCRVar(key=key, value=value))
    return result


@router.get("/{key:path}", tags=["ucr"], response_model=UCRVar)
async def get(key: str, ucr: ConfigRegistry = Depends(get_ucr)) -> UCRVar:
    """
    Retrieve the value of a UCR variable.
    """
    ucr_value = ucr.get(key)
    return UCRVar(key=key, value=ucr_value)


@router.post("/", tags=["ucr"], response_model=List[UCRVar])
async def post(
    ucr_vars: List[UCRVar], ucr: ConfigRegistry = Depends(get_ucr),
    logger: logging.Logger = Depends(get_logger),
) -> List[UCRVar]:
    """
    Create / change one or more UCR variables.

    **ucr_vars**: A **list of UCRVar** objects to create or update. If the
        value is null, the UCR variable will be unset (deleted).
    """
    params_set = list()
    params_unset = list()
    for ucr_var in ucr_vars:
        if ucr_var.value:
            params_set.append(f"{ucr_var.key}={ucr_var.value}")
        else:
            params_unset.append(ucr_var.key)
    logger.info("set=%r unset=%r", params_set, params_unset)
    handler_set(params_set)
    handler_unset(params_unset)
    ucr.load()
    return [UCRVar(key=ucr_var.key, value=ucr.get(ucr_var.key)) for ucr_var in ucr_vars]


@router.put("/{key:path}", tags=["ucr"], response_model=UCRVar)
async def put(
    key: str, ucr_var: UCRVar, ucr: ConfigRegistry = Depends(get_ucr),
    logger: logging.Logger = Depends(get_logger),
) -> UCRVar:
    """
    Set or unset a UCR variable.

    **value**: The new value, null will unset (delete) the UCR variable
    """
    if ucr_var.key != key:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Key in body must match key in path (URL).")
    if isinstance(ucr_var.value, str):
        logger.info("handler_set([%r=%r])", ucr_var.key, ucr_var.value)
        handler_set([f"{ucr_var.key}={ucr_var.value}"])
    else:
        logger.info("handler_unset([%r])", ucr_var.key)
        handler_unset([ucr_var.key])
    ucr.load()
    ucr_value = ucr.get(ucr_var.key)
    return UCRVar(key=ucr_var.key, value=ucr_value)


@router.delete("/{key:path}", tags=["ucr"], status_code=HTTP_204_NO_CONTENT)
async def delete(key: str, logger: logging.Logger = Depends(get_logger)) -> None:
    """
    Unset (delete) a UCR variable.
    """
    logger.info("handler_unset([%r])", key)
    handler_unset([key])
    return None


app.include_router(router, prefix=URL_PREFIX_UCR_RESSOURCE)
