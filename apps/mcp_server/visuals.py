import json
from typing import Literal
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs_version

# Pin the renderer to the plotly.js build that produced the spec. jsDelivr mirrors npm,
# so every release resolves; cdnjs lags and has empty entries for some versions.
PLOTLY_JS_URL = f"https://cdn.jsdelivr.net/npm/plotly.js-dist-min@{get_plotlyjs_version()}/plotly.min.js"

POWER_DURATIONS = [5, 15, 30, 60, 120, 300, 1200]
CATEGORICAL_PALETTE = [
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
    "#e87ba4", "#008300", "#4a3aa7", "#e34948",
]
POWER_METRICS = {
    "wkg": {"column": "wkg_{}".format, "y_title": "Power (W/kg)", "value_format": ".2f", "unit": "W/kg"},
    "watts": {"column": "watts_{}".format, "y_title": "Power (watts)", "value_format": ".0f", "unit": "W"},
}


def format_duration(seconds: int) -> str:
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def figure_payload(fig: go.Figure) -> dict:
    """
    Wrap a figure with the plotly.js script that must render it.
    to_json handles numpy/decimal types that a plain to_dict would leave unserialisable.
    """
    return {"plotly_js_url": PLOTLY_JS_URL, "figure": json.loads(fig.to_json())}


def power_curve(riders: list[dict], metric: Literal["wkg", "watts"] = "wkg") -> dict:
    """
    Build a power curve figure with one line per rider across POWER_DURATIONS.
    Expects rows from core.riders; returns the figure_payload for it.
    """
    spec = POWER_METRICS[metric]
    x = [format_duration(d) for d in POWER_DURATIONS]

    fig = go.Figure()
    for i, rider in enumerate(riders):
        fig.add_trace(go.Scatter(
            x=x,
            y=[rider[spec["column"](d)] for d in POWER_DURATIONS],
            name=rider["rider"],
            mode="lines+markers",
            line=dict(width=2, color=CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)]),
            marker=dict(size=8),
            hovertemplate=f"<b>{rider['rider']}</b><br>%{{x}}: %{{y:{spec['value_format']}}} {spec['unit']}<extra></extra>",
        ))

    fig.update_xaxes(type="category", title_text="Duration (mm:ss)")
    fig.update_yaxes(title_text=spec["y_title"])
    fig.update_layout(title="Power curve", hovermode="x unified")

    return figure_payload(fig)
