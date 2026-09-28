import io
import re
from typing import Literal
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullLocator

POWER_DURATIONS = [5, 15, 30, 60, 120, 300, 1200]
CATEGORICAL_PALETTE = [
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
    "#e87ba4", "#008300", "#4a3aa7", "#e34948",
]
POWER_METRICS = {
    "wkg": {"column": "wkg_{}".format, "y_title": "Power (W/kg)"},
    "watts": {"column": "watts_{}".format, "y_title": "Power (W)"},
}

# Chart chrome, light theme: a PNG can't follow the viewer's theme, so it carries its own surface.
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

# Emoji and other symbols the chart font can't draw.
UNRENDERABLE = re.compile(r"[\U00010000-\U0010ffff☀-➿️]")


def format_duration(seconds: int) -> str:
    return f"{seconds}s" if seconds < 60 else f"{seconds // 60}m"


def display_name(rider: str) -> str:
    return " ".join(UNRENDERABLE.sub("", rider).split())


def _style_axes(ax, title: str, y_title: str | None):
    ax.set_facecolor(SURFACE)
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(FixedLocator(POWER_DURATIONS))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels([format_duration(d) for d in POWER_DURATIONS])
    ax.set_xlim(POWER_DURATIONS[0] * 0.85, POWER_DURATIONS[-1] * 1.15)
    ax.grid(axis="y", color=GRIDLINE, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.tick_params(colors=TEXT_MUTED, labelsize=9, length=0, pad=6)
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=TEXT_PRIMARY, pad=10)
    if y_title:
        ax.set_ylabel(y_title, color=TEXT_SECONDARY, fontsize=9)


def power_curve(
    groups: dict[str, list[dict]],
    metric: Literal["wkg", "watts"] = "wkg",
) -> bytes:
    """
    Render power curves as a PNG, one panel per group (e.g. per team) on a shared y-axis.
    Each panel draws its own riders in colour over the other panels' riders in faint grey,
    so riders can be compared within and across groups. Expects rows from core.riders.
    """
    spec = POWER_METRICS[metric]
    all_riders = [rider for riders in groups.values() for rider in riders]
    if any(len(riders) > len(CATEGORICAL_PALETTE) for riders in groups.values()):
        raise ValueError(f"At most {len(CATEGORICAL_PALETTE)} riders per group, split them into more groups or calls.")

    def curve(rider):
        return [rider[spec["column"](d)] for d in POWER_DURATIONS]

    fig, axes = plt.subplots(
        1, len(groups), sharey=True, squeeze=False,
        figsize=(5.2 * len(groups) + 0.8, 4.6), facecolor=SURFACE,
    )
    for i, (ax, (title, riders)) in enumerate(zip(axes[0], groups.items())):
        _style_axes(ax, title, spec["y_title"] if i == 0 else None)
        if len(groups) > 1:
            for other in (r for r in all_riders if r not in riders):
                ax.plot(POWER_DURATIONS, curve(other), color=BASELINE, linewidth=1, alpha=0.6, zorder=1)
        for j, rider in enumerate(riders):
            ax.plot(
                POWER_DURATIONS, curve(rider),
                label=display_name(rider["rider"]),
                color=CATEGORICAL_PALETTE[j], linewidth=2, zorder=2,
                marker="o", markersize=5, markeredgecolor=SURFACE, markeredgewidth=1.5,
            )
        legend = ax.legend(
            loc="upper right", frameon=False, fontsize=8.5,
            handlelength=1.2, labelcolor=TEXT_SECONDARY,
        )
        legend.set_zorder(3)

    fig.tight_layout(w_pad=2)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return buffer.getvalue()
