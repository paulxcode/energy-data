import pandas as pd
import numpy as np
import json
import os
import warnings
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

CSV_PATH = os.path.join(os.path.dirname(__file__), "electricityConsumptionAndProductioction.csv")
DATA_JS_PATH = os.path.join(os.path.dirname(__file__), "data.js")

df = pd.read_csv(CSV_PATH, parse_dates=["DateTime"])
df = df.sort_values("DateTime").reset_index(drop=True)

# Data Validation & Cleaning
print("🔍 Data Validation Report:")
print("=" * 60)

# Check for negative values (clean wind values)
negative_wind = (df["Wind"] < 0).sum()
if negative_wind > 0:
    print(f"⚠️  Found {negative_wind} negative wind values, setting to 0")
    df.loc[df["Wind"] < 0, "Wind"] = 0

# Check data continuity
df["Year"] = df["DateTime"].dt.year
df["Month"] = df["DateTime"].dt.month
df["Hour"] = df["DateTime"].dt.hour
df["MonthName"] = df["DateTime"].dt.month_name()
df["Date"] = df["DateTime"].dt.date

# Alert on incomplete years
year_counts = df["Year"].value_counts().sort_index()
for year, count in year_counts.items():
    expected = 8784 if year % 4 == 0 else 8760  # leap year
    if count < expected - 100:
        print(f"⚠️  Year {year}: only {count} records (expected ~{expected})")

total_records = len(df)
date_min = df["DateTime"].min().strftime("%Y-%m-%d")
date_max = df["DateTime"].max().strftime("%Y-%m-%d")
print(f"✓ Date range: {date_min} to {date_max}")
print(f"✓ Total records: {total_records:,}")
print("=" * 60 + "\n")

total_consumption = int(df["Consumption"].sum())
total_production = int(df["Production"].sum())
avg_hourly_consumption = round(df["Consumption"].mean(), 1)
avg_hourly_production = round(df["Production"].mean(), 1)
peak_consumption_row = df.loc[df["Consumption"].idxmax()]
peak_consumption_val = int(peak_consumption_row["Consumption"])
peak_consumption_time = peak_consumption_row["DateTime"].strftime("%Y-%m-%d %H:%M")
peak_production_row = df.loc[df["Production"].idxmax()]
peak_production_val = int(peak_production_row["Production"])
peak_production_time = peak_production_row["DateTime"].strftime("%Y-%m-%d %H:%M")

source_cols = ["Nuclear", "Wind", "Hydroelectric", "Oil and Gas", "Coal", "Solar", "Biomass"]
production_total = df["Production"].sum()
source_pct = {s: round(df[s].sum() / production_total * 100, 1) for s in source_cols}

df["NetFlow"] = df["Production"] - df["Consumption"]
total_export_hours = int((df["NetFlow"] > 0).sum())
total_import_hours = int((df["NetFlow"] < 0).sum())
self_sufficiency_pct = round((total_production / total_consumption) * 100, 1)

df["Renewable"] = df["Wind"] + df["Solar"] + df["Hydroelectric"] + df["Biomass"]
df["RenewablePct"] = (df["Renewable"] / df["Production"] * 100).round(1)

charts = {}
template = "plotly_dark"
font_cfg = dict(color="#e2e8f0")
paper_bg = "rgba(0,0,0,0)"
px_kwargs = dict(template=template)


def apply_layout(fig):
    fig.update_layout(paper_bgcolor=paper_bg, font=font_cfg, margin=dict(l=40, r=20, t=40, b=40))
    return fig


# Chart 1: Consumption & Production over time
fig_cp = go.Figure()
fig_cp.add_trace(go.Scatter(x=df["DateTime"], y=df["Consumption"], mode="lines", name="Consumption", line=dict(color="#636efa", width=1)))
fig_cp.add_trace(go.Scatter(x=df["DateTime"], y=df["Production"], mode="lines", name="Production", line=dict(color="#f59e0b", width=1)))
fig_cp.update_layout(title="Hourly Consumption & Production (MW)", xaxis_title="", yaxis_title="MW", hovermode="x unified", **px_kwargs)
apply_layout(fig_cp)
charts["consumption_production"] = fig_cp.to_dict()

# Chart 2: Energy mix stacked area
fig_mix = go.Figure()
colors_mix = {"Nuclear": "#ef4444", "Wind": "#22c55e", "Hydroelectric": "#3b82f6", "Oil and Gas": "#f97316", "Coal": "#a1a1aa", "Solar": "#eab308", "Biomass": "#8b5cf6"}
for s in source_cols:
    fig_mix.add_trace(go.Scatter(x=df["DateTime"], y=df[s], mode="none", stackgroup="one", name=s, line=dict(width=0.5), fillcolor=colors_mix[s]))
