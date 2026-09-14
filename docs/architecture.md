# Smart Traffic Management Platform - System Architecture

## Overview
The Smart Traffic Management System evaluates microscopic and deterministic traffic management strategies for peak morning (09:00-12:00) and evening (16:00-19:00) congestion across key Nagpur urban corridors (Variety Square, Samvidhan Square, Zero Mile, Rani Jhansi Square).

## Architecture Layout
```
                          +---------------------------------------+
                          |   Frontend (HTML5 / Vanilla JS / 3D)  |
                          |   React 18 UI / Three.js / Chart.js   |
                          +-------------------|-------------------+
                                              |
                                     HTTP / SSE API Calls
                                              |
                                              v
                          +---------------------------------------+
                          |        FastAPI Backend Engine         |
                          |       (backend/app/main.py)           |
                          +--------|----------------------|-------+
                                   |                      |
                        Simulation Adapter            ML Classifier
                                   |                      |
                                   v                      v
                +----------------------------+   +-------------------+
                | Traffic Simulation Adapter |   |  Scikit-Learn /   |
                | - Queueing (Active)        |   |  XGBoost Engine   |
                | - SUMO/TraCI (Adapter Ready)|   |  (ml_engine.py)   |
                +----------------------------+   +-------------------+
```

## Folder Structure
- `frontend/`: Web application interface (`index.html`, `css/style.css`, `js/app.js`).
- `backend/`: FastAPI application server (`backend/app/main.py`, `simulation_engine.py`, `ml_engine.py`, `network_data.py`, `schemas.py`).
- `ml/`: Pre-trained ML model assets (`ml/models/`) and data processing scripts.
- `sumo/`: SUMO network geometry files (`osm.net.xml.gz`, edge geometry CSVs) and modular SUMO TraCI adapter (`sumo_interface.py`).
- `docs/`: Technical documentation and API specifications.
