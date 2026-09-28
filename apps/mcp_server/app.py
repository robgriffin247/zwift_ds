import json
import os
from pathlib import Path
from typing import Literal
import duckdb
from fastmcp import FastMCP
from fastmcp.tools import ToolResult
from fastmcp.utilities.types import Image
from mcp.types import TextContent
from pydantic import BaseModel, Field
from apps.mcp_server.visuals import power_curve

mcp = FastMCP(
    "Zwift DS MCP Server",
    instructions=
    """
    Zwift DS is a data platform collecting data on the attributes of cyclists riding on Zwift.
    Begin by using discover() to see what tables and columns are available to use.
    Present all output directly in the chat as part of the conversation: prose and markdown tables.
    Charts returned by tools are already shown to the user in the tool result - never use web
    image search or embed other images to illustrate answers. Do not create artifacts, side panels,
    documents or HTML files unless the user explicitly asks for one.
    For ladder race strategy, ask the user for the route details first (see ladder_tactics) and
    give no analysis or advice until they have been provided.
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
def plot_power_curve(rider_ids: list[int], metric: Literal["wkg", "watts"] = "wkg") -> Image:
    """
    Plot power curves (5s to 20m) for up to 8 riders (get rider_id from search_riders).
    Returns a PNG image that the user already sees in the tool result - refer to it in your
    reply, but do not try to re-display it, search the web for images, or build an artifact.
    For ladder races, ladder_tactics already includes a team-by-team chart.
    """
    result = CON.execute("select * from core.riders where list_contains(?, rider_id)", [rider_ids])
    return Image(data=power_curve({"Power curve": _pack_result(result)}, metric), format="png")


class Team(BaseModel):
    name: str = Field(description="Team name as the user refers to it, e.g. 'Tea & Scone A'.")
    rider_ids: list[int] = Field(min_length=1, max_length=5, description="rider_id values from search_riders.")


@mcp.tool
def ladder_tactics(
    your_team: Team,
    opponents: Team,
    route: str = Field(description=(
        "The route details exactly as the user gave them (name/world, distance, laps, climbs, "
        "sprints, finish). Never invent, guess or look this up - ask the user first."
    )),
) -> ToolResult:
    """
    Ladder races are races with two teams of up to 5 riders per team.
    Points are given as 10 for first, 9 for 2nd, 8 for 3rd... and so on.
    Races are very tactical and riders need to know the strengths and weaknesses of the teams.
    Aerodynamic drafting can make a big difference so solo/pairs of riders will struggle to hold off a group.
    Advantages can, for example, come from attacking as groups/pairs or attacking on climbs where drag is of lesser importance (lower speeds).

    BEFORE calling this tool or giving any analysis or advice:
    1. Confirm the riders and name of each team (use search_riders, clarify ambiguous matches).
       your_team is the team the user is advising, opponents is the team they race against.
    2. Ask the user for the route details, e.g. route name/world, distance, laps, elevation,
       key climbs (length and gradient), sprints and where the finish is. Then wait for the answer.
       Do not guess or look up the route yourself, and do not give a preliminary rider
       comparison or strategy while waiting - ask the question and stop.

    Returns the rider data for both teams plus a PNG of their power curves, one panel per team.
    Compare the strengths and weaknesses of each team in the context of the route, suggest how
    your_team should go about trying to win, and what to expect/be wary of from opponents.
    Refer to the teams by name.

    The power curve chart is already visible to the user in the tool result; refer to it but do
    not re-display it or add web images. Write the answer directly in the chat as a normal
    conversational reply, not as an artifact, side panel, document or HTML report.
    Keep it concise and skimmable, e.g.:
    - a markdown table of each rider's key numbers (e.g. w/kg at 15s, 1m, 5m, 20m),
    - team strengths and weaknesses,
    - a plan for your_team by section of the route,
    - threats to watch from opponents.
    """
    if your_team.name == opponents.name:
        raise ValueError("The two teams need different names.")

    result = CON.execute("""
    select ? as team, * from core.riders where list_contains(?, rider_id)
    union all by name
    select ? as team, * from core.riders where list_contains(?, rider_id)
    """, [your_team.name, your_team.rider_ids, opponents.name, opponents.rider_ids])
    riders = _pack_result(result)

    chart = power_curve({
        team.name: [rider for rider in riders if rider["team"] == team.name]
        for team in (your_team, opponents)
    })
    return ToolResult(
        content=[
            TextContent(type="text", text=json.dumps({"route": route, "riders": riders}, default=str)),
            Image(data=chart, format="png").to_image_content(),
        ],
    )

if __name__=="__main__":
    mcp.run()
