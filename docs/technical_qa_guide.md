# Technical Q&A Guide: How Every Page & Feature Works Under the Hood

---

## 🖥️ Category 1: Frontend Dashboard & Interactive Map (`index.html`, `app.js`, `style.css`)

### Q1: How does the frontend render the Nagpur traffic map and color-code road edges in real time?
**Answer**:
- **Initialization**: The Leaflet map (`L.map('map')`) initializes centered on Nagpur city coordinates (`21.1458° N, 79.0882° E`).
- **GeoJSON Parsing**: When the dashboard loads, `fetch('/api/map/congestion?time_period=Morning')` retrieves a GeoJSON `FeatureCollection` containing 294 OSM edge geometries.
- **Dynamic Styling**: Each feature has a `congestion_level` (`LOW`, `MODERATE`, `HIGH`) and a normalized `flow_score` (0.0 to 1.0). Leaflet applies a dynamic color palette:
  - `LOW` (flow < 0.4): Cyan/Green `#00F2FE` (free flow)
  - `MODERATE` (0.4 ≤ flow < 0.75): Amber `#F6D365` (moderate queue)
  - `HIGH` (flow ≥ 0.75): Crimson `#FF0844` (saturation spillback)
- **Polyline Tooltips**: Clicking any edge opens a popup rendering edge length, speed limit, lane count, and live ML congestion probability.

---

### Q2: How does the frontend handle real-time simulation progress updates without freezing the browser?
**Answer**:
- **Server-Sent Events (SSE)**: When a user clicks **Run Simulation**, `app.js` opens an `EventSource` connection to `/api/simulate/stream`.
- **Event Streaming**: The FastAPI backend streams two custom SSE event types:
  1. `event: progress` — Sends `{"pct": 30, "status": "Generating peak demand profile..."}` to update a smooth CSS loading bar.
  2. `event: result` — Transmits the final simulation output JSON once computation completes.
- **Asynchronous UI Updates**: Using non-blocking async promises, the main event loop remains free, allowing smooth map zooming and panel animations during execution.

---

### Q3: How do the live intersection signal countdown timers work?
**Answer**:
- **Timer Controller**: `app.js` maintains a JavaScript `setInterval` running every 1000ms.
- **State Machine**: Cycles through Green $\rightarrow$ Yellow $\rightarrow$ Red phases based on optimal phase allocations returned by `/api/simulate`.
- **CSS Keyframes**: Signal components in `style.css` use CSS custom properties (`var(--signal-green)`, `var(--signal-red)`) with keyframe glow effects (`box-shadow: 0 0 15px currentColor`) to render realistic light illuminations.

---

## 🚦 Category 2: SUMO Microscopic Simulation & TraCI Engine (`sumo_runner.py`, `sitabuldi_sim.py`)

### Q4: How is the OpenStreetMap (OSM) map converted into a SUMO network binary?
**Answer**:
- **OSM Extraction**: Nagpur street networks were exported via `netconvert` tool using:
  ```bash
  netconvert --osm-files sitabuldi.osm -o sitabuldi_junction.net.xml --geometry.remove --ramps.guess --tls.discard-loaded --tls.guess
  ```
- **Edge Coordinate Transformation**: `sitabuldi_sim.py` uses SUMO's `traci.simulation.convert2D()` utility to translate local SUMO network X/Y cartesian coordinates into spatial WGS84 Longitude/Latitude pairs for Leaflet map polylines.

---

### Q5: How does TraCI extract second-by-second vehicle telemetry?
**Answer**:
- **Execution Loop**: `sitabuldi_sim.py` launches SUMO in headless mode (`sumo -c ... --no-step-log`) and establishes a TCP socket connection via Python `traci.start()`.
- **Micro-Step Telemetry Extraction**:
  ```python
  for step in range(800):
      traci.simulationStep()
      for veh_id in traci.vehicle.getIDList():
          x, y = traci.vehicle.getPosition(veh_id)
          lon, lat = traci.simulation.convert2D(net_id, x, y)
          speed = traci.vehicle.getSpeed(veh_id)
          edge_id = traci.vehicle.getRoadID(veh_id)
  ```
- **Data Scale**: Generates 18,857 frame records saved into `sim_output_clean.json`.

---

### Q6: How does autonomous vehicle rerouting work in SUMO under the hood?
**Answer**:
- **Rerouting Device**: Vehicles are injected with SUMO's `device.rerouting` parameter (`rerouting.probability=1.0`, `rerouting.period=20`).
- **Dynamic Edge Cost Update**: Every 20 seconds, TraCI evaluates edge travel times based on current queue density:
  $$c_e = \frac{L_e}{v_e} \cdot \left(1 + \alpha \left(\frac{N_e}{K_e}\right)^\beta\right)$$
  where $L_e$ is edge length, $v_e$ is mean speed, $N_e$ is vehicle count, and $K_e$ is lane capacity.
- **Route Deviation Detection**: `sitabuldi_sim.py` compares each vehicle's `traci.vehicle.getRoute()` against its original departure route, logging genuine edge deviations (**9 verified reroute events recorded**).

---

## 🤖 Category 3: Machine Learning Engine (`ml_engine.py`, `model.pkl`)

