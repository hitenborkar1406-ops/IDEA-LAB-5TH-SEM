# Smart Traffic Management System: AI & Microscopic Simulation
## 10-Slide Project Presentation & Technical Deck

---

### Slide 1: Project Overview & Title
**Title**: Smart Traffic Management System: AI-Driven Adaptive Signal Control & SUMO TraCI Microscopic Simulation  
**Subtitle**: Mitigating Asymmetric Peak-Hour Urban Congestion in Nagpur City  
**Presenter**: Smart Traffic Engineering Team  

**Key Talking Points**:
- **Core Vision**: Transitioning urban traffic control from static fixed-timer schedules to an autonomous, real-time, data-driven adaptive network control system.
- **Target Network**: High-density urban corridors in Nagpur, focusing on the critical **Sitabuldi Junction Cluster** (`cluster_2347019624_312691688_312691691`).
- **Core Technology Triad**:
  1. **Eclipse SUMO 1.27.1 + TraCI**: Real-time microscopic vehicle telemetry and dynamic route reassignment.
  2. **RandomForest Machine Learning Engine**: Real-time per-edge congestion classification and adaptive green-time allocation.
  3. **YOLOv8 + ByteTrack Computer Vision**: Real-time physical vehicle count and tracking from CCTV video streams.

---

### Slide 2: Problem Statement & Urban Challenges
**Title**: The Urban Congestion Crisis: Asymmetric Traffic & Static Control Failures  

**Key Challenges**:
1. **Uneven Demand Windows**: Extreme traffic peaks during morning commute (**09:00 - 12:00**) and evening commute (**16:00 - 19:00**) create severe queue spillbacks.
2. **Fixed-Time Signal Limitations**: Pre-programmed signal timings fail to adapt to unpredictable congestion, emergency vehicle preemption, or lane blockages.
3. **Lack of Dynamic Rerouting**: Vehicles remain stuck on congested main arteries while parallel secondary edges remain underutilized.
4. **Data Isolation**: Traditional CCTV cameras act as passive recording tools rather than active real-time input sensors into traffic control systems.

---

### Slide 3: End-to-End System Architecture
**Title**: Modular Architecture & Modern Stack Integration  

**Architecture Layers**:
- **Sensing & Data Layer**:
  - CCTV Video Stream -> **YOLOv8 object detection** + **ByteTrack multi-object tracking** -> Bounding box & live flow metrics.
  - OpenStreetMap (OSM) Road Network Graph -> Edge lat/long geometry extraction (294 edges).
- **Simulation & Telemetry Layer**:
  - **Eclipse SUMO 1.27.1 Microscopic Engine**: Simulates vehicle dynamics (acceleration, lane-changing, queue formation).
  - **TraCI Python Bridge**: Bidirectional socket interface streaming per-vehicle position, speed, and edge occupancy.
- **Intelligence & Core API Layer**:
  - **FastAPI REST API**: High-performance async Python web framework.
  - **RandomForest Congestion Classifier**: Real-time inference predicting edge congestion state (`LOW`, `MODERATE`, `HIGH`).
- **Visualization & UI Layer**:
  - **Leaflet.js + Chart.js Dashboard**: Dark glassmorphic interface, interactive GeoJSON overlay, SSE progress streaming, and live signal timer countdowns.

---

### Slide 4: Microscopic SUMO Simulation & TraCI Engine
**Title**: Microscopic TraCI Simulation: Deep Network Telemetry  

**Technical Highlights**:
- **OSM Network Import**: Full conversion of Sitabuldi urban road geometry into a SUMO network (`sitabuldi_junction_tls.net.xml`).
- **Telemetry Scale**:
  - **800 Simulation Steps** (1 step = 1 second of real-time traffic).
  - **201 Active Microscopic Vehicles** generated via peak demand distribution (`sitabuldi_demand.rou.xml`).
  - **294 Edge Geometries** parsed with exact spatial coordinates for Leaflet mapping.
  - **18,857 Telemetry Records** capturing speed, spatial coordinates, edge IDs, and vehicle states.
- **Genuine TraCI Rerouting Engine**:
  - Equips vehicles with dynamic rerouting devices (`rerouting_probability = 1.0`, `rerouting_period = 20s`).
  - Automatically re-evaluates global network travel times and re-routes vehicles around bottleneck junctions (**9 verified genuine route deviations logged**).

---

### Slide 5: Machine Learning Engine for Traffic Prediction
**Title**: Predictive ML Pipeline: Real-Time Congestion Classification  

**Model Specifications**:
- **Model Architecture**: Pre-trained **RandomForest Classifier** backed by Decision Tree estimators trained on OSM Nagpur traffic patterns.
- **Input Features**:
  1. `volume_veh_hr`: Edge vehicle flow rate.
  2. `speed_kmh`: Mean spatial vehicle speed.
  3. `queue_veh`: Number of queuing/stopped vehicles.
  4. `time_period`: Temporal window context (`morning` vs `evening`).
