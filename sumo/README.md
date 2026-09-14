# SUMO Integration Guide

This directory contains the files and interface connectors for Eclipse SUMO (Simulation of Urban MObility).

## Current Status
SUMO is currently disconnected / downloading. The platform automatically uses the deterministic queueing simulation engine (`backend/app/simulation_engine.py`) so all features, APIs, and UI controls remain 100% functional without requiring SUMO binary dependencies.

## Network Files
- `osm.net.xml.gz`: Compressed OpenStreetMap network file for Nagpur corridors.
- `morning_edge_geometry.csv`: Edge geometry & lane parameters for the Morning peak (09:00 - 12:00).
- `evening_edge_geometry.csv`: Edge geometry & lane parameters for the Evening peak (16:00 - 19:00).

## How to Connect SUMO Once Installed

1. **Install SUMO**:
   Download and install Eclipse SUMO from [https://sumo.dlr.de/](https://sumo.dlr.de/). Default Windows path is `C:\Program Files (x86)\Eclipse\Sumo`.

2. **Configure Environment Variables**:
   Update `.env` in the root directory:
   ```env
   SUMO_HOME=C:/Program Files (x86)/Eclipse/Sumo
   SIMULATION_ENGINE_TYPE=sumo
   ```

3. **Verify Connection**:
   The adapter in `sumo/sumo_interface.py` (`SUMOSimulationAdapter`) will automatically detect TraCI and `SUMO_HOME` and toggle the backend to run full microscopic SUMO simulations.
