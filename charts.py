import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw straight to image files
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

BASE = Path(__file__).resolve().parent
REPORT_DIR = BASE / "reports"
CHART_DIR = BASE / "charts"
CHART_DIR.mkdir(exist_ok=True)

# Colours: calm greys for text and grid, blue and orange for the data
SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE = "#2a78d6", "#eb6834"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def inr(x):
    """Format rupees as lakh / crore, e.g. 4190000 -> '₹41.9 L'."""
    if x >= 1e7:
        return f"₹{x / 1e7:.2f} Cr"
    if x >= 1e5:
        return f"₹{x / 1e5:.1f} L"
    return f"₹{x:,.0f}"


def style_axes(ax, grid_axis="y"):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def set_title(ax, text):
    ax.set_title(text, loc="left", fontsize=11, fontweight="bold", color=INK, pad=12)


def plot_monthly(ax, monthly):
    df = monthly.copy()
    df["year"] = df["month"].str[:4]
    df["mon"] = df["month"].str[5:].astype(int)
    style_axes(ax)
    for year, color in zip(sorted(df["year"].unique()), (BLUE, ORANGE)):
        d = df[df["year"] == year].sort_values("mon")
        ax.plot(d["mon"], d["revenue"], color=color, linewidth=2, marker="o", markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=year)
        ax.annotate(year, (d["mon"].iloc[-1], d["revenue"].iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=9, color=INK_2)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTHS)
    ax.set_xlim(0.6, 12.9)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1e5:.0f}"))
    ax.set_ylabel("Revenue (₹ lakh)", color=MUTED, fontsize=9)
    ax.legend(frameon=False, loc="upper left", fontsize=9, labelcolor=INK_2)
    set_title(ax, "Monthly revenue, year over year")


def plot_top_products(ax, top):
    d = top.sort_values("revenue")
    style_axes(ax, grid_axis=None)
    ax.barh(d["product_name"], d["revenue"], color=BLUE, height=0.62)
    for y, v in enumerate(d["revenue"]):
        ax.text(v, y, f"  {inr(v)}", va="center", fontsize=9, color=INK_2)
    ax.set_xlim(0, d["revenue"].max() * 1.22)
    ax.xaxis.set_visible(False)
    ax.tick_params(axis="y", colors=INK_2)
    ax.spines["bottom"].set_visible(False)
    set_title(ax, "Top 10 products by revenue")


def plot_category(ax, cat):
    style_axes(ax, grid_axis=None)
    labels = [textwrap.fill(c, 12) for c in cat["category"]]
    ax.bar(labels, cat["revenue"], color=BLUE, width=0.62)
    for x, v in enumerate(cat["revenue"]):
        ax.text(x, v, inr(v), ha="center", va="bottom", fontsize=9, color=INK_2)
    ax.set_ylim(0, cat["revenue"].max() * 1.15)
    ax.yaxis.set_visible(False)
    ax.tick_params(axis="x", colors=INK_2, labelsize=8.5)
    set_title(ax, "Revenue by category")


def plot_region(ax, reg):
    d = reg.sort_values("revenue")
    style_axes(ax, grid_axis=None)
    ax.barh(d["region"], d["revenue"], color=BLUE, height=0.62)
    for y, (v, share) in enumerate(zip(d["revenue"], d["revenue_share_pct"])):
        ax.text(v, y, f"  {inr(v)} ({share:.0f}%)", va="center", fontsize=9, color=INK_2)
    ax.set_xlim(0, d["revenue"].max() * 1.35)
    ax.xaxis.set_visible(False)
    ax.tick_params(axis="y", colors=INK_2)
    ax.spines["bottom"].set_visible(False)
    set_title(ax, "Revenue by region")


def main():
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURFACE})

    monthly = pd.read_csv(REPORT_DIR / "monthly_sales.csv")
    top = pd.read_csv(REPORT_DIR / "top_products.csv")
    cat = pd.read_csv(REPORT_DIR / "category_sales.csv")
    reg = pd.read_csv(REPORT_DIR / "region_sales.csv")

    # 1) four separate charts
    singles = {
        "monthly_revenue.png": (plot_monthly, monthly, (8, 4.6)),
        "top_products.png": (plot_top_products, top, (8, 5)),
        "category_revenue.png": (plot_category, cat, (8, 4.6)),
        "region_revenue.png": (plot_region, reg, (8, 4.2)),
    }
    for filename, (plot_fn, data, size) in singles.items():
        fig, ax = plt.subplots(figsize=size)
        plot_fn(ax, data)
        fig.tight_layout()
        fig.savefig(CHART_DIR / filename, dpi=150)
        plt.close(fig)

    # 2) one combined dashboard
    total_rev = monthly["revenue"].sum()
    total_orders = int(monthly["orders"].sum())
    margin = 100 * monthly["profit"].sum() / total_rev

    fig, axes = plt.subplots(2, 2, figsize=(14, 9.5))
    fig.subplots_adjust(left=0.08, right=0.97, bottom=0.06, top=0.77, hspace=0.38, wspace=0.30)
    plot_monthly(axes[0, 0], monthly)
    plot_top_products(axes[0, 1], top)
    plot_category(axes[1, 0], cat)
    plot_region(axes[1, 1], reg)

    fig.text(0.06, 0.955, "Sales Analytics Dashboard", fontsize=18, fontweight="bold", color=INK)
    fig.text(0.06, 0.925, f"{monthly['month'].iloc[0]} to {monthly['month'].iloc[-1]}  ·  "
                          f"{total_orders:,} validated orders", fontsize=10, color=MUTED)
    kpis = [("Total revenue", inr(total_rev)), ("Orders", f"{total_orders:,}"),
            ("Avg order value", inr(total_rev / total_orders)), ("Profit margin", f"{margin:.1f}%")]
    for i, (label, value) in enumerate(kpis):
        x = 0.06 + i * 0.235
        fig.text(x, 0.885, label, fontsize=9.5, color=MUTED)
        fig.text(x, 0.845, value, fontsize=20, fontweight="bold", color=INK)
    fig.savefig(CHART_DIR / "dashboard.png", dpi=150)
    plt.close(fig)

    print("Charts saved in:", CHART_DIR)


if __name__ == "__main__":
    main()