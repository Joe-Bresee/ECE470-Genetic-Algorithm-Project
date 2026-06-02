# ECE 470 Project Context: Avalanche Danger Predictor using Genetic Algorithm

---

## Recommended Region: Rogers Pass / Columbia Mountains (Glacier National Park, BC)

**Why Rogers Pass specifically, and not "all of BC":**

All of BC is far too broad. Terrain, climate, and snowpack character vary enormously from the Coast Mountains to the Rockies. A single model trained on all of BC would be weak everywhere. Focusing on one well-defined zone gives you consistent terrain type, a concentrated set of weather stations, and a much richer historical record.

Rogers Pass / Glacier National Park is the single best choice in Canada for this project for several reasons:

- **Parks Canada records approximately 2,000 avalanche activity events along the Trans-Canada corridor every year**, with continuous monitoring going back to the 1960s. This is one of the longest and most detailed avalanche records in the world.
- Rogers Pass averages **10 metres of snowfall per year at treeline** and has 155 days of snowfall annually — the Selkirk Mountains see more frequent and intense avalanche cycles than most of BC.
- The area has two primary long-term weather stations: **Rogers Pass Summit (1,315m)** with records back to 1965 and **Mt. Fidelity (1,905m)** with records back to the same year, giving 60 years of data.
- Parks Canada publishes daily public avalanche forecasts for the area; Avalanche Canada covers the broader Selkirks / Columbia Mountains forecast zone.
- More academic research papers use Rogers Pass data than any other Canadian location, which makes it easier to validate your results against published benchmarks.

Secondary option if Rogers Pass data access is difficult: the **Kootenay Pass** zone (Highway 3 corridor), which has a similarly long operational record and is managed by the BC Ministry of Transportation.

---

## What This Project Is

The goal is to build a model that predicts the **daily avalanche danger rating** (Low / Moderate / Considerable / High / Extreme — the standard 5-level North American Avalanche Danger Scale) for the Rogers Pass / Columbia Mountains forecast zone, given weather and snowpack input features.

This is a **classification problem**. The target label is the historical danger rating published by Parks Canada / Avalanche Canada. The input features are weather observations (new snow, temperature, wind, snowpack depth, etc.) from the same day and preceding days.

The role of the **Genetic Algorithm** is to optimize the model that makes these predictions — either by evolving the weights/thresholds of a rule-based classifier, or by performing feature selection and hyperparameter tuning for a machine learning model. This is the core AI technique required by ECE 470.

---

## What is a Genetic Algorithm (GA)?

A GA is a search and optimization method inspired by biological natural selection. It is part of Evolutionary Computation within AI — it is *not* machine learning and does not use gradient descent or backpropagation. It evolves a population of candidate solutions over many generations.

**Key concepts:**
- **Chromosome**: One encoded solution (e.g., a set of feature weights, or a set of decision thresholds)
- **Population**: Many candidate solutions evaluated at once
- **Fitness function**: A score for how good a solution is (e.g., prediction accuracy on validation data)
- **Selection**: Better-scoring solutions are more likely to become parents
- **Crossover**: Combine two parents to create children
- **Mutation**: Random small changes to prevent stagnation
- **Generation**: One full cycle; repeat until convergence

The GA is not "training" a neural network. It is searching for the best combination of parameters — a fundamentally different operation.

---

## Three Ways to Use GA in This Project

There are three legitimate framings for the GA's role, from simplest to most sophisticated. Your team should pick one and justify it clearly in the proposal.

### Option A — GA for Feature Weight Optimization (Recommended for ECE 470)

Build a weighted scoring rule that combines input features into a danger prediction. The chromosome is a vector of weights, one per feature. The GA evolves these weights to maximize classification accuracy on historical data.

Example: `danger_score = w1*(new_snow_24h) + w2*(temp_trend) + w3*(wind_speed) + w4*(snowpack_instability) + ...`

Map score ranges to danger levels (e.g., 0–20 = Low, 21–40 = Moderate, etc.).
GA evolves both the weights (w1, w2, ...) and the threshold boundaries simultaneously.

This is a clean, justified GA application. The chromosome is fully continuous, crossover and mutation are natural, and the fitness function is prediction accuracy.

### Option B — GA for Decision Tree Structure Optimization

Build a decision tree classifier where the GA evolves the tree's structure (which features to split on, at what thresholds). Each chromosome encodes a tree. Fitness = accuracy + parsimony (penalize overly complex trees).

More complex to implement but very well-suited to GA and very defensible in the proposal.

### Option C — GA as Hyperparameter Optimizer for a Classifier

