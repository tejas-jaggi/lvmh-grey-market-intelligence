# LVMH Grey Market Diversion Intelligence — Prototype Blueprint
### IS 534 Information Consulting | Group 1 | April 2026

---

## 🎯 Project Overview

**What we're building:** A working web-based prototype of an AI-driven grey market diversion intelligence dashboard for LVMH. This simulates a real-world system that monitors marketplace listings, scores distributor risk, detects price anomalies, and surfaces actionable diversion signals — all within a luxury-grade UI fit for executive presentation.

**What it is NOT:** A production system, live API integration, or enterprise deployment. This is a strategic concept prototype using synthetic data to demonstrate the capabilities we recommended in our consulting engagement.

**Hardware Profile (Your Laptop):**
- Intel i7-11800H @ 2.30GHz — excellent for local Flask server + ML inference
- 16GB RAM — sufficient for pandas, scikit-learn, and SQLite with thousands of mock records
- 4GB GPU — not needed for Phase 1 or 2; optional for Phase 3 NLP
- 757GB used / 954GB total — plenty of space

---

## 🗂️ Full Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Backend | Python 3.11 + Flask | Lightweight, fast, easy to demo |
| Database | SQLite + SQLAlchemy | Zero config, portable, runs anywhere |
| Data Gen | Faker + Pandas + NumPy | Realistic synthetic LVMH-style data |
| ML | Scikit-learn | Isolation Forest, risk scoring |
| Frontend | HTML/CSS/JS + Chart.js | No build step needed, fast iteration |
| Fonts | Google Fonts (Playfair + DM Mono) | Premium luxury aesthetic |
| Charts | Chart.js v4 | Clean, interactive, no backend needed |

---

## 📁 Project Structure

```
lvmh_prototype/
│
├── app.py                    # Flask application (main entry point)
├── database.py               # SQLAlchemy models + DB setup
├── data_generator.py         # Synthetic data generation
├── ml_engine.py              # Risk scoring + anomaly detection (Phase 2)
├── requirements.txt          # Python dependencies
├── setup.py                  # One-click setup script
│
├── templates/
│   ├── dashboard.html        # Main KPI dashboard
│   ├── listings.html         # Marketplace monitoring table
│   ├── distributors.html     # Distributor risk scores (Phase 2)
│   └── analytics.html        # Deep analytics charts (Phase 3)
│
└── static/
    ├── css/
    │   └── style.css         # Global luxury styles
    └── js/
        └── dashboard.js      # Chart init + live polling
```

---

## 🗓️ 3-Week Roadmap

---

### ✅ PHASE 1 — Data Foundation & Monitoring Dashboard (Week 1)
**Goal:** A running, beautiful, demo-ready dashboard with synthetic data and marketplace monitoring.

| Day | Task | Output |
|-----|------|--------|
| Day 1 | Environment setup, project scaffold, install dependencies | Running Flask server on localhost |
| Day 2 | Build synthetic data generator (products, distributors, listings) | 500+ realistic mock records in SQLite |
| Day 3 | Flask API routes — KPIs, listings, alerts | REST endpoints returning JSON |
| Day 4 | Dashboard HTML/CSS — luxury design system | Pixel-perfect dark luxury UI |
| Day 5 | KPI cards, price anomaly table, Chart.js graphs | Interactive dashboard visible on browser |
| Day 6 | Listings monitor page with filter + search | Sortable, filterable data table |
| Day 7 | Polish, demo walkthrough, README | Phase 1 deliverable complete ✅ |

**Phase 1 Deliverables:**
- Live dashboard at `http://localhost:5000`
- KPI cards: Listings scanned, unauthorized flagged, high-risk distributors, revenue at risk
- Marketplace monitoring table with risk badges
- Price anomaly bar chart (by region)
- Platform distribution pie chart
- Geographic risk heat data
- Diversion alert feed

---

### 🔵 PHASE 2 — AI Risk Scoring & Distributor Intelligence (Week 2)
**Goal:** Add actual ML-driven scoring — Isolation Forest for anomaly detection + rule-based distributor risk model.

| Day | Task | Output |
|-----|------|--------|
| Day 8 | Build `ml_engine.py` — Isolation Forest for listing anomalies | Anomaly scores on all mock listings |
| Day 9 | Distributor risk scoring model (order velocity, price gap, SKU mix) | 0–100 risk score per distributor |
| Day 10 | Risk Score Ladder logic (Monitor / Flag / Audit / Hold) | Color-coded distributor tiers |
| Day 11 | Distributor deep-dive page with risk breakdown | Clickable distributor profiles |
| Day 12 | Seller network clustering (simple graph logic) | Connected seller groups visualization |
| Day 13 | Add "Run Scan" button — triggers ML re-scoring | Interactive demo flow |
| Day 14 | Phase 2 integration test + demo script | Phase 2 deliverable complete ✅ |

