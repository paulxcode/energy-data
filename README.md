# Romania Energy Analysis

An interactive data exploration of **62,810 hourly electricity records** from Romania's national grid covering 2019–2025 (with partial 2026). All charts and data are precomputed into a single file — no server, no database, no API calls. Just open the page and explore.

**Live demo:** [.vercel.app]

---

## Sections

### Consumption & Production Over Time

Hourly electricity consumption and production trends. Peak consumption reached 11,986 MW during winter mornings.

### Production by Energy Source

Energy mix composition showing the contribution of 7 sources over time. Nuclear provides stable baseload at ~20%, while renewables make up 44% of production.

### Energy Mix Breakdown

Monthly renewable production trends and baseload vs intermittent comparison. Seasonality is visible across all sources.

### Renewable Energy Analysis

Solar and wind production patterns with seasonal variations. Wind is strongest in winter, solar peaks in summer — they complement each other.

### Import/Export & Grid Balance

Net energy flow showing periods of export (surplus) vs import (deficit). Romania is 97.4% self-sufficient.

---

## How It Works (Step by Step)

This project has two parts:

1. **A Python script** that reads a CSV file and produces a data file
2. **A web page** that reads that data file and displays charts

### 1. The Data

The raw data comes from hourly electricity consumption and production records from Romania's national grid. It is a single CSV file (`electricityConsumptionAndProductioction.csv`) containing:

- **DateTime** — hourly timestamps from 2019–2026
- **Consumption** — total electricity consumption in MW
- **Production** — total electricity production in MW
- **7 energy sources** — Nuclear, Hydroelectric, Wind, Solar, Coal, Oil & Gas, Biomass

CSV is a plain-text format that Python can read with a single function call.

### 2. `export_data.py` — The Pipeline

`export_data.py` is a Python script that:

1. Reads the CSV file
2. Parses datetime and extracts time features (year, month, hour, season)
3. Cleans data quality issues (negative wind values set to 0)
4. Computes aggregate statistics (total production, average consumption, peak loads)
5. Calculates energy source percentages and self-sufficiency metrics
6. Generates 10 interactive Plotly charts
7. Packages everything into a single JavaScript file called `data.js`

Here is how it reads the data:

```python
df = pd.read_csv("electricityConsumptionAndProductioction.csv")
df["DateTime"] = pd.to_datetime(df["DateTime"])
```

And how it computes the renewable share:

```python
df["Renewable"] = df["Solar"] + df["Wind"] + df["Hydroelectric"] + df["Biomass"]
df["RenewablePct"] = (df["Renewable"] / df["Production"]) * 100
```

### 3. How the Charts Are Made

The script uses **Plotly**, a Python charting library. It creates each chart (line charts, stacked area charts, donut charts, heatmaps) and converts every chart into a JSON object — a plain text description of the chart's data and layout.

These JSON chart objects get stored in a dictionary:

```python
charts["consumption_production"] = fig_cp.to_dict()
charts["energy_mix"] = fig_mix.to_dict()
charts["energy_mix_donut"] = fig_donut.to_dict()
# ... and so on for every chart
```

### 4. `data.js` — The Bridge

The script dumps every statistic and every chart into a single JavaScript file:

```python
js_content = f"window.SITE_DATA = {json.dumps(data, cls=PlotlyJSONEncoder)};"
```

This creates a global variable `window.SITE_DATA` that contains everything the web page needs. The file is large enough to hold 10 charts and all metrics, small enough to load instantly.

### 5. `index.html` — The Frontend

The web page is a single HTML file. It does three things:

1. Loads `data.js` (which sets `window.SITE_DATA`)
2. Loads Plotly.js from CDN (a free library for rendering charts)
3. Renders each chart by passing the precomputed JSON to Plotly

```javascript
const DATA = window.SITE_DATA;
const CHARTS = DATA.charts;
Plotly.newPlot("cpChart", CHARTS.consumption_production.data, CHARTS.consumption_production.layout);
```

No server, no database, no API. Everything runs in the browser.

---

## Project Structure

```
energyData/
  index.html                                   The web page
  style.css                                    All colors, fonts, and layout
  data.js                                      Precomputed data (statistics + charts)
  export_data.py                               Python script that generates data.js
  electricityConsumptionAndProductioction.csv  Source data (hourly records)
  requirements.txt                             Python dependencies
  vercel.json                                  Configuration for deploying to Vercel
  package.json                                 npm metadata
  README.md                                    This file
```

---

## Data Source

Hourly electricity consumption and production data from Romania's national grid. Covers 2019–2025 (complete years) with partial 2026 data.

The 7 energy sources tracked:

| Source | Description |
|--------|-------------|
| Nuclear | Cernavodă Nuclear Power Plant |
| Hydroelectric | Run-of-river and reservoir hydro |
| Wind | Onshore wind farms |
| Solar | Photovoltaic installations |
| Coal | Lignite and hard coal plants |
| Oil & Gas | Thermal power plants |
| Biomass | Organic material power generation |

---

## Data Quality

Real-world datasets contain imperfections. This analysis handles several known issues:

| Issue | Count | Action | Impact |
|-------|-------|--------|--------|
| Negative wind values | 696 | Cleaned to 0 | Wind data is more reliable |
| Solar zero values | 30,049 (47.8%) | Kept as-is | Occurs during night hours |
| Production mismatch | Mean 7.33 MW | Documented | May indicate missing sources |
| Data gaps | 90 hours | Noted | <0.15% of dataset |
| Incomplete 2026 | 1,752 records | Included with note | ~20% of expected 2026 |

**Recommendation:** Use data for 2019–2025 for reliable analysis. Treat 2026 as preliminary.

---

## How to Run Locally

The site works immediately — just open `index.html` in any browser. No installation needed.

### To Regenerate the Data (Optional)

If you want to re-run the data pipeline:

1. Install Python dependencies:

```bash
pip install pandas numpy plotly
```

2. Run the pipeline:

```bash
python export_data.py
```

3. Refresh `index.html` in your browser

### Deploy to Vercel

```bash
vercel --prod
```

Vercel will run `python export_data.py` as a build step and serve the static site. No server required.

---

## Built With

- **Python** — data processing and analysis
- **Pandas & NumPy** — data wrangling and statistics
- **Plotly** — interactive charts
- **Vanilla HTML, CSS, JavaScript** — frontend (no frameworks)
