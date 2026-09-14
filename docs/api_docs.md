# API Documentation

## Base Endpoint
- Development Server: `http://localhost:8000`

## Endpoints Summary

### 1. Health Check
- **GET** `/api/health`
- **Response**:
  ```json
  {
    "status": "ok",
    "engine": "custom-deterministic-queueing",
    "sumo": false,
    "api_version": "1.0.0"
  }
  ```

### 2. Node Metadata
- **GET** `/api/nodes?corridor=corridor-a`
- **Response**: Array of Nagpur intersection configurations.

### 3. Scenario Comparison
- **POST** `/api/simulate/compare`
- **Request Payload**:
  ```json
  {
    "time_window": "morning",
    "demand_multiplier": 1.0,
    "lane_closure": false,
    "corridor": "corridor-a"
  }
  ```
- **Response**: Side-by-side comparison object (`baseline`, `proposed`, `improvement`).

### 4. Live Simulation SSE Stream
- **GET** `/api/simulate/stream?time_window=morning&scenario=proposed`
- **Response**: Server-Sent Events stream emitting progress and final result payloads.

### 5. ML Congestion Classifier
- **POST** `/api/ml/predict`
- **Request Payload**:
  ```json
  {
    "volume_veh_hr": 950,
    "speed_kmh": 18.5,
    "queue_veh": 140,
    "time_period": "morning",
    "node_name": "Variety Square Junction"
  }
  ```
- **Response**: Congestion class, probability, and recommended traffic management action.

### 6. Simulation Analytics Timeseries
- **GET** `/api/analytics?time_window=morning&corridor=corridor-a`
- **Response**: Aggregated 3-hour timeseries data for baseline vs proposed scenarios.
