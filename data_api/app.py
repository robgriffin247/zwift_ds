from fastapi import FastAPI, HTTPException
import duckdb

app = FastAPI()


@app.get("/")
async def root():
    return {"content": "Hello, Zwifter!"}


@app.get("/riders")
async def get_riders():
    with duckdb.connect("data/zwift_ds_dev.duckdb") as con:
        data = con.sql(f"select * from core.fct_riders").pl()
    _check_no_data(data)
    return {"content": data.to_dicts()}


@app.get("/riders/{rider_id}")
async def get_rider(rider_id):
    with duckdb.connect("data/zwift_ds_dev.duckdb") as con:
        data = con.sql(f"select * from core.fct_riders where rider_id={rider_id}").pl()
    _check_no_data(data)
    return {"content": data.to_dicts()}


def _check_no_data(data):
    if data.shape[0] == 0:
        raise HTTPException(status_code=404, detail="No data found")