fig_mix.update_layout(title="Energy Mix Over Time (MW by Source)", hovermode="x unified", **px_kwargs)
apply_layout(fig_mix)
charts["energy_mix"] = fig_mix.to_dict()

# Chart 3: Energy mix donut (latest year)
latest_year = df["Year"].max()
df_year = df[df["Year"] == latest_year]
year_source_totals = {s: int(df_year[s].sum()) for s in source_cols}
labels_donut = [f"{s} ({year_source_totals[s]:,} MW)" for s in source_cols]
values_donut = [year_source_totals[s] for s in source_cols]
colors_donut = [colors_mix[s] for s in source_cols]
fig_donut = go.Figure(data=[go.Pie(labels=labels_donut, values=values_donut, hole=0.45, marker=dict(colors=colors_donut))])
fig_donut.update_layout(title=f"Energy Mix ({latest_year})", **px_kwargs, showlegend=False)
apply_layout(fig_donut)
charts["energy_mix_donut"] = fig_donut.to_dict()

# Chart 4: Import/Export net flow (monthly)
monthly_net = df.groupby(["Year", "Month"])["NetFlow"].sum().reset_index()
monthly_net["Label"] = monthly_net.apply(lambda r: f"{r['Year']}-{int(r['Month']):02d}", axis=1)
bar_colors = monthly_net["NetFlow"].apply(lambda v: "#22c55e" if v > 0 else "#ef4444")
fig_flow = go.Figure(data=[go.Bar(x=monthly_net["Label"], y=(monthly_net["NetFlow"] / 1000000), marker_color=bar_colors)])
fig_flow.update_layout(title="Monthly Net Flow (GWh, positive = export)", xaxis_title="", yaxis_title="GWh", hovermode="x unified", **px_kwargs)
apply_layout(fig_flow)
charts["net_flow"] = fig_flow.to_dict()

# Chart 5: Hourly heatmap (consumption)
hourly_monthly = df.groupby(["Month", "Hour"])["Consumption"].mean().reset_index()
heatmap_data = hourly_monthly.pivot(index="Hour", columns="Month", values="Consumption")
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
fig_heat = go.Figure(data=go.Heatmap(z=heatmap_data.values, x=month_names, y=list(range(24)), colorscale="Viridis", colorbar=dict(title="MW")))
fig_heat.update_layout(title="Avg Hourly Consumption by Month (MW)", xaxis_title="Month", yaxis_title="Hour of Day", **px_kwargs)
apply_layout(fig_heat)
charts["hourly_heatmap"] = fig_heat.to_dict()

# Chart 6: Solar & Wind over time
fig_renew = go.Figure()
fig_renew.add_trace(go.Scatter(x=df["DateTime"], y=df["Solar"], mode="lines", name="Solar", line=dict(color="#eab308", width=1)))
fig_renew.add_trace(go.Scatter(x=df["DateTime"], y=df["Wind"], mode="lines", name="Wind", line=dict(color="#22c55e", width=1)))
fig_renew.update_layout(title="Solar & Wind Production (MW)", xaxis_title="", yaxis_title="MW", hovermode="x unified", **px_kwargs)
apply_layout(fig_renew)
charts["solar_wind"] = fig_renew.to_dict()

# Chart 7: Diurnal profiles (summer vs winter for solar & wind)
summer_months = [6, 7, 8]
winter_months = [12, 1, 2]
summer_solar = df[df["Month"].isin(summer_months)].groupby("Hour")["Solar"].mean()
winter_solar = df[df["Month"].isin(winter_months)].groupby("Hour")["Solar"].mean()
summer_wind = df[df["Month"].isin(summer_months)].groupby("Hour")["Wind"].mean()
winter_wind = df[df["Month"].isin(winter_months)].groupby("Hour")["Wind"].mean()

fig_diurnal = make_subplots(rows=1, cols=2, subplot_titles=("Solar: Summer vs Winter", "Wind: Summer vs Winter"), shared_yaxes=False)
fig_diurnal.add_trace(go.Scatter(x=summer_solar.index, y=summer_solar.values, mode="lines+markers", name="Solar Summer", line=dict(color="#eab308")), row=1, col=1)
fig_diurnal.add_trace(go.Scatter(x=winter_solar.index, y=winter_solar.values, mode="lines+markers", name="Solar Winter", line=dict(color="#f97316")), row=1, col=1)
fig_diurnal.add_trace(go.Scatter(x=summer_wind.index, y=summer_wind.values, mode="lines+markers", name="Wind Summer", line=dict(color="#22c55e")), row=1, col=2)
fig_diurnal.add_trace(go.Scatter(x=winter_wind.index, y=winter_wind.values, mode="lines+markers", name="Wind Winter", line=dict(color="#3b82f6")), row=1, col=2)
fig_diurnal.update_layout(title="Diurnal Profiles (Hourly Average, MW)", **px_kwargs)
apply_layout(fig_diurnal)
fig_diurnal.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99))
charts["diurnal_profiles"] = fig_diurnal.to_dict()

