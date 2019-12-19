from typing import List

from fastapi import FastAPI, Depends, Query
from pydantic import BaseModel
from starlette.status import HTTP_201_CREATED
from univention.config_registry import ConfigRegistry

app = FastAPI()


class UCRVar(BaseModel):
    identifier: str
    value: str


def get_ucr():
    ucr = ConfigRegistry()
    ucr.load()
    return ucr


@app.get("/", response_model=List[UCRVar])
async def search(
    pattern_filter: str = Query(
        None,
        title="Pattern to match searched UCR variables to. List all if empty",
        min_length=2,
    ),
    ucr: ConfigRegistry = Depends(get_ucr),
):
    pass


@app.get("/{var_name}", response_model=List[UCRVar])
async def get(var_name: str, ucr: ConfigRegistry = Depends(get_ucr)) -> List[UCRVar]:
    pass


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
