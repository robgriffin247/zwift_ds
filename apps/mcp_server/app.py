import os
from pathlib import Path
from typing import Literal
import duckdb
from fastmcp import FastMCP
from visuals import power_curve

mcp = FastMCP(
    "Zwift DS MCP Server",
    instructions=
    """
    Zwift DS is a data platform collecting data on the attributes of cyclists riding on Zwift.
    Begin by using discover() to see what tables and columns are available to use.
    """,
)

DATABASE = (
    f"md:zwift_ds_prod?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}"
    if os.getenv("TARGET") == "prod"
    else str(Path(__file__).resolve().parents[2] / "data/zwift_ds_dev.duckdb")
)

CON = duckdb.connect(DATABASE, read_only=True)

def _pack_result(result):
    columns = [col[0] for col in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]

@mcp.tool
def discover():
    """
    Use this tool to discover the database, getting information on production tables and columns.
    """
    result = CON.execute("select table_name, column_name, data_type from information_schema.columns where table_schema='core'")
    return _pack_result(result)


@mcp.tool
def search_riders(name: str | None = None):
    """
    Search riders by partial case-insensitive name matching.
    Returns a compact summary for the given rider matches or all riders if name is None.
    Clarify with the user which riders to use if more than one rider matches, before proceeding.
    Consider even variants of names like Rob and Robert, Tim and Timothy etc.
    """
    query = "select rider, rider_id, club from core.riders"
    params = []

    if name:
        query += " where rider ilike ?"
        params += [f"%{name}%"]

    result = CON.execute(query, params)
    
    return _pack_result(result)


@mcp.tool
def get_riders(rider_ids: list[int]):
    """
    Return detailed profile of a selected rider after getting rider_id from search_riders.
    """
    result = CON.execute("select * from core.riders where list_contains(?, rider_id)", [rider_ids])
    return _pack_result(result)


@mcp.tool
def plot_power_curve(rider_ids: list[int], metric: Literal["wkg", "watts"] = "wkg"):
    """
    Plot power curves for the given riders (get rider_id from search_riders).
    Returns {"plotly_js_url", "figure"}: a Plotly figure spec (data + layout) and the exact
    plotly.js script that renders it. Load plotly.js ONLY from plotly_js_url (never guess a
    version or CDN, other builds may be missing or incompatible), then call
    Plotly.newPlot(el, figure.data, figure.layout). Render as-is, e.g. in an artifact or a
    standalone HTML file, without restyling or recomputing the data.
    """
    result = CON.execute("select * from core.riders where list_contains(?, rider_id)", [rider_ids])
    return power_curve(_pack_result(result), metric)


@mcp.tool
def ladder_tactics(team_1_rider_ids: list[int], team_2_rider_ids: list[int], route_description: str) -> list[dict]:
    """
    Ladder races are races with two teams of up to 5 riders per team.
    Points are given as 10 for first, 9 for 2nd, 8 for 3rd... and so on.
    Races are very tactical and riders need to know the strengths and weaknesses of the teams.
    Aerodynamic drafting can make a big difference so solo/pairs of riders will struggle to hold off a group. 
    Advantages can, for example, come from attacking as groups/pairs or attacking on climbs where drag is of lesser importance (lower speeds).
    Help compare the strengths and weaknesses of each team, suggest how team 1 should go about trying to win, and what to expect/be wary of from team 2.
    Ask for and consider the route description in combination with the data on riders.
    Consider providing visuals including power curves.
    """
    result = CON.execute("""
    select 1 as team, * from core.riders where list_contains(?, rider_id)
    union all by name
    select 2 as team, * from core.riders where list_contains(?, rider_id)
    """, [team_1_rider_ids, team_2_rider_ids])
    return _pack_result(result)

if __name__=="__main__":
    mcp.run()