Train an existing classifier (e.g., Random Forest, SVM, k-NN) but use the GA to find the optimal hyperparameters (number of trees, max depth, kernel type, etc.). Chromosome = hyperparameter vector. Fitness = cross-validated accuracy.

**Note for ECE 470:** This option is the weakest framing because the GA role is indirect — you are optimizing around ML, not replacing it. Make sure the proposal justifies why grid search or Bayesian optimization isn't sufficient (answer: hyperparameter space is mixed discrete/continuous and non-convex, making GA exploration more thorough than grid search).

---

## Problem Formulation

### Input Features (what you feed the model)

These come from weather station data and snowpack observations:

| Feature | Description | Why It Matters |
|---|---|---|
| New snow (24h) | cm of snowfall in last 24 hours | Loading is the #1 trigger of storm-slab avalanches |
| New snow (72h) | cm in last 3 days | Cumulative loading effect |
| Snow water equivalent | Density-adjusted snowpack depth | Heavy, wet snow is more dangerous than light snow |
| Temperature (current) | Air temp at station elevation | Warming weakens snowpack bonding |
| Temperature trend | Change over 24–48h | Rapid warming is a key danger indicator |
| Wind speed | Average and gust speed | Wind creates slabs, transports snow to leeward slopes |
| Wind direction | Prevailing direction | Determines which aspects are loaded |
| Snowpack depth | Total depth at weather station | Deep snowpacks bury weak layers; shallow = unstable |
| Days since last storm | Time since significant loading | Snowpack settles and strengthens over time |
| Aspect (terrain) | Slope orientation (N/S/E/W) | North aspects hold cold, weak layers longer |
| Elevation band | Alpine / treeline / below treeline | Danger varies significantly by elevation |

### Target Variable

Daily danger rating for the Rogers Pass / Columbia Mountains forecast zone:
- 1 = Low
- 2 = Moderate
- 3 = Considerable
- 4 = High
- 5 = Extreme

### Fitness Function

```
fitness(chromosome) = classification_accuracy(predictions, historical_labels)
                    - λ * complexity_penalty(chromosome)
```

Where `λ` controls the trade-off between accuracy and model simplicity. The complexity penalty is optional but encouraged for Option B.

### Search Space Size

For Option A with 10 features and 4 threshold boundaries: each chromosome is a vector of 14 continuous values. The search space is continuous and 14-dimensional — a textbook GA application where exact methods cannot help.

---

## Where Data Mining Fits In

Data mining is not just compatible with this project — it arguably makes the GA *work properly*. Here is where it integrates:

### 1. Feature Engineering via Clustering

Run k-means or hierarchical clustering on historical weather observations to identify distinct "snowpack regimes" — e.g., cold/dry inland conditions vs. warm/wet maritime-influence conditions. These clusters can become categorical input features, or help you decide which features to include in the GA chromosome.

### 2. Association Rule Mining for Danger Pattern Discovery

Mine association rules from the historical dataset to find patterns like:
- `{new_snow_24h > 30cm, wind_speed > 60km/h} → danger = High (confidence: 78%)`
- `{temp_trend > +5°C, days_since_storm < 3} → danger ≥ Considerable (confidence: 81%)`

These rules serve two purposes: they validate that your model is finding real physical patterns, and they can provide the initial population for the GA (seeding with domain-knowledge solutions speeds up convergence).

### 3. Feature Selection / Importance

Use mutual information or correlation analysis to rank features by their predictive power before the GA runs. This reduces the chromosome size and makes the GA more efficient. This is a data mining step that directly improves the GA's performance.

### 4. Outlier Detection

Clean the historical dataset using outlier detection (e.g., isolation forest or z-score filtering) before training. Weather station data contains sensor errors and missing values. Dirty training data directly degrades fitness evaluation accuracy.

The proposal story becomes: "We use data mining techniques to clean, explore, and engineer features from historical avalanche and weather data, then apply a GA to optimize a danger prediction model trained on those features."

---

## Data Sources

### 1. Avalanche Canada — Public Forecast Archive + API

**What it is:** Avalanche Canada is Canada's national public avalanche safety organization, based in Revelstoke. It publishes daily public danger forecasts for forecast zones across western Canada, including the **Columbia Mountains zone** which covers Rogers Pass and Revelstoke.

**What you get:**
- Historical daily danger ratings (Low/Moderate/Considerable/High/Extreme) by elevation band (alpine, treeline, below treeline)
- Avalanche problem types (wind slab, storm slab, persistent slab, wet avalanche, etc.)
- Confidence levels and trend information

**How to access:**
- Avalanche Canada has a **public API** at `https://docs.avalanche.ca/` that returns current and historical forecast products as JSON. The API is used by their own website and is openly documented.
- Historical forecasts going back multiple seasons are accessible via the API and web archive.

