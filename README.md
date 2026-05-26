# LVMH Grey Market Intelligence

An AI-assisted grey market diversion intelligence prototype for luxury brand protection, channel governance, and allocation risk monitoring.

This project was built for an information consulting engagement focused on LVMH's grey market challenges. The data is synthetic, but the workflow is real: the app scans marketplace listings, scores distributor risk, explains why records were flagged, and gives leadership an operating view of diversion exposure.

## Live Demo

[Open the live prototype](https://lvmh-grey-market-intelligence.onrender.com)

Render free-tier apps may take a short moment to wake up after inactivity.

![Dashboard scan view](docs/assets/screenshots/dashboard-scan.png)

## Why This Exists

Luxury maisons face a recurring grey market problem: unauthorized listings, regional price arbitrage, suspicious reseller clusters, and distributor behavior are often monitored in separate systems. This prototype explores what a connected intelligence layer could look like if marketplace monitoring, allocation intelligence, and distributor governance were combined into one explainable AI workflow.

## What It Does

- Scans 520 synthetic marketplace listings across resale platforms and regions.
- Scores listing anomalies using an Isolation Forest model when `scikit-learn` is available, with a deterministic fallback for lightweight demos.
- Calculates a composite distributor risk score from order pressure, price-gap exposure, compliance history, and allocation intensity.
- Persists each scan in `scan_runs` and stores DIS snapshots in `dis_history` for portfolio-level risk trending.
- Imports a small eBay Browse API listing batch when credentials are configured, with a fixture fallback for reliable demos.
- Shows evidence trails for escalated listings so a reviewer can see why a flag exists.
- Maps seller clusters with a network graph based on shared SKU, platform, and region signals.
- Provides a price and allocation analytics page with regional gap charts, severity distribution, heatmap, and a What-If simulator.
- Seeds a full demo database automatically on first run.

## Recent Build Milestones

- Added DIS score history tracking with `scan_runs` and `dis_history`, so every scan persists an auditable portfolio risk snapshot.
- Replaced the dashboard trend mockup with saved DIS history from actual scan events.
- Added a small eBay Browse API connector with OAuth live mode, fixture fallback, and `ingest_runs` audit records.
- Added a Marketplace Monitor `eBay Import` workflow that imports or updates eBay-sourced listing rows without duplicating them.

## Prototype Screens

| Marketplace Monitor | Distributor Risk |
| --- | --- |
| ![Marketplace monitor](docs/assets/screenshots/marketplace-monitor.png) | ![Distributor risk workspace](docs/assets/screenshots/distributor-risk.png) |

| Price and Allocation Analytics |
| --- |
| ![Price and allocation analytics](docs/assets/screenshots/price-allocation.png) |

## Architecture

```mermaid
flowchart LR
    A[Synthetic LVMH Products] --> D[(SQLite Demo Database)]
    B[Marketplace Listings] --> D
    C[Distributor Profiles] --> D
    N[eBay Browse API or Fixture] --> E
    D --> E[Flask API]
    E --> F[ML Scan Engine]
    E --> O[Listing Ingest Runs]
    F --> G[Listing Risk Escalations]
    F --> H[Distributor Risk Scores]
    F --> M[DIS Score History]
    E --> I[Dashboard UI]
    E --> J[Marketplace Monitor]
    E --> K[Distributor Risk Workspace]
    E --> L[Price and Allocation Analytics]
```

## Tech Stack

- Python
- Flask
- SQLAlchemy
- SQLite
- scikit-learn, optional deploy/runtime model path
- Chart.js
- D3.js
- eBay Browse API connector with fixture fallback
- HTML/CSS/JavaScript
- Render-ready Gunicorn deployment

## Run Locally

Use Python 3.11+ for local development. Python 3.12 is recommended if you want the optional `scikit-learn` path.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open:

- `http://127.0.0.1:5000`
- `http://127.0.0.1:5000/listings`
- `http://127.0.0.1:5000/distributors`
- `http://127.0.0.1:5000/analytics`

Optional advanced ML install:

```powershell
python -m pip install -r requirements-phase2.txt
```

Optional eBay live connector:

```powershell
$env:EBAY_CLIENT_ID="your-ebay-client-id"
$env:EBAY_CLIENT_SECRET="your-ebay-client-secret"
$env:EBAY_MARKETPLACE_ID="EBAY_US"
```

Without those variables, the Marketplace Monitor uses the bundled eBay-style fixture so the import workflow still works locally and on Render.

Free Render services spin down when idle and have an ephemeral filesystem. That is acceptable for this prototype because the app automatically reseeds synthetic demo data when the SQLite database is missing.

## Demo Script

1. Open the dashboard and click `Run Scan`.
2. Show the Diversion Intelligence Score, scan deltas, and listing evidence trails.
3. Open Marketplace Monitor and click `eBay Import` to show the external listing connector workflow.
4. Show listing-level risk, confidence, seller, platform, status, and source badges.
5. Open Distributor Risk to explain how partner risk is scored and translated into action.
6. Open Price and Allocation to show regional price gaps and the What-If simulator.

## Project Structure

```text
app.py                         Flask routes and REST API
database.py                    SQLAlchemy models
data_generator.py              Synthetic LVMH-style dataset generation
ml_engine.py                   Listing anomaly and distributor risk scoring
connectors/ebay_connector.py   eBay Browse API client and fixture fallback
fixtures/ebay_luxury_listings.json
                               Local eBay-style listings for credential-free demos
templates/dashboard.html       Executive dashboard and scan workflow
templates/listings.html        Marketplace monitoring table
templates/distributors.html    Distributor risk workspace
templates/analytics.html       Price and allocation analytics
docs/assets/screenshots/       README screenshots
render.yaml                    Render deployment blueprint
requirements.txt               Local app dependencies
requirements-deploy.txt        Deploy-only runtime dependencies
requirements-phase2.txt        Optional advanced ML dependency
```

## Next Build Priorities

- Expand the eBay connector into scheduled marketplace ingestion with more brands and search terms.
- Add a constrained natural-language query interface over approved database filters.
- Add role-based views for Brand Protection, Supply Chain, and Leadership.

## Important Note

This is a student prototype with synthetic data. It is not affiliated with LVMH, the University of Illinois, or any marketplace platform.
