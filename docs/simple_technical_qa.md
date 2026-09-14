# Simple Technical Q&A: Every Page & Feature Explained

---

## 📄 Page 1: Main Traffic Map Dashboard (`index.html`, `app.js`)

### Q1: How does the main traffic map page work?
**Answer**:
- **Tech Used**: HTML5, Leaflet.js, OpenStreetMap GeoJSON.
- **How It Works**:
  1. The page loads an interactive Leaflet map focused on Nagpur city.
  2. It calls the backend API `GET /api/map/congestion` to fetch 294 road segments (edges).
  3. Roads are automatically colored based on congestion: **Green** for free traffic, **Yellow** for moderate traffic, and **Red** for heavy traffic.
  4. Clicking any road segment displays details like lane count, speed limit, and live traffic status.

---

## 🚦 Page 2: SUMO Microscopic Simulation Page (`sitabuldi_sim.py`, `sumo_runner.py`)

### Q2: How does the SUMO simulation page work?
**Answer**:
- **Tech Used**: Eclipse SUMO 1.27.1, Python TraCI Socket Bridge, WebSockets/JSON.
- **How It Works**:
  1. When you click **Run Simulation**, the backend launches SUMO in headless mode.
  2. TraCI streams data for 201 individual vehicles step-by-step across 800 seconds.
  3. Every vehicle’s position, speed, and road location are recorded (18,857 records total).
  4. The frontend renders moving dots on the map representing live vehicles navigating Nagpur’s Sitabuldi Junction.

---

## 📊 Page 3: Traffic Analytics & Baseline Comparison Page (`/api/analytics`)

### Q3: How does the analytics comparison page work?
**Answer**:
- **Tech Used**: Chart.js, FastAPI REST API.
- **How It Works**:
  1. The page requests comparison data from `GET /api/analytics`.
  2. It runs two scenarios side-by-side: **Baseline** (fixed signal timers) vs **AI Proposed** (adaptive signals).
  3. Chart.js draws dual-axis line charts comparing travel delay, queue length (meters), and vehicle throughput over a 3-hour peak window.
  4. It displays live improvement percentages (e.g., **66.5% reduction in delay**).

---

## 🤖 Feature 4: Machine Learning Congestion Prediction (`ml_engine.py`)

### Q4: How does the ML prediction feature work?
**Answer**:
- **Tech Used**: Python `scikit-learn`, RandomForest Classifier.
- **How It Works**:
  1. The ML model accepts 4 inputs: vehicle volume, average speed, queue count, and time of day (morning/evening peak).
  2. The pre-trained RandomForest model analyzes the data and classifies traffic into `LOW`, `MODERATE`, or `HIGH` congestion.
  3. It returns a confidence score (e.g., 91.7%) and an actionable recommendation (e.g., *"Extend green light by +15 seconds"*).

---

## 📹 Feature 5: CCTV Video Vehicle Detection & Tracking (`video_detect.py`)

### Q5: How does the CCTV camera vehicle detection feature work?
**Answer**:
- **Tech Used**: YOLOv8 (Ultralytics), ByteTrack, OpenCV, HTML5 Video Stream.
- **How It Works**:
  1. **YOLOv8** scans CCTV video feeds frame-by-frame to detect cars, buses, trucks, and bikes with bounding boxes.
  2. **ByteTrack** assigns a unique ID to each vehicle so stopped vehicles at red lights are not double-counted.
  3. The detected vehicle counts feed directly into the backend API to update real-time traffic demand.

---

## ⏱️ Feature 6: Dynamic Adaptive Signal Timer

### Q6: How does the adaptive traffic signal timer feature work?
**Answer**:
- **Tech Used**: Custom Queueing Algorithm, CSS Keyframe Animations.
- **How It Works**:
  1. Instead of fixed 30-second timers, the backend measures the exact queue length at an intersection.
  2. If a road has a long queue, the system automatically increases its green light time (up to 60s) and decreases red light time on empty roads.
  3. The frontend displays animated traffic light countdown timers in real time.

---

## 🔄 Feature 7: Autonomous Vehicle Rerouting

### Q7: How does the vehicle rerouting feature work?
**Answer**:
- **Tech Used**: SUMO TraCI Dynamic Re-routing Device.
- **How It Works**:
  1. Vehicles are equipped with dynamic rerouting capability in SUMO.
  2. Every 20 seconds, TraCI checks if a main road is jammed.
  3. If travel time on the main road becomes too high, TraCI automatically recalculates routes and directs vehicles onto open secondary side streets.

---

## ⚡ Feature 8: FastAPI Backend & Live Streaming API (`main.py`)

### Q8: How does the backend API and progress streaming work?
**Answer**:
- **Tech Used**: FastAPI, Python AsyncIO, Server-Sent Events (SSE).
- **How It Works**:
  1. FastAPI handles all REST requests (`/api/health`, `/api/simulate`, `/api/ml/predict`).
  2. For long simulation runs, it uses **Server-Sent Events (SSE)** to stream progress updates (`10%`, `50%`, `100%`) directly to the user's browser without reloading the page.
  3. Static file middleware serves the frontend HTML, CSS, and JS files from a single server port (`8000`).