URL: https://avalanche.ca / API docs: https://docs.avalanche.ca/

---

### 2. Parks Canada — Rogers Pass Avalanche Records

**What it is:** Parks Canada's Mountain Safety team at Glacier National Park records avalanche activity along the Trans-Canada Highway corridor year-round. This is one of the longest continuous operational avalanche records in the world.

**What you get:**
- Approximately 2,000 recorded avalanche activity events per year along the corridor
- Daily public avalanche forecasts specific to Rogers Pass (distinct from the broader Avalanche Canada zone forecast)
- Field observations from professional forecasters including snowpack profiles, stability tests, and observed avalanche activity

**How to access:**
- Parks Canada forecasts are published via the Avalanche Canada platform
- Contact Parks Canada directly for raw historical observation data — they have shared data with academic researchers before
- The Parks Canada facts page for Glacier NP confirms snowfall records at Rogers Pass Summit back to 1965 and Mt. Fidelity back to 1965

URL: https://parks.canada.ca/pn-np/bc/glacier/nature/controle-avalanche-control

---

### 3. Avalanche Canada Mountain Information Network (MIN)

**What it is:** A public observation network where backcountry users and professional forecasters submit field reports including snowpack observations, weather, avalanche sightings, and incident reports.

**What you get:**
- Geotagged field observations filterable by date, region, and report type
- Snowpack reports: depth, layering, bonding, stability test results
- Weather reports: temperature, precipitation, wind, cloud cover
- Avalanche activity reports: size, type, aspect, elevation

**How to access:**
- Reports are publicly viewable at https://avalanche.ca/mountain-information-network
- Filterable by forecast region (select "Columbia Mountains") and date range
- Available as a list view for bulk extraction

URL: https://avalanche.ca/mountain-information-network

---

### 4. BC Ministry of Transportation — Avalanche and Weather Programs (SAW-PAWS)

**What it is:** The BC Ministry of Transportation operates a network of automated weather stations specifically designed for avalanche and road safety programs along BC highways.

**What you get:**
- Hourly weather data: snow depth, snow water equivalent, air temperature, precipitation, wind speed, wind direction, relative humidity
- Station list downloadable as CSV/XLS/PDF
- Historical data download available at the SAW-PAWS portal

**Key stations near Rogers Pass / Glacier:** Several stations cover Highway 1 through the Selkirks and Rogers Pass area.

**How to access:**
- Station list: https://prdoas6.pub-apps.th.gov.bc.ca/saw-paws/weatherstation?page=stationList&format=csv
- Historical data download: https://prdoas6.pub-apps.th.gov.bc.ca/saw-paws/weatherstation
- Also listed on the federal Open Canada portal

URL: https://prdoas6.pub-apps.th.gov.bc.ca/saw-paws/weatherstation

---

### 5. Environment and Climate Change Canada — Historical Climate Data

**What it is:** Canada's federal historical weather archive, covering all ECCC weather stations with hourly, daily, and monthly records going back decades.

**What you get:**
- Temperature (max, min, mean), precipitation, snow depth, snow on ground, wind speed and direction, relative humidity
- Rogers Pass has a long-running ECCC station with multi-decade records
- Bulk download available as CSV or GeoJSON via ClimateData.ca

**How to access:**
- Search by station name or province: https://climate.weather.gc.ca/historical_data/search_historic_data_e.html
- Bulk download via Canadian Centre for Climate Services: https://climatedata.ca

URL: https://climate.weather.gc.ca/historical_data/search_historic_data_e.html

---

### 6. BC Government — Snow Survey Data (Automated Snow Weather Stations)

**What it is:** BC's Ministry of Environment operates automated snow weather stations (ASWS) in mountainous areas across the province, transmitting data hourly via GOES satellites. Maintained in partnership with BC Hydro, Rio Tinto Alcan, and Metro Vancouver.

**What you get:**
- Hourly snow water equivalent, snow depth, air temperature, precipitation
- Historical data from 2011 to present (automated); manual survey data going back further
- Near-real-time daily graphs for current water year

**How to access:**
- Snow survey portal: https://www2.gov.bc.ca/gov/content/environment/air-land-water/water/water-science-data/water-data-tools/snow-survey-data
- Archive of automated snow weather stations (ASWS) data: 2011–2016 archived; more recent via the live portal

URL: https://www2.gov.bc.ca/gov/content/environment/air-land-water/water/water-science-data/water-data-tools/snow-survey-data

---

### 7. Natural Resources Canada — Digital Elevation Model (DEM)

**What it is:** Terrain data covering all of Canada, providing elevation, slope angle, and slope aspect at various resolutions.

