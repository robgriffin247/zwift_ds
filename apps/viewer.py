import streamlit as st
import duckdb 
import polars as pl

with duckdb.connect("data/zwift_ds_dev.duckdb") as con:
    data = con.sql("select * from staging.stg_riders").pl()

riders = data.select(pl.col("rider").sort()).to_series().to_list()
selected_riders = st.multiselect("Rider", options=riders)
filtered_riders = selected_riders if len(selected_riders)>0 else riders

st.dataframe(data.filter(pl.col("rider").is_in(filtered_riders)))