### Q7: What features feed into the ML model and how is congestion classified?
**Answer**:
- **Feature Vector**: 4 input variables: `[volume_veh_hr, speed_kmh, queue_veh, time_period_encoded]`.
- **Model Classifier**: Pre-trained **RandomForestClassifier** (100 decision trees) trained on OSM traffic features.
- **Classification Decision Thresholds**:
  - `LOW` (Gini impurity split on speed > 30 km/h and queue < 10 veh).
  - `MODERATE` (speed 15–30 km/h, queue 10–30 veh).
  - `HIGH` (speed < 15 km/h, queue > 30 veh, saturation ratio > 0.85).
- **Probability Output**: Returns class probabilities e.g., `{'LOW': 0.03, 'MODERATE': 0.917, 'HIGH': 0.053}`.

---

### Q8: How does the AI recommendation generator work?
**Answer**:
- **Rule Engine**: `recommended_action()` maps the predicted class and confidence score to specific traffic control directives:
  - If `HIGH` (>85% confidence): *"Trigger immediate Signal Timing Override: Add +15s green phase to Eastbound approach & send reroute advisory."*
  - If `MODERATE`: *"Trending toward saturation. Monitoring queue growth rate; standby for secondary phase extension."*
  - If `LOW`: *"Free flow detected. Maintaining baseline energy-efficient cycle."*

---

## 📹 Category 4: Computer Vision & CCTV Stream Engine (`video_detect.py`)

### Q9: How does YOLOv8 + ByteTrack prevent vehicle double-counting?
**Answer**:
- **Object Detection**: YOLOv8 (`yolov8n.pt`) detects vehicles per frame with bounding boxes `[x1, y1, x2, y2, confidence, class_id]` (classes: car, bus, truck, motorcycle).
- **ByteTrack Association**: ByteTrack associates detections across consecutive frames by matching Kalman filter state predictions using Intersection-over-Union (IoU) distance.
- **Unique Track ID**: Assigns a persistent `track_id` to each vehicle. When a vehicle stops at a red light, its `track_id` remains unchanged, ensuring the cumulative count increments only when a new `track_id` enters the Region of Interest (ROI).

---

### Q10: How does HTTP Range video streaming work in `main.py`?
**Answer**:
- **Partial Content Delivery**: Endpoint `/api/sumo/video-stream` parses incoming `Range: bytes=start-end` HTTP headers.
- **Streaming Response**: Serves video in 64KB chunks using Python async generators with status `206 Partial Content` and header `Content-Range: bytes start-end/file_size`.
- **HTML5 Player Seeking**: Enables smooth scrubbing and seeking on the frontend `<video>` player without downloading the entire video file.

---

## ⚙️ Category 5: Backend REST API Services (`main.py`, `simulation_engine.py`)

### Q11: How does the custom deterministic queueing simulation calculate delays?
**Answer**:
- **Point-Queue Model**: Models each intersection as a deterministic queueing system evaluated in 5-minute time steps over a 3-hour window (36 steps).
- **Queue Dynamics Equation**:
  $$Q(t + \Delta t) = \max\left(0, Q(t) + (\lambda(t) - \mu(t)) \cdot \Delta t\right)$$
  where $\lambda(t)$ is arrival rate (veh/hr), $\mu(t)$ is departure capacity under active green time, and $Q(t)$ is queue backlog.
- **Delay Formula**: Average step delay is computed via Webster's approximation:
  $$d = \frac{C (1 - g/C)^2}{2 (1 - \min(1, x) \cdot g/C)} + \frac{x^2}{2 q (1 - x)}$$
  where $C$ is cycle length, $g$ is green time, $x$ is degree of saturation ($\lambda / \mu$), and $q$ is flow rate.

---

### Q12: How are CORS and static file routing configured in FastAPI?
**Answer**:
- **CORS Middleware**: Configured with `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]` to allow seamless local development and cross-origin frontend API calls.
- **Static Mounting**: `app.mount("/static", StaticFiles(...))` mounts `frontend/`, `css/`, and `js/` folders so FastAPI serves both REST endpoints and frontend assets on a single unified port (`http://127.0.0.1:8000`).

---

## 📊 Category 6: Quantitative Performance & Formulae

### Q13: What math governs the adaptive green time allocation $G_{opt}$?
**Answer**:
- **Adaptive Green Time Formula**:
  $$G_{opt} = \max\left(G_{min}, \min\left(G_{max}, \frac{Q + \lambda \cdot C}{S}\right)\right)$$
  - $G_{min} = 15\text{s}$ (minimum pedestrian clearance)
  - $G_{max} = 60\text{s}$ (maximum phase constraint)
  - $Q$ = measured queue backlog (vehicles)
  - $\lambda$ = arrival rate (veh/s)
  - $C$ = total cycle time (90s)
  - $S$ = saturation flow rate (1.8 veh/s per lane)

---

### Q14: How are the verified final improvement metrics calculated?
**Answer**:
- **Delay Reduction (-66.5%)**:
  $$\text{Improvement} = \frac{85.0\text{s (Baseline)} - 28.5\text{s (Proposed)}}{85.0\text{s}} \times 100 = 66.47\% \approx \mathbf{66.5\%}$$
- **Queue Reduction (-74.3%)**:
  $$\text{Improvement} = \frac{140.0\text{m} - 36.0\text{m}}{140.0\text{m}} \times 100 = \mathbf{74.28\%}$$
- **Throughput Gain (+28.0%)**:
  $$\text{Gain} = \frac{1600\text{ veh/hr} - 1250\text{ veh/hr}}{1250\text{ veh/hr}} \times 100 = \mathbf{28.0\%}$$
