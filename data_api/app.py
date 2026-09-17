from fastapi import FastAPI, HTTPException
import duckdb
from enum import Enum
import os

app = FastAPI()

DATABASE = f"md:zwift_ds_prod?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}" if os.getenv("TARGET")=="prod" else "data/zwift_ds_dev.duckdb" 

class CoreTables(str, Enum):
    riders = "riders"


@app.get("/")
async def root():
    return {"content": "Hello, Zwifter! Checkout the /docs endpoint :)"}


@app.get("/{table}")
async def get_table(table: CoreTables):
    with duckdb.connect(DATABASE) as con:
        data = con.sql(f"select * from core.{table.value}").pl()

    return {"content": data.to_dicts()}