**What you get:**
- Elevation in metres at 23–25m grid resolution (base CDEM) or up to 1m resolution (HRDEM LiDAR-derived)
- Derived products: slope angle, slope aspect, shaded relief — all directly computed from the DEM
- The CDEM is available free as an Earth Engine image collection and via Open Canada

**Why you need it:** Slope angle and aspect are fundamental avalanche terrain inputs. Slopes of 30–45° are the prime avalanche zone; north-facing aspects hold weak layers longer. Without terrain data you cannot characterize avalanche start zones or weight terrain-specific features.

**How to access:**
- CDEM on Google Earth Engine: `ee.ImageCollection("NRCan/CDEM")`
- High Resolution DEM (HRDEM): https://open.canada.ca/data/en/dataset/0fe65119-e96e-4a57-8bfe-9d9245fba06b
- BC-specific 25m DEM (TRIM): https://www2.gov.bc.ca/gov/content/data/geographic-data-services/topographic-data/elevation

URL: https://natural-resources.canada.ca/maps-tools-publications/satellite-elevation-air-photos/digital-elevation-models

---

### 8. BC Data Catalogue — Archived Automated Snow Weather Stations

**What it is:** Province of BC open data archive of historical snowpack observations, specifically the Archived Automated Snow Weather Stations (ASWS) dataset.

**What you get:**
- Historical hourly snow water equivalent, snow depth, air temperature, precipitation for all BC ASWS stations from 2011–2016
- Historical daily max/min temperature, precipitation, snow depth, snow water equivalent from station installation date to 2011
- Tabular format, downloadable

URL: https://catalogue.data.gov.bc.ca/dataset/automated-snow-weather-station-locations

---

## Implementation Stack (Proposed)

- **Python** — primary language
- **pandas / NumPy** — data loading, feature engineering, dataset construction
- **scikit-learn** — classification baseline models, cross-validation framework
- **DEAP** — Python library for genetic algorithms (provides GA framework; or implement from scratch)
- **mlxtend** — association rule mining (Apriori/FP-growth for data mining component)
- **requests / json** — Avalanche Canada API data retrieval
- **rasterio / richdem** — DEM processing to extract slope and aspect features
- **matplotlib / seaborn** — visualization of results, danger rating distributions, feature importance

---

## Suggested Division of Work

| Component | Skills Required |
|---|---|
| Data acquisition: weather + snowpack | Python, API calls, CSV processing |
| Data acquisition: DEM + terrain features | rasterio, GIS |
| Data mining: feature engineering, clustering, association rules | Data mining background → key contribution |
| GA implementation: chromosome design, crossover, mutation | Python, DEAP or from scratch |
| Fitness function + model evaluation | ML/classification knowledge |
| Visualization and final report | All members |

---

## Why This Justifies AI (ECE 470 Requirement)

1. **High-dimensional, non-convex search space**: The weight vector or hyperparameter space has no known optimal solution and no gradient to follow. GA explores it efficiently.
2. **No closed-form solution**: There is no mathematical formula that maps snowpack inputs to danger ratings — the relationship is complex, non-linear, and varies by season and location.
3. **Multi-objective trade-offs**: Balancing prediction accuracy vs. false-alarm rate vs. model simplicity is naturally handled by GA fitness weighting.
4. **Seeded initialization from domain knowledge**: Association rules mined from historical data can seed the GA's initial population, demonstrating integration of data mining and GA.

---

## Key References to Cite in Proposal

- Avalanche Canada: https://avalanche.ca
- Avalanche Canada API: https://docs.avalanche.ca/
- Parks Canada — Glacier NP Avalanche Control: https://parks.canada.ca/pn-np/bc/glacier/nature/controle-avalanche-control
- BC Ministry of Transportation SAW-PAWS: https://prdoas6.pub-apps.th.gov.bc.ca/saw-paws/weatherstation
- Environment Canada Historical Climate Data: https://climate.weather.gc.ca/historical_data/search_historic_data_e.html
- BC Snow Survey Data: https://www2.gov.bc.ca/gov/content/environment/air-land-water/water/water-science-data/water-data-tools/snow-survey-data
- NRCan HRDEM: https://open.canada.ca/data/en/dataset/0fe65119-e96e-4a57-8bfe-9d9245fba06b
- DEAP framework: Fortin et al. (2012). DEAP: Evolutionary Algorithms Made Easy. Journal of Machine Learning Research, 13, 2171-2175.
- Haegeli, P. & McClung, D. (2007). Expanding the snow climate classification with avalanche relevant information. Cold Regions Science and Technology. (Uses Rogers Pass data — cite as precedent)
