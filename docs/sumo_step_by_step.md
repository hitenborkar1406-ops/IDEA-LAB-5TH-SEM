# SUMO Live Execution - Step-by-Step Guide

This guide takes you step-by-step through connecting and executing Eclipse SUMO with TraCI live in the Smart Traffic Management Platform.

---

## Step 1: Verify SUMO Installation Path
Ensure Eclipse SUMO is installed on your Windows system.
Default Windows installation folder:
```
C:\Program Files (x86)\Eclipse\Sumo
```

To verify SUMO from PowerShell / Command Prompt:
```powershell
& "C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" --version
```

---

## Step 2: Configure Environment Variables
Open or create `.env` in your project root directory (`Smart_Traffic_Project/.env`):
```env
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
SUMO_HOME=C:/Program Files (x86)/Eclipse/Sumo
SIMULATION_ENGINE_TYPE=sumo
```

---

## Step 3: Test SUMO TraCI Python Adapter
Run the TraCI adapter test script from PowerShell:
```powershell
python -c "import os, sys; sys.path.append(os.path.join(os.getenv('SUMO_HOME', 'C:/Program Files (x86)/Eclipse/Sumo'), 'tools')); import traci; print('TraCI import successful! SUMO is ready.')"
```

---

## Step 4: Run the Web Platform with Live SUMO
Launch the backend server:
```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://localhost:8000` in your web browser.

---

## Step 5: Execute Simulation with Real TraCI Control Loop
1. Navigate to the **Control Panel** tab.
2. Select **Morning (09:00-12:00)** or **Evening (16:00-19:00)** window.
3. Click **RUN SIMULATION**.
4. The simulation progress modal will connect to the backend SSE stream (`/api/simulate/stream`), executing live signal phase extensions (+18s) and dynamic rerouting (20% diversion) on Wardha Road, Ajni Square, and Lokmat Square corridors!
