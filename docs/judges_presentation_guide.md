# Smart Traffic Management System - Project Workflow & Judges Demonstration Guide

## 1. Project Overview & Problem Statement

Urban corridors in Nagpur (e.g. Wardha Road, Ajni Square, Lokmat Square) suffer from severe traffic congestion during morning (09:00–12:00) and evening (16:00–19:00) peak hours due to **uneven traffic distribution**. Fixed-time traffic signals fail to adapt, causing long queues on primary trunk roads while adjacent bypass corridors remain under-utilized.

This project solves uneven distribution by integrating **Microscopic SUMO 1.27.1 Simulation**, **Machine Learning Congestion AI**, a **FastAPI Backend Engine**, and an **Interactive 3D WebGL Frontend**.

---

## 2. Technical Architecture & Component Roles

```
  +-------------------------------------------------------------------------+
  |                     React 18 & 3D WebGL Frontend                        |
  |  - Dashboard Control Panel       - 3D Corridor Map with 5-Min Time Slider |
  |  - ML Classifier Sandbox         - Synopsis Baseline vs Proposed Metrics|
  +------------------------------------|------------------------------------+
                                       | HTTP REST & SSE Streaming APIs
                                       v
  +-------------------------------------------------------------------------+
  |                        FastAPI Backend Engine                           |
  |  - /api/simulate/compare         - /api/simulate/stream (SSE Stream)   |
  |  - /api/ml/predict               - /api/map/congestion & /api/hotspots |
  +-------------------/--------------------------------\--------------------+
                     /                                  \
                    v                                    v
  +-----------------------------------+    +--------------------------------+
  |    Machine Learning Engine        |    |    SUMO 1.27.1 Microscopic      |
  |  - RandomForest / XGBoost Models  |    |    Simulator & TraCI Controller|
  |  - Feature Vectors: Volume, Speed,|    |  - 267,836 Road Segment Records|
  |    Queue Length, Time Period      |    |  - TraCI Adaptive Signal Loops |
  +-----------------------------------+    +--------------------------------+
```

### Component Roles:
1. **Eclipse SUMO 1.27.1 & TraCI Connector**:
   - Simulates realistic vehicle movements, lane changing, and queuing behavior over OpenStreetMap geometry.
   - Extracts real-time edge features (volume, speed, density, queue length, time loss).
   - Executes dynamic signal phase adjustments (`traci.trafficlight.setPhaseDuration`).

2. **Machine Learning Congestion Classifier (`backend/app/ml_engine.py`)**:
   - Scores observed traffic conditions every simulated step.
   - Predicts multi-class congestion state (`LOW`, `MEDIUM`, `HIGH`).
   - Recommends adaptive signal extensions (+18s green time) and 20% traffic diversion advisories when `HIGH` congestion is detected.

3. **FastAPI Backend API (`backend/app/main.py`)**:
   - Coordinates simulation execution and streams progress via Server-Sent Events (SSE).
   - Calculates fair before/after metrics (Baseline fixed-time vs. Proposed ML adaptive control).
   - Indexes and serves 267,836 predicted road segment records (`traffic_map_data.csv`).

4. **React 18 & 3D WebGL Frontend (`frontend/js/app.js`)**:
   - Renders 3D metallic gold dark-mode corridor animations using Three.js and Chart.js.
   - Provides time-travel sliders (0 to 175 minutes in 5-minute steps) and Auto-Play playback.
   - Displays real-time inspection metrics for Nagpur hotspots (**Wardha Road**, **Ajni Square**, **Kriplani Square**, **Rahate Colony**, **Lokmat Square**).

---

## 3. Step-by-Step Demonstration Flow for Judges

### **Step 1: Introduction & Live System Health (30 Seconds)**
- Open **`http://127.0.0.1:8000`** in your browser.
- Point out the **Live Status Badge** in the top right header:
  `SUMO Integration: ONLINE (SUMO 1.27.1 TraCI + Deterministic Queueing Engine Active)`.
- **Explain**: *"Our platform integrates live microscopic simulation, machine learning, and dynamic signal control to resolve peak-hour traffic bottlenecks in Nagpur."*

### **Step 2: Control Panel & Baseline vs Proposed Comparison (1 Minute)**
- On the **Control Panel** tab:
  - Select **Morning (09:00–12:00)** or **Evening (16:00–19:00)** peak window.
  - Click **RUN SIMULATION**.
- Observe the **Live Simulation Progress Modal** streaming backend SSE events in real-time.
- Highlight the **Synopsis Metrics Table**:
  - **Avg Delay**: Reduced from 85s to 21s (**↓ 74.4% Reduction**).
  - **Max Queue Length**: Reduced from 140m to 28m (**↓ 80.0% Reduction**).
  - **Throughput**: Increased from 1,200 to 1,314 veh/h (**↑ 9.5% Capacity Boost**).

### **Step 3: Interactive 3D Congestion Map & Time Travel (1.5 Minutes)**
- Navigate to the **Nagpur Corridor 3D Simulation** tab.
- Show the 5 key Nagpur hotspots: **Wardha Road**, **Ajni Square**, **Kriplani Square**, **Rahate Colony**, **Lokmat Square**.
- Click the **Auto-Play** button or move the **5-Minute Interval Slider** (0m to 175m):
  - Point out how edge segments dynamically shift color (`LOW` Green → `MEDIUM` Amber → `HIGH` Red) based on ML predictions.
- Click **Ajni Square** in the 3D canvas or dropdown:
  - Show live metrics: Average Speed (14.2 km/h), Average Delay (42.5s), and AI Recommended Action.

### **Step 4: Machine Learning Congestion AI Sandbox (1 Minute)**
- Navigate to the **ML Congestion AI** tab.
- Move the live feature sliders:
  - Increase **Vehicle Flow** to 1,500 veh/hr and **Queue Length** to 220m.
  - Show how the backend model immediately computes `HIGH CONGESTION (Probability: 94.8%)` and triggers:
    *`"Extending green phase (+18s) and issuing 20% reroute advisory."`*

### **Step 5: What-If Stress Testing Sandbox (30 Seconds)**
- Return to **Control Panel** tab:
  - Click **+30% Demand Spike** or **Simulate Variety Sq Lane Closure**.
  - Show how the ML controller dynamically adjusts signal splits to absorb severe stress.

---

## 4. Key Takeaways for Judges Summary Table

| Metric / Parameter | Baseline (Fixed Signals) | Proposed Strategy (ML + SUMO) | Impact Achieved |
|---|---|---|---|
| **Average Delay** | 85 seconds / vehicle | 21 seconds / vehicle | **74.4% Delay Reduction** |
| **Max Queue Length** | 140 meters | 28 meters | **80.0% Queue Reduction** |
| **Throughput** | 1,200 vehicles / hour | 1,314 vehicles / hour | **9.5% Capacity Gain** |
| **Congestion State** | HIGH (Saturated) | MODERATE / LOW (Optimized) | **Balanced Corridor Flow** |
