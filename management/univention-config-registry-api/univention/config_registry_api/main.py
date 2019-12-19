from typing import List

from fastapi import Body, Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from starlette.status import HTTP_201_CREATED
from univention.config_registry import (
    ConfigRegistry,
    handler_search,
    handler_set,
    handler_unset,
)
from . import __version__


URL_API_PREFIX = "ucr-api"

app = FastAPI(
    title="Kelvin API",
    description="UCS@school objects HTTP API",
    version=__version__,
    docs_url=f"{URL_API_PREFIX}/docs",
    redoc_url=f"{URL_API_PREFIX}/redoc",
    openapi_url=f"{URL_API_PREFIX}/openapi.json",
)


class UCRVar(BaseModel):
    key: str
    value: str = None


def get_ucr() -> ConfigRegistry:
    ucr = ConfigRegistry()
    ucr.load()
    return ucr


@app.get("ucr/", response_model=List[UCRVar])
async def search(
    pattern: str = Query(
        default="",
        description="Pattern to search UCR variables with. If empty, all UCR "
        "variables will be returned. '.*' will be prepended / "
        "appended, if the pattern does not start / end with '^' / "
        "'$'.",
        min_length=2,
    )
):
    try:
        ucr_vars = list(handler_search([pattern]))
    except SystemExit:
        raise HTTPException(status_code=400, detail="Invalid pattern provided.")
    result = list()
    for ucr_var in ucr_vars:
        key, value = ucr_var.split(":", 1)
        value = value[1:] if value != " <empty>" else None
        result.append(UCRVar(key=key, value=value))
    return result


@app.get("ucr/{key:path}", response_model=UCRVar)
async def get(key: str, ucr: ConfigRegistry = Depends(get_ucr)) -> UCRVar:
    """
    Retrieve the value of a UCR variable.
    """
    ucr_value = ucr.get(key)
    return UCRVar(key=key, value=ucr_value)


@app.post("ucr/", status_code=HTTP_201_CREATED, response_model=List[UCRVar])
async def post(
    ucr_vars: List[UCRVar], ucr: ConfigRegistry = Depends(get_ucr)
) -> List[UCRVar]:
    """
    Create / change one or more UCR variables.

    **ucr_vars**: A **list of UCRVar** objects to create or update. If the
        value is null, the UCR variable will be unset (deleted).
    """
    pass


@app.put("ucr/{key}", response_model=List[UCRVar])
async def put(
    key: str, value: str = Body(default=None), ucr: ConfigRegistry = Depends(get_ucr)
):
    """
    Set or unset a UCR variable.

    **value**: The new value, null will unset (delete) the UCR variable
    """
    if type(value) == str:
        handler_set([f"{key}={value}"])
    else:
        handler_unset([key])
    ucr.load()
    ucr_value = ucr.get(key)
    return UCRVar(key=key, value=ucr_value)


@app.delete("ucr/{key}")
async def delete(key: str, ucr: ConfigRegistry = Depends(get_ucr)):
    """
    Unset (delete) a UCR variable.
    """
    pass
