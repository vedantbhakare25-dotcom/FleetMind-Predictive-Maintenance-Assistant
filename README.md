# FleetMind
# FleetMind — AI-Powered Predictive Maintenance Platform

> **Predict machine failures before they happen. Understand why. Act immediately.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20FleetMind-blue?style=for-the-badge)](YOUR_VERCEL_URL_HERE)
[![Backend API](https://img.shields.io/badge/Backend%20API-Swagger%20Docs-green?style=for-the-badge)](YOUR_RENDER_URL_HERE/docs)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue?style=flat-square)](https://react.dev)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML%20Engine-orange?style=flat-square)](https://xgboost.ai)

---

## What Is FleetMind?

Unplanned industrial machine failure costs manufacturers an average of **$260,000 per hour** in downtime. Most factories either react after the machine breaks, or follow fixed maintenance schedules regardless of actual machine condition — both approaches are expensive and inefficient.

FleetMind is a full-stack AI platform that monitors industrial machines in real time, predicts failures before they occur, and explains *why* a machine is at risk — in plain language any maintenance engineer can act on.

**This is not a Jupyter notebook.** It's a production-grade platform with a real authenticated API, a live dashboard, explainable AI, and an autonomous alert system.

---

## Live Demo

> **[→ Open FleetMind Dashboard](YOUR_VERCEL_URL_HERE)**
>
> Login: `ramesh@fleetmind.dev` / `FleetMind@123`

What to try:
1. Log in and see the machine fleet health dashboard
2. Click any machine card to see the detailed prediction — health score, failure probability, SHAP explanation, RUL estimate, and root cause text
3. Visit the Alert Center (bell icon) to see and acknowledge active alerts
4. Check the [API docs](YOUR_RENDER_URL_HERE/docs) to explore every endpoint

---

## Key Features

**Failure Prediction**
XGBoost classifier trained on the AI4I 2020 Predictive Maintenance dataset. Predicts failure probability for each machine reading. Handles class imbalance (3.4% failure rate) via SMOTE oversampling + class weights + threshold tuning. Achieves ROC-AUC of 0.98 and PR-AUC of 0.85 on held-out test data.

**Explainable AI (SHAP)**
Every prediction comes with a SHAP breakdown showing which sensor features drove the prediction and by how much. Built using TreeSHAP (exact, not approximate) for sub-millisecond inference. The dashboard displays this as human-readable percentage contributions — no data science background required to interpret.

**Failure Mode Classification**
Five dedicated XGBoost classifiers (one per failure mode: TWF, HDF, PWF, OSF, RNF) identify not just *that* a machine will fail, but *how* — heat dissipation failure, power failure, overstrain, tool wear, or random fault. This turns a prediction into an actionable maintenance directive.

**Remaining Useful Life (RUL)**
Physics-informed RUL estimation derived from tool wear degradation and failure probability signals. Returns cycle count and hours remaining with a trend indicator (STABLE → DECLINING → CRITICAL_DECLINE).

**Health Score System**
Weighted combination of failure probability and normalized RUL into a single 0–100 score. Maps directly to five alert severity levels: NORMAL → LOW → MEDIUM → HIGH → CRITICAL. Designed for non-technical users — no probability interpretation required.

**Root Cause Analysis**
Hybrid ML + rule engine that maps SHAP values and failure mode probabilities to specific, sensor-value-aware maintenance text. Output: *"Heat dissipation failure risk (99% probability). Cooling gap narrowed to 7.1K (critical threshold: 8.6K). Check cooling system and airflow."* Not generic — specific.

**Automated Alert System**
Alerts fire automatically when health score crosses configured thresholds. Duplicate prevention logic ensures one active alert per machine per severity level. Full acknowledgment workflow with audit trail (who acknowledged, when, with what note).

**Multi-Machine Dashboard**
Real-time fleet overview with machine cards color-coded by health level. Summary counts by severity (Critical / High / Medium / Normal). Clicking any machine navigates to its full prediction detail page.

---

## Architecture

```
┌─────────────────┐     HTTPS + JWT      ┌──────────────────────┐
│   React Frontend │ ──────────────────▶ │   FastAPI Backend     │
│   (Vercel)       │ ◀────────────────── │   (Render)            │
└─────────────────┘                      └──────────┬───────────┘
                                                     │
                               ┌─────────────────────┼──────────────────────┐
                               │                     │                      │
                    ┌──────────▼──────┐   ┌──────────▼──────┐   ┌──────────▼──────┐
                    │   ML Module     │   │    Supabase      │   │   Alert Engine  │
                    │                 │   │   (PostgreSQL)   │   │                 │
                    │ XGBoost Models  │   │                  │   │ Threshold check │
                    │ SHAP Explainer  │   │ 7 tables + RLS   │   │ Deduplication   │
                    │ Health Score    │   │ JWT Auth         │   │ Audit trail     │
                    │ Root Cause      │   │ Row Level Sec.   │   │                 │
                    └─────────────────┘   └─────────────────┘   └─────────────────┘
```

**Prediction Flow (12 steps):**
```
HTTP Request → JWT Validation → Plant Authorization → Fetch Sensor Readings
→ Feature Engineering → XGBoost Inference → SHAP Explanation
→ Health Score Calculation → Root Cause Generation
→ Store Prediction → Create Alert (if threshold crossed) → Return Response
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React 18 + Vite | Component-based, fast dev experience |
| Styling | Tailwind CSS | Utility-first, rapid UI development |
| Auth | Supabase Auth + JWT | Production-grade, zero custom auth code |
| Backend | FastAPI (Python 3.11) | Async, auto-docs, native ML ecosystem |
| Database | Supabase (PostgreSQL) | Hosted, RLS, realtime-capable |
| ML Core | XGBoost + scikit-learn | Industry standard for tabular data |
| Explainability | SHAP (TreeSHAP) | Exact Shapley values, sub-ms inference |
| Deployment | Render + Vercel | Free tier, GitHub auto-deploy |

---

## Dataset

**AI4I 2020 Predictive Maintenance Dataset** (UCI ML Repository)
- 10,000 observations of a simulated CNC machine
- 5 sensor features + 4 engineered features
- Binary failure label + 5 failure mode sub-labels
- 3.4% failure rate (class imbalance handled via SMOTE + class weights)

**Why this dataset?** AI4I provides labeled failure modes (HDF, PWF, OSF, TWF) which enable the root cause analysis module — a feature most predictive maintenance demos skip entirely because their dataset only has a binary label.

---

## ML Performance

| Model | Metric | Score |
|---|---|---|
| Failure Classifier | ROC-AUC | 0.9806 |
| Failure Classifier | PR-AUC | 0.8467 |
| Failure Classifier | Recall (failure class) | 0.91 |
| HDF Mode Classifier | ROC-AUC | 0.9998 |
| PWF Mode Classifier | ROC-AUC | 0.9997 |
| OSF Mode Classifier | ROC-AUC | 1.0000 |
| TWF Mode Classifier | ROC-AUC | 0.9488 |

**Note on TWF:** Low F1 (0.11) due to only 36 positive training examples. ROC-AUC (0.95) confirms the model's ranking ability is good — insufficient data prevents clean threshold separation. In production, more historical TWF examples would resolve this.

**Note on dataset:** AI4I uses mathematically-defined failure conditions (synthetic). Model metrics reflect this — real-world noisy sensor data would produce lower but more generalizable metrics. The architecture is designed for real sensor streams; AI4I is used as a realistic simulation.

---

## Project Structure

```
fleetmind/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── app/
│   │   ├── core/                  # Config, security, dependencies
│   │   ├── routers/               # HTTP layer (sensors, predictions, machines, alerts)
│   │   ├── services/              # Business logic (prediction pipeline, alerts)
│   │   ├── models/                # Pydantic request/response schemas
│   │   └── db/                    # Supabase client + schema
│   ├── ml/
│   │   ├── preprocessor.py        # Feature engineering pipeline
│   │   ├── predictor.py           # Model inference (failure, modes, RUL)
│   │   ├── explainer.py           # TreeSHAP explanations
│   │   ├── health_score.py        # 0-100 health score calculation
│   │   ├── root_cause.py          # Hybrid ML + rule root cause generation
│   │   ├── models/                # Trained .joblib files
│   │   └── notebooks/             # EDA + training notebooks
│   └── scripts/
│       └── simulate_sensors.py    # Autonomous sensor simulation
└── frontend/
    ├── src/
    │   ├── pages/                 # Login, Dashboard, MachineDetail, AlertCenter
    │   ├── components/            # MachineCard, HealthGauge, SHAPBarChart, AlertBanner
    │   ├── context/               # AuthContext (JWT session management)
    │   └── lib/                   # Supabase client, Axios API instance
    └── vite.config.js
```

---

## Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Supabase project (free tier)

### Backend Setup

```bash
cd fleetmind/backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

Create `.env` from `.env.example` and fill in your Supabase credentials:
```bash
cp .env.example .env
# Edit .env with your SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_JWT_SECRET
```

Run the database schema in Supabase SQL Editor:
```bash
# Copy contents of backend/app/db/schema.sql → paste in Supabase SQL Editor → Run
```

Start the backend:
```bash
uvicorn main:app --reload
# API running at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Frontend Setup

```bash
cd fleetmind/frontend
npm install
```

Create `.env` from `.env.example`:
```bash
cp .env.example .env
# Edit .env with your VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_BASE_URL
```

Start the frontend:
```bash
npm run dev
# Running at http://localhost:5173
```

### Simulate Live Sensor Data

```bash
cd fleetmind/backend
python scripts/simulate_sensors.py
# Posts sensor readings every 5 seconds, triggers predictions automatically
```

---

## Design Decisions Worth Discussing

**Why XGBoost over neural networks?**
AI4I has 10,000 rows and 339 failure examples. Research consistently shows tree-based models outperform deep learning on tabular datasets under 100k rows (Grinsztajn et al., 2022). XGBoost also has native TreeSHAP integration, making explainability computationally trivial — a key product requirement.

**Why monolith over ML microservice?**
At V1 scale, splitting ML into a separate service doubles infrastructure complexity with no performance benefit. The ML module is structured for easy extraction (clean interface via `predictor.py`, `explainer.py`) when load requires it — V2 decision.

**Why not timestamps in AI4I?**
AI4I is cross-sectional, not time-series. Standard stratified K-fold validation was used rather than temporal splits. In production with real sensor streams, time-based splits and concept drift monitoring would be applied.

**Why Supabase over raw PostgreSQL?**
Supabase provides hosted PostgreSQL + Row Level Security + Auth + realtime subscriptions. For V1, this eliminates infrastructure management while retaining full PostgreSQL capability. RLS ensures data isolation at the database level, not just the API level — defense in depth.

---

## What This Demonstrates

- **Machine Learning:** Classification, multi-label classification, imbalanced data handling, feature engineering, SHAP explainability
- **Backend Engineering:** RESTful API design, JWT authentication, role-based access control, dependency injection, service layer architecture
- **Database Design:** Relational schema, foreign keys, indexes, Row Level Security policies
- **Frontend Development:** React hooks, context API, protected routing, async data fetching
- **System Design:** End-to-end ML pipeline, alert system design, multi-tenant data isolation
- **Product Thinking:** User personas, MVP scoping, operational vs technical metrics, explainability for non-technical users

---

## Author

**Vedant Bhakare**
Second-year CSE (AI) student at VIT Pune
