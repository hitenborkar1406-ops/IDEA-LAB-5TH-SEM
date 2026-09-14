# Smart Traffic Management System for Uneven Traffic Distribution (Nagpur City)

An integrated traffic management platform featuring an HTML5/React 3D WebGL frontend, FastAPI backend server, machine learning congestion classifier, and modular SUMO simulation interface.

## System Architecture & Folder Layout

```
Smart_Traffic_Project/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI server & route handlers
│   │   ├── ml_engine.py          # Machine learning congestion classifier
│   │   ├── network_data.py       # Corridor topology & signal timing parameters
│   │   ├── schemas.py            # Pydantic data schemas
│   │   └── simulation_engine.py  # Custom deterministic queueing engine
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── css/
│   │   └── style.css            # Custom High-Contrast Metallic Gold Dark CSS
│   ├── js/
│   │   ├── app.js               # React 18 frontend UI & 3D WebGL engine
│   │   └── app.jsx              # React JSX source code
│   └── index.html               # Main application web entrypoint
├── ml/
│   ├── models/                  # Pre-trained ML models (.joblib, .json)
│   └── create_final_map_dataset.py
├── sumo/
│   ├── sumo_interface.py        # Abstract adapter interface for SUMO & Queueing
│   ├── osm.net.xml.gz           # Nagpur network file
│   ├── morning_edge_geometry.csv
│   ├── evening_edge_geometry.csv
│   └── README.md                # SUMO connection instructions
├── docs/
│   ├── architecture.md          # Detailed architecture overview
│   └── api_docs.md              # REST API reference
├── .env.example
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser and navigate to:
`http://localhost:8000`

Interactive API Docs are accessible at `http://localhost:8000/docs`.

## Integration Workflow
- **Frontend → Backend API → ML → Backend → Frontend**:
  - The React frontend connects directly to `/api/simulate/compare` for live baseline vs proposed evaluations.
  - The simulation progress modal streams live simulation progress & logs using Server-Sent Events (`/api/simulate/stream`).
  - The ML Congestion AI tab queries `/api/ml/predict` for real-time congestion predictions.
  - The Analytics tab visualizes timeseries charts powered by `/api/analytics`.

## SUMO Integration
SUMO integration is decoupled via `sumo/sumo_interface.py`. When SUMO is installed on the system and `SUMO_HOME` is configured in `.env`, the adapter can seamlessly toggle to microscopic SUMO simulations without modifying frontend or backend logic.