# Chart 8: Monthly renewable output (stacked bar)
monthly_renewable = df.groupby(["Year", "Month"])[["Solar", "Wind", "Hydroelectric"]].sum().reset_index()
monthly_avg_solar = monthly_renewable.groupby("Month")["Solar"].mean()
monthly_avg_wind = monthly_renewable.groupby("Month")["Wind"].mean()
monthly_avg_hydro = monthly_renewable.groupby("Month")["Hydroelectric"].mean()

fig_monthly = go.Figure()
fig_monthly.add_trace(go.Bar(x=month_names, y=monthly_avg_solar.values, name="Solar", marker_color="#eab308"))
fig_monthly.add_trace(go.Bar(x=month_names, y=monthly_avg_wind.values, name="Wind", marker_color="#22c55e"))
fig_monthly.add_trace(go.Bar(x=month_names, y=monthly_avg_hydro.values, name="Hydroelectric", marker_color="#3b82f6"))
fig_monthly.update_layout(title="Avg Monthly Renewable Production by Source (MW)", xaxis_title="", yaxis_title="MW", barmode="stack", **px_kwargs)
apply_layout(fig_monthly)
charts["monthly_renewable"] = fig_monthly.to_dict()

# Chart 9: Baseload vs intermittent
fig_base = go.Figure()
fig_base.add_trace(go.Scatter(x=df["DateTime"], y=df["Nuclear"], mode="lines", name="Nuclear (Baseload)", line=dict(color="#ef4444", width=1)))
fig_base.add_trace(go.Scatter(x=df["DateTime"], y=df["Solar"] + df["Wind"], mode="lines", name="Solar + Wind (Intermittent)", line=dict(color="#22c55e", width=1)))
fig_base.update_layout(title="Baseload (Nuclear) vs Intermittent (Solar + Wind)", xaxis_title="", yaxis_title="MW", hovermode="x unified", **px_kwargs)
apply_layout(fig_base)
charts["baseload_vs_intermittent"] = fig_base.to_dict()

# Chart 10: Renewable share trend
monthly_renewable_pct = df.groupby(["Year", "Month"])[["RenewablePct"]].mean().reset_index()
monthly_renewable_pct["Label"] = monthly_renewable_pct.apply(lambda r: f"{int(r['Year'])}-{int(r['Month']):02d}", axis=1)
fig_share = go.Figure(data=[go.Scatter(x=monthly_renewable_pct["Label"], y=monthly_renewable_pct["RenewablePct"], mode="lines+markers", line=dict(color="#22c55e", width=2))])
fig_share.update_layout(title="Monthly Renewable Share of Production (%)", xaxis_title="", yaxis_title="% Renewable", hovermode="x unified", **px_kwargs)
fig_share.update_xaxes(tickangle=45, nticks=20)
apply_layout(fig_share)
charts["renewable_share"] = fig_share.to_dict()

# Compute variability metrics
variability = {}
for s in source_cols:
    by_season = df.copy()
    by_season["Season"] = by_season["Month"].map({12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring", 6: "Summer", 7: "Summer", 8: "Summer", 9: "Fall", 10: "Fall", 11: "Fall"})
    season_stats = by_season.groupby("Season")[s].agg(["mean", "std", "min", "max"]).round(1)
    season_stats["cv"] = (season_stats["std"] / season_stats["mean"] * 100).round(1)
    variability[s] = season_stats.to_dict()

data = {
    "total_records": total_records,
    "date_range": f"{date_min} to {date_max}",
    "total_consumption": total_consumption,
    "total_production": total_production,
    "avg_hourly_consumption": avg_hourly_consumption,
    "avg_hourly_production": avg_hourly_production,
    "peak_consumption_val": peak_consumption_val,
    "peak_consumption_time": peak_consumption_time,
    "peak_production_val": peak_production_val,
    "peak_production_time": peak_production_time,
    "source_pct": source_pct,
    "self_sufficiency_pct": self_sufficiency_pct,
    "total_export_hours": total_export_hours,
    "total_import_hours": total_import_hours,
    "latest_year": latest_year,
    "variability": variability,
    "charts": charts,
}

js_content = f"window.SITE_DATA = {json.dumps(data, default=str)};"

os.makedirs(os.path.dirname(DATA_JS_PATH), exist_ok=True)
with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
    f.write(js_content)

print(f"Exported data to {DATA_JS_PATH}")
print(f"File size: {os.path.getsize(DATA_JS_PATH):,} bytes")
