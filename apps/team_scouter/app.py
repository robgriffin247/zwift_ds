import streamlit as st
import httpx
import polars as pl
import plotly.express as px
from collections import Counter
import os

API_URL = "https://robgriffin247-zwift-ds--zwift-ds-api-fastapi-app.modal.run" if os.getenv("TARGET") == "prod" else "http://127.0.0.1:8000"
API_TOKEN = os.getenv("ZWIFT_DS_API_TOKEN")

if "riders" not in st.session_state:
    response = httpx.get(f"{API_URL}/riders", headers={"X-API-Key": API_TOKEN})
    response.raise_for_status()
    st.session_state["riders"] = pl.DataFrame(response.json()["content"])

data = st.session_state["riders"]

POWER_DURATIONS = [5, 15, 30, 60, 120, 300, 1200]
CATEGORICAL_PALETTE = [
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
    "#e87ba4", "#008300", "#4a3aa7", "#e34948",
]


def format_duration(seconds: int) -> str:
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


METRICS = {
    "Power (W/kg)": {
        "column": "wkg_{}".format,
        "keys": POWER_DURATIONS,
        "x_label": format_duration,
        "value_format": ".2f",
        "unit": "w/kg",
        "y_title": "Power (W/kg)",
    },
    "Power (W)": {
        "column": "watts_{}".format,
        "keys": POWER_DURATIONS,
        "x_label": format_duration,
        "value_format": ".0f",
        "unit": "W",
        "y_title": "Power (watts)",
    },
    "Phenotype Score": {
        "column": "phenotype_{}".format,
        "keys": ["sprinter", "puncheur", "pursuiter", "climber", "timetrialist"],
        "x_label": str.capitalize,
        "value_format": ".2f",
        "unit": "",
        "y_title": "Phenotype Score",
    },
    "Velo Handicap": {
        "column": "handicap_{}".format,
        "keys": ["flat", "rolling", "hilly", "mountainous"],
        "x_label": str.capitalize,
        "value_format": ".2f",
        "unit": "",
        "y_title": "Velo Handicap",
    },
    "Velo Factor": {
        "column": "velo_factor_{}".format,
        "keys": ["sprint", "punch", "pursuit", "climb", "time_trial"],
        "x_label": lambda k: k.replace("_", " ").capitalize(),
        "value_format": ".2f",
        "unit": "",
        "y_title": "Velo Factor",
    },
}


def build_rider_labels(df: pl.DataFrame) -> dict[int, str]:
    """
    Map rider_id to a display label: rider name, then club if the name is not
    unique, then rider_id too if name & club is not unique either.
    """
    riders = {i["rider_id"]: (i["rider"], i["club"]) for i in df.iter_rows(named=True)}
    name_counts = Counter(name for name, _ in riders.values())
    name_club_counts = Counter(riders.values())

    def label(rid):
        name, club = riders[rid]
        if name_counts[name] == 1:
            return name
        if name_club_counts[(name, club)] == 1:
            return f"{name}, {club}"
        return f"{name}, {club} ({rid})"

    return {rid: label(rid) for rid in riders}


def select_teams(labels: dict[int, str]):
    """Multiselect two teams of riders, return them as one dataframe tagged with team number."""
    c1, c2 = st.columns(2)
    team1 = c1.multiselect("Team 1", key="team1_riders", options=labels.keys(), format_func=lambda rid: labels[rid])
    team2 = c2.multiselect("Team 2", key="team2_riders", options=labels.keys(), format_func=lambda rid: labels[rid])

    df = pl.concat([
        data.filter(pl.col("rider_id").is_in(team1)).with_columns(team=pl.lit(1)),
        data.filter(pl.col("rider_id").is_in(team2)).with_columns(team=pl.lit(2)),
    ])

    return df


def rider_comparison_charts(df: pl.DataFrame, labels: dict[int, str]):
    """Plot a chosen metric across its categories, coloured by rider and dashed by team."""
    metric_label = st.session_state.get("power_metric", "Power (W/kg)")
    split_by_team = st.session_state.get("split_by_team", False)
    metric = METRICS[metric_label]

    col_to_key = {metric["column"](key): key for key in metric["keys"]}
    key_to_label = {key: metric["x_label"](key) for key in metric["keys"]}
    category_order = list(key_to_label.values())
    unit_suffix = f" {metric['unit']}" if metric["unit"] else ""

    long_df = (
        df.select("rider_id", "team", *col_to_key.keys())
        .unpivot(index=["rider_id", "team"], variable_name="metric_col", value_name="value")
        .with_columns(
            pl.col("metric_col").replace_strict(col_to_key).alias("key"),
            pl.col("team").cast(pl.Utf8),
            pl.col("rider_id").replace_strict(labels).alias("rider"),
        )
        .with_columns(pl.col("key").replace_strict(key_to_label).alias("category"))
    )

    fig = px.line(
        long_df.to_pandas(),
        x="category",
        y="value",
        color="rider",
        line_dash="team",
        line_dash_map={"1": "solid", "2": "dash"},
        facet_col="team" if split_by_team else None,
        category_orders={"category": category_order},
        color_discrete_sequence=CATEGORICAL_PALETTE,
        markers=True,
        hover_name="rider",
        labels={"category": "", "value": metric["y_title"], "rider": "Rider", "team": "Team"},
    )
    fig.update_traces(
        marker=dict(size=8),
        line=dict(width=2),
        hovertemplate=f"<b>%{{hovertext}}</b><br>%{{y:{metric['value_format']}}}{unit_suffix}<extra></extra>",
    )
    fig.update_xaxes(type="category", title_text=None)
    fig.update_layout(showlegend=False)
    fig.for_each_annotation(lambda a: a.update(text=""))
    st.plotly_chart(fig, width="content")

    c1, c2 = st.columns(2)
    c1.toggle("Split by team", key="split_by_team")
    c2.selectbox("Metric", options=list(METRICS.keys()), key="power_metric")


labels = build_rider_labels(data)
df = select_teams(labels)

if df.shape[0] > 0:
    st.write(df)
    rider_comparison_charts(df, labels)