**Phase 2 Deliverables:**
- ML-driven anomaly scores on listings
- Distributor Risk Ladder dashboard (0-40 Monitor → 86-100 Hold Shipment)
- Seller network graph view
- Interactive "Scan Now" button for live demo

---

### 🟡 PHASE 3 — Predictive Intelligence & Presentation Polish (Week 3)
**Goal:** Add allocation intelligence layer, finalize all UI, prepare demo script.

| Day | Task | Output |
|-----|------|--------|
| Day 15 | Pricing anomaly detection — threshold model comparing MSRP vs. resale | Region-level price gap heatmap |
| Day 16 | Allocation optimization simulation — over-allocated region flags | Allocation intelligence panel |
| Day 17 | Analytics deep-dive page with full charts | Executive analytics view |
| Day 18 | "What-If" scenario simulator — adjust price gap, see diversion impact | Interactive scenario tool |
| Day 19 | Full UI polish, loading states, transitions | Demo-ready application |
| Day 20 | Demo script, walkthrough recording, talking points | Presentation ready ✅ |
| Day 21 | Buffer / final rehearsal | Backup day |

**Phase 3 Deliverables:**
- Allocation intelligence simulation
- Price gap scenario tool
- Full 3-page dashboard (Overview → Distributors → Analytics)
- Demo script with narrative walkthrough
- Final prototype zip for submission

---

## 🎨 Design Language

**Aesthetic:** Dark luxury intelligence terminal — like Bloomberg meets LVMH's Maisons HQ.

| Element | Value |
|---------|-------|
| Background | `#080c14` (deep navy-black) |
| Cards | `#0f1623` with `1px solid rgba(255,255,255,0.06)` |
| Primary Accent | `#c9a84c` (warm LVMH gold) |
| Danger | `#e85454` |
| Success | `#2ecc87` |
| Display Font | Playfair Display (headers, brand) |
| Data Font | DM Mono (numbers, SKUs, codes) |
| Body Font | Plus Jakarta Sans (readable, modern) |

---

## 📊 Synthetic Data Schema

### Products (75 records across 8 Maisons)
```
sku, maison, product_name, category, 
msrp_usd, msrp_eur, msrp_cny, 
is_limited_edition, launch_year
```

### Distributors (180 records across 12 regions)
```
distributor_id, name, region, country, tier,
allocation_volume, sales_velocity, 
order_to_sales_ratio, price_gap_exposure,
compliance_flags, risk_score
```

### Marketplace Listings (500+ records)
```
listing_id, platform, seller_id, product_sku,
listed_price, currency, msrp_equivalent,
price_deviation_pct, is_flagged,
flag_reason, detection_timestamp, confidence
```

### Price Anomaly Events (200 records)
```
event_id, product_sku, region, 
expected_msrp, detected_resale_price,
gap_pct, arbitrage_potential_usd,
detected_at
```

---

## 🚀 Demo Flow (For Presentation)

**Narrative arc (5 minutes):**

1. **"The Problem"** → Open dashboard, show KPI cards — "$4.2M revenue at risk, 47 unauthorized listings detected today"
2. **"Real-Time Monitoring"** → Navigate to Listings page, filter by "High Risk", show a flagged Louis Vuitton listing on a grey market platform
3. **"AI Scoring"** → Click into Distributor Risk, show a "Hold Shipment" distributor in Southeast Asia with a 91/100 risk score
4. **"Prediction"** → Show the Analytics page — price gap in China driving 34% of detected diversion
5. **"What LVMH Should Do"** → Tie back to the 18-month roadmap from the tech assessment

---

## 🔧 Setup (Complete Guide — Phase 1)

See Phase 1 section below for full step-by-step terminal commands.

---

## 📌 Key Constraints & Decisions

- **No live scraping:** We use synthetic data. Real scraping would require API keys and raises legal questions outside scope.
- **No GPU training:** All ML uses CPU-friendly scikit-learn models. 16GB RAM is more than enough.
- **SQLite only:** No PostgreSQL setup needed. SQLite file travels with the project.
- **Self-contained:** Everything runs on localhost. No cloud, no API keys needed for core demo.

---

*Built by Group 1 — Joanita D'Souza, Aman Joshi, Prasidha Murali, Aditya Dilip, Tejas Jaggi*
*IS 534 Information Consulting — University of Illinois Urbana-Champaign*
