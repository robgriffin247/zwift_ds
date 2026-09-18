from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import APIKeyHeader
import duckdb
from enum import Enum
import os
import secrets

app = FastAPI()

API_TOKEN = os.getenv("ZWIFT_DS_API_TOKEN")
DATABASE = f"md:zwift_ds_prod?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}" if os.getenv("TARGET")=="prod" else "data/zwift_ds_dev.duckdb" 

api_key_header = APIKeyHeader(name="X-API-Key")

class CoreTables(str, Enum):
    riders = "riders"

async def verify_token(api_key: str = Depends(api_key_header)) -> None:
    if not API_TOKEN or not secrets.compare_digest(api_key, API_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

@app.get("/")
async def root():
    return {"content": "Hello, Zwifter! Checkout the /docs endpoint :)"}


@app.get("/{table}")
async def get_table(table: CoreTables, _: None = Depends(verify_token)):
    with duckdb.connect(DATABASE) as con:
        data = con.sql(f"select * from core.{table.value} where rider_id=4598636").pl()

    return {"content": data.to_dicts()}