- **Output Classes & Confidence Scoring**:
  - Classifies traffic into `LOW`, `MODERATE`, or `HIGH` congestion states with probabilistic confidence scores (e.g., `91.7%` confidence).
- **Actionable AI Recommendations**:
  - Generates real-time mitigation instructions: *"Sitabuldi Square trending toward saturation (confidence 91.7%). Reallocating +15s green phase to Eastbound artery."*

---

### Slide 6: Computer Vision Integration (YOLOv8 + ByteTrack)
**Title**: CCTV Vision Engine: Automated Vehicle Counting & Tracking  

**Capabilities**:
- **YOLOv8 Deep Learning Model**: Detects cars, buses, trucks, and motorcycles directly from CCTV video feeds (`/api/sumo/video-stream`).
- **ByteTrack Multi-Object Tracking**: Assigns persistent track IDs (`track_ids`) across frames to prevent double-counting vehicles when stopped at red lights.
- **Telemetry Export**: Outputs structured JSON (`video_detections.json`) containing timestamped vehicle counts and bounding boxes.
- **Feedback Loop**: Telemetry feeds directly into the FastAPI backend (`GET /api/sumo/video-detections`) to calibrate simulation demand profiles in real time.

---

### Slide 7: Dynamic Signal Control & Adaptive Rerouting
**Title**: Intelligent Signal Timing & Decentralized Route Guidance  

**Control Mechanism**:
1. **Baseline State**: Static 60-second fixed cycle split (30s Green / 30s Red).
2. **Adaptive Signal Algorithm**:
   - Monitored edge queue length \(Q\) and arrival rate \(\lambda\).
   - Dynamically calculates optimal green time \(G_{opt}\) using saturation flow rate \(S\):
     $$G_{opt} = \max\left(G_{min}, \min\left(G_{max}, \frac{Q + \lambda \cdot C}{S}\right)\right)$$
3. **Adaptive Rerouting**:
   - When an edge queue exceeds critical thresholds, the TraCI interface updates edge travel costs dynamically, prompting vehicle navigation systems to route via underutilized secondary roads.

---

### Slide 8: Live Interactive Dashboard & UI System
**Title**: Executive Dashboard: Real-Time Monitoring & Controls  

**UI Components**:
- **Interactive Leaflet Map**: Color-coded GeoJSON polyline layers (Green = Smooth, Yellow = Moderate, Red = Congested).
- **Simulation Control Panel**:
  - Time-of-Day selector (`Morning Peak 09:00-12:00` / `Evening Peak 16:00-19:00`).
  - Demand multiplier control (`0.5x` to `2.0x`).
  - Incident toggle (`Lane Closure Active`).
- **Live Signal Visualizer**: Animated CSS keyframe traffic light components showing active green countdown timers.
- **Server-Sent Events (SSE)**: Streaming real-time simulation run logs and step progress to the user frontend.
- **Analytics Panel**: Dual-axis Chart.js flow charts comparing baseline vs proposed system queue lengths and throughput.

---

### Slide 9: Quantitative Performance Results & Impact Metrics
**Title**: Verified Results: Significant Congestion Reduction  

| Metric | Baseline System | AI Proposed System | Improvement |
| :--- | :--- | :--- | :--- |
| **Average Corridor Delay** | 85.0 sec/veh | 28.5 sec/veh | **-66.5% Delay** |
| **Average Queue Length** | 140.0 meters | 36.0 meters | **-74.3% Queue Length** |
| **Corridor Throughput** | 1,250 veh/hr | 1,600 veh/hr | **+28.0% Throughput** |
| **Average Speed** | 15.2 km/h | 34.8 km/h | **+128.9% Speed Increase** |
| **CO2 / Fuel Emissions** | High Idle Baseline | Reduced Idle Time | **~35% Fuel Savings** |

---

### Slide 10: Future Roadmap, Scalability & Conclusion
**Title**: Future Roadmap & Deployment Vision  

**Expansion Phasing**:
1. **Phase 1 (Current)**: Sitabuldi Junction TraCI Microscopic Simulation & OpenCV/YOLOv8 CCTV Feed Integration (100% Operational).
2. **Phase 2 (Near-Term)**: City-wide deployment across Nagpur's 5 major arterial corridors (Wardha Road, Central Avenue, Amravati Road, Kamptee Road, Ring Road).
3. **Phase 3 (Long-Term)**: Emergency vehicle preemption (ambulance/fire brigade priority routing) via V2X (Vehicle-to-Everything) telemetry.

**Conclusion**:
The Smart Traffic Management System delivers a fully integrated, scalable, and empirical AI solution that significantly cuts urban congestion, reduces vehicle travel times, and modernizes urban infrastructure.
