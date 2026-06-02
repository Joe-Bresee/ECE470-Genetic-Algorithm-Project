# ECE 470 Project Context: Victoria Bike Lane Optimizer using Genetic Algorithm

## What This Project Is

We are building a **Bike Lane Optimizer** for the City of Victoria, BC. The goal is to determine which road segments in Victoria should have bike lanes added or upgraded, given a fixed budget, in order to maximize some combination of network connectivity, cyclist safety, and access to key destinations.

This is fundamentally a **combinatorial optimization problem**: with hundreds of candidate road segments, there are astronomically many possible combinations to evaluate. We use a **Genetic Algorithm (GA)** to search this space efficiently.

---

## What is a Genetic Algorithm?

A Genetic Algorithm is a search and optimization technique inspired by biological evolution. It belongs to the field of **Evolutionary Computation**, which sits within Artificial Intelligence. It is *not* Machine Learning — it does not learn from data using gradient descent or statistical inference. Instead, it evolves a population of candidate solutions toward better ones over many generations.

### Key Concepts

- **Chromosome**: One candidate solution, encoded as a data structure. In our case, a binary string where each bit represents one road segment (1 = add bike lane, 0 = don't).
- **Population**: A set of many chromosomes (e.g., 200 candidate layouts).
- **Fitness function**: A score assigned to each chromosome. Higher = better solution. This is what we define based on our objectives.
- **Selection**: Better-scoring chromosomes are more likely to be chosen as "parents" for the next generation.
- **Crossover**: Two parent chromosomes are combined to produce child chromosomes, mixing their characteristics.
- **Mutation**: Random small changes to a chromosome, preventing the algorithm from getting stuck in a local optimum.
- **Generation**: One full cycle of evaluation → selection → crossover → mutation. Repeated for hundreds or thousands of iterations.

### The GA Loop

1. Initialize a random population of candidate bike lane layouts
2. Score each layout using the fitness function
3. Select the fittest layouts as parents
4. Produce next generation via crossover + mutation
5. Repeat until convergence or max generations reached
6. Output the best layout found

### Why GA and Not Exact Methods?

The "which road segments to include" decision is a **0/1 integer programming problem**. With 500+ candidate segments, the number of possible combinations is 2^500 — larger than the number of atoms in the observable universe. Exact Integer Linear Programming (ILP) solvers can find the provably optimal solution but may take hours or never terminate for problems this size. The GA trades the guarantee of finding the *best* solution for the ability to find a *very good* solution in practical time.

---

## How LP/OR Background Integrates

One team member has a background in **Linear Programming and Operations Research**. This is directly useful and makes the project more sophisticated than most ECE 470 submissions.

### The Bilevel Optimization Structure

The project uses a two-level optimization structure:

- **Outer level (GA)**: Searches over binary decisions — which road segments to include in the bike network. This is the combinatorial part that LP cannot handle directly.
- **Inner level (LP)**: Once the GA picks a set of segments, a Linear Program evaluates the quality of that layout by solving a **network flow problem** — computing things like maximum cyclist throughput, minimum travel distances between origin-destination pairs, or coverage scores. The LP output becomes the fitness score returned to the GA.

This is called a **bilevel optimization** or a **metaheuristic with LP subproblem** approach. It is academically legitimate and worth highlighting in the proposal as a design contribution.

### Why LP Alone Doesn't Solve It

LP handles continuous variables well but cannot directly solve binary (0/1) decisions without becoming Integer Linear Programming (ILP), which is NP-hard. For large networks, ILP is computationally intractable. GA handles the discrete search space; LP handles the evaluation of each candidate solution.

---

## Problem Formulation

### Decision Variable (Chromosome Encoding)

A binary vector **x** of length *n*, where *n* is the number of candidate road segments:
- x_i = 1 → add/upgrade a bike lane on segment i
- x_i = 0 → do not

Victoria's road network has several hundred candidate segments, giving a search space of roughly 2^400 to 2^600.

### Objective Function (Fitness)

Maximize a weighted combination of:

1. **Network connectivity** — how many residential areas, schools, hospitals, and transit stops are reachable via a continuous protected route
2. **Safety score** — avoid high-traffic roads and known crash locations (weighted using ICBC data)
3. **Coverage** — proportion of the city's population within a defined buffer distance of a bike lane
4. **Connectivity to existing AAA network** — additions that connect to Victoria's existing 40+ km of AAA routes score higher

Subject to:
- **Budget constraint**: total construction cost ≤ B (penalized in fitness or enforced as hard constraint)
- **Feasibility constraints**: physical width requirements, no duplicate segments

### Fitness Function Formula (Sketch)

```
fitness(x) = w1 * connectivity(x) + w2 * safety(x) + w3 * coverage(x) - penalty(x)

penalty(x) = large constant if cost(x) > budget
```

The weights (w1, w2, w3) are tunable parameters — this is also something GA can optimize in an extended version.

---

## Data Sources

### 1. City of Victoria Open Data Portal — opendata.victoria.ca

All free, publicly downloadable as Shapefile / GeoJSON / CSV.

| Dataset | What It Gives You | Use In Project |
|---|---|---|
| **Bike Lanes** | Existing AAA protected, off-street, painted, shared bus/bike lanes; route type and number of lanes | Defines current network; candidate upgrades start here |
| **Streets** | Road geometry, street classification, direction of travel, speed limit, truck routes, road width, number of lanes | Candidate segment list; road type weighting in fitness |
| **Intersections** | All road intersections with street name pairs | Graph node construction for network analysis |
| **Traffic Volume** | 24-hour vehicle counts by road segment | Safety penalty input — higher traffic = higher danger weight |
| **Zoning Boundary** | Land use categories (residential, commercial, mixed, institutional) | Origin/destination demand estimation |
| **Zoning Map Labels** | Same as above with precise label placement | Supplementary to Zoning Boundary |

URL: https://opendata.victoria.ca

---

### 2. ICBC Open Data — icbc.com/open-data

Free, publicly available crash data for all of BC, filterable by municipality.

| Dataset | What It Gives You | Use In Project |
|---|---|---|
| **Crashes involving cyclists** | Location, severity, year, street name for all cyclist-involved crashes | Safety scoring: weight against adding lanes near high-crash segments |
| **Crashes involving pedestrians** | Same but pedestrian | Supporting context for dangerous intersections |
| **Crash maps (Tableau)** | Interactive 5-year crash visualization by municipality | Exploratory analysis; verify hotspot locations |

URL: https://www.icbc.com/about-icbc/research-library/crash-data  
Tableau dashboards: https://public.tableau.com/app/profile/icbc

---

### 3. Capital Regional District (CRD) — crd.ca

| Dataset | What It Gives You | Use In Project |
|---|---|---|
| **CRD Bike Map (Oct 2025)** | Regional cycling network across 13 municipalities including Saanich, Oak Bay, Esquimalt | Ensures proposed additions connect to the broader regional network, not just within city limits |
| **Pedestrian & Cycling Master Plan data** | Strategic priority corridors | Validates that GA results align with planned improvements |

URL: https://www.crd.ca/programs-services/getting-around/find-bike-map

---

### 4. OpenStreetMap — openstreetmap.org

Free, global, detailed road network data. Accessible via the **Overpass API** (no account needed) or downloadable as a PBF/OSM file for the Victoria region.

| What It Gives You | Use In Project |
|---|---|
| Full road network with geometry, road class, bike infrastructure tags | Primary graph structure if Victoria open data is insufficient |
| Points of interest: schools, hospitals, transit stops, parks | Origin/destination nodes for connectivity scoring |
| Existing cycling infrastructure tags (cycleway, bicycle=yes, etc.) | Supplement to city data |

Tool: Use **OSMnx** Python library to download and build the road graph directly. One function call gives you a NetworkX graph of Victoria's entire street network.

---

### 5. Statistics Canada — Census 2021

Free via Statistics Canada open data portal.

| Dataset | What It Gives You | Use In Project |
|---|---|---|
| **Dissemination Area population counts** | Population density at small geographic unit (~400-700 people each) | Weight coverage score by number of people served |
| **Commute mode data** | What percentage of people in each area cycle to work | Identifies high-demand corridors; validates model outputs |
| **Origin-destination (Journey to Work)** | Where people travel from and to | Demand weights for connectivity scoring |

URL: https://www12.statcan.gc.ca/census-recensement/2021/

---

### 6. BC Government Open Data Catalogue — data.gov.bc.ca

| Dataset | What It Gives You | Use In Project |
|---|---|---|
| **BC Schools** (point locations) | All K-12 schools in BC with coordinates | High-priority destinations for connectivity; families with children are key cycling demographic |
| **BC Health Authority Facilities** | Hospital and clinic locations | High-priority destinations |
| **Digital Road Atlas (DRA)** | Provincial road network with attributes | Backup/supplement for road geometry |

URL: https://catalogue.data.gov.bc.ca

---

### 7. Can-BICS (Canadian Bikeway Comfort and Safety Classification)

A standardized national cycling infrastructure dataset derived from OpenStreetMap, maintained by researchers and available via ArcGIS Online.

| What It Gives You | Use In Project |
|---|---|
| Categorized cycling infrastructure comfort and safety levels across Canada | Pre-processed cycling infrastructure data; cross-validate against city data |

URL: https://www.arcgis.com/home/item.html?id=efaf04c6e3914c059bfb7298e784a8 (as cited in recent Victoria cycling research, 2025)

---

## Implementation Stack (Proposed)

- **Python** — primary language
- **OSMnx + NetworkX** — road graph construction and network analysis
- **GeoPandas / Shapely** — spatial operations on Victoria open data shapefiles
- **SciPy or PuLP** — LP subproblem solver for inner-level fitness evaluation
- **NumPy** — GA chromosome operations (crossover, mutation)
- **Matplotlib / Folium** — visualization; output best layout on an interactive map
- **DEAP** — Python library for genetic algorithms (optional; provides GA framework)

---

## Division of Work (Suggested)

| Component | Skills Required |
|---|---|
| Data acquisition and preprocessing | Python, GIS, GeoPandas |
| Road graph construction (nodes/edges) | OSMnx, NetworkX |
| GA implementation (chromosome, crossover, mutation, selection) | Python, DEAP or from scratch |
| Fitness function design and LP subproblem | LP/OR background → key contribution |
| Visualization and map output | Folium, Matplotlib |
| Evaluation and writeup | All members |

---

## Why This Justifies AI (ECE 470 Requirement)

The problem has the following properties that justify using a GA over other methods:

1. **Combinatorial search space**: 2^n possible solutions (n ≈ 400–600 segments). Exact enumeration is impossible.
2. **Non-linear, multi-objective fitness**: The objective function is not a simple formula — it involves graph algorithms, spatial queries, and safety scoring, making classical optimization intractable.
3. **No gradient information available**: The fitness landscape is discrete; gradient-based methods do not apply.
4. **Good approximate solutions are sufficient**: We do not need the provably optimal bike lane layout — we need a good, practically implementable one within budget.

GA is the natural fit. The LP integration elevates the fitness evaluation beyond typical GA projects and demonstrates applied OR knowledge.

---

## Key References to Cite in Proposal

- City of Victoria Cycling Network: https://www.victoria.ca/getting-around/walking-riding-rolling/cycling-network
- City of Victoria Open Data Portal: https://opendata.victoria.ca
- ICBC Crash Data: https://www.icbc.com/about-icbc/research-library/crash-data
- CRD Bike Map: https://www.crd.ca/programs-services/getting-around/find-bike-map
- OSMnx Python library: Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. Computers, Environment and Urban Systems, 65, 126-139.
- DEAP framework: Fortin et al. (2012). DEAP: Evolutionary Algorithms Made Easy. Journal of Machine Learning Research, 13, 2171-2175.
