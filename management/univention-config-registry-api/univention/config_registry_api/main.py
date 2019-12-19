from typing import List

from fastapi import FastAPI, Depends, Query, HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_201_CREATED
from univention.config_registry import ConfigRegistry, handler_set, handler_search

app = FastAPI()


class UCRVar(BaseModel):
    identifier: str
    value: str = None


def get_ucr():
    ucr = ConfigRegistry()
    ucr.load()
    return ucr


@app.get("/", response_model=List[UCRVar])
async def search(
    pattern: str = Query(
        None,
        title="Pattern to match searched UCR variables to. List all if empty",
        min_length=2,
    )
):
    try:
        ucr_vars = handler_search(pattern)
    except SystemExit as exc:
        raise HTTPException(status_code=400, detail="Invalid pattern provided")
    result = list()
    for ucr_var in ucr_vars:
        identifier, value = ucr_var.split(":", 1)
        value = value[1:] if value != " <empty>" else None
        result.append(UCRVar(identifier=identifier, value=value))
    return result


@app.get("/{var_name:path}", response_model=UCRVar)
async def get(var_name: str, ucr: ConfigRegistry = Depends(get_ucr)) -> UCRVar:
    ucr_value = ucr.get(var_name)
    return UCRVar(identifier=var_name, value=ucr_value)


@app.post("/", status_code=HTTP_201_CREATED, response_model=List[UCRVar])
async def post(
    ucr_vars: List[UCRVar], ucr: ConfigRegistry = Depends(get_ucr)
) -> List[UCRVar]:
    pass


@app.put("/{var_name}", response_model=List[UCRVar])
async def put(var_name: str, ucr_var: UCRVar, ucr: ConfigRegistry = Depends(get_ucr)):
    pass


@app.delete("/{var_name}")
async def delete(var_name: str, ucr: ConfigRegistry = Depends(get_ucr)):
    pass
