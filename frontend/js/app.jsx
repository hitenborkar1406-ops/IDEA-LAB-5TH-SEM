/* ==========================================================================
   SMART TRAFFIC MANAGEMENT SYSTEM FOR UNEVEN TRAFFIC DISTRIBUTION (NAGPUR)
   React 18 Component Application - Scientifically Rigorous Demo Version
   ========================================================================== */

const { useState, useEffect, useRef } = React;

// Demo Scenario Repository with Provenance
const DEMO_SCENARIOS = {
  'morning-peak': {
    baseline: {
      avgDelay: 85,
      queueLength: 140,
      travelTime: 12,
      throughput: 1200,
      congestionClass: 'HIGH',
      congestionProb: '88.4%',
      congestionIndex: '0.88',
      pillClass: 'red',
      title: 'Baseline (Fixed Signal Timings)',
      desc: 'Simulating standard fixed-time signal cycles (45s fixed green) without dynamic ML adjustments. High density produces severe queues at Variety Square and Zero Mile.',
      runId: 'DEMO_MORNING_BASE_001',
      simTime: '10:35:00 AM'
    },
    proposed: {
      avgDelay: 52,
      queueLength: 91,
      travelTime: 9,
      throughput: 1450,
      congestionClass: 'MODERATE',
      congestionProb: '42.1%',
      congestionIndex: '0.42',
      pillClass: 'green',
      title: 'Proposed (ML Adaptive Control & Dynamic Route Redistribution)',
      desc: 'Integrated smart traffic strategy combining ML adaptive signal timing (+18s green extension at Variety Sq) with dynamic route redistribution (20% traffic diverted to Ring Rd).',
      runId: 'DEMO_MORNING_OPT_001',
      simTime: '10:35:00 AM'
    }
  },
  'evening-peak': {
    baseline: {
      avgDelay: 94,
      queueLength: 158,
      travelTime: 14,
      throughput: 1150,
      congestionClass: 'HIGH',
      congestionProb: '93.2%',
      congestionIndex: '0.93',
      pillClass: 'red',
      title: 'Baseline (Fixed Signal Timings)',
      desc: 'Evening rush hour outbound commute (4:00 PM – 7:00 PM). Heavy traffic accumulation along Wardha Road towards Rahate Colony.',
      runId: 'DEMO_EVENING_BASE_001',
      simTime: '05:45:00 PM'
    },
    proposed: {
      avgDelay: 56,
      queueLength: 98,
      travelTime: 10,
      throughput: 1410,
      congestionClass: 'MODERATE',
      congestionProb: '46.5%',
      congestionIndex: '0.46',
      pillClass: 'green',
      title: 'Proposed (ML Adaptive Control & Dynamic Route Redistribution)',
      desc: 'Evening peak optimization: Adjusts signal offsets for outbound traffic and issues dynamic rerouting advisories via VMS.',
      runId: 'DEMO_EVENING_OPT_001',
      simTime: '05:45:00 PM'
    }
  }
};

// Nagpur Nodes Data Repository
const NAGPUR_NODES = {
  'node-1': {
    name: 'Intersection 1: Variety Square Junction',
    baselineVol: '950 veh/hr', baselineSpeed: '18.2 km/h', baselineQueue: '140 meters',
    proposedVol: '1,120 veh/hr', proposedSpeed: '39.5 km/h', proposedQueue: '91 meters',
    status: 'Severe Bottleneck', statusClass: 'red',
    mlAction: '"Wardha Rd approach occupancy exceeded 78% while Ring Rd bypass operates at 34% capacity. Re-allocating +18s green time and issuing 20% reroute advisory."',
    justification: 'High density accumulation on main trunk corridor; adjacent collector roads have 66% spare capacity.'
  },
  'node-2': {
    name: 'Intersection 2: Samvidhan Square (RBI Sq.)',
    baselineVol: '820 veh/hr', baselineSpeed: '22.4 km/h', baselineQueue: '128 meters',
    proposedVol: '980 veh/hr', proposedSpeed: '41.0 km/h', proposedQueue: '82 meters',
    status: 'Moderate Queue', statusClass: 'red',
    mlAction: '"Balanced approach volumes detected. Re-allocating 12s signal phase to Eastbound Central Avenue corridor."',
    justification: 'Central Avenue eastbound queue growth rate 1.4x higher than westbound flow.'
  },
  'node-3': {
    name: 'Intersection 3: Zero Mile Landmark Sq.',
    baselineVol: '910 veh/hr', baselineSpeed: '19.8 km/h', baselineQueue: '142 meters',
    proposedVol: '1,060 veh/hr', proposedSpeed: '38.2 km/h', proposedQueue: '90 meters',
    status: 'High Density', statusClass: 'red',
    mlAction: '"Zero Mile Metro corridor congestion detected. Deploying phase offset optimization across connected nodes 2 and 3."',
    justification: 'Metro station feeder vehicles creating intermittent blockage on left-turn lane.'
  },
  'node-4': {
    name: 'Intersection 4: Rani Jhansi Square Corridor',
    baselineVol: '780 veh/hr', baselineSpeed: '24.1 km/h', baselineQueue: '135 meters',
    proposedVol: '940 veh/hr', proposedSpeed: '42.8 km/h', proposedQueue: '88 meters',
    status: 'Heavy Peak Flow', statusClass: 'red',
    mlAction: '"Westbound Amravati Road traffic burst absorbed. Green wave progression synced with Variety Sq."',
    justification: 'Platoon arrival synchronized with Variety Sq phase green start.'
  }
};

// SUMO Project Code Strings
const SUMO_FILES = {
  sumocfg: `<?xml version="1.0" encoding="UTF-8"?>
<!-- SUMO Configuration File for Nagpur Sitabuldi Corridor -->
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <input>
        <net-file value="nagpur_sitabuldi.net.xml"/>
        <route-files value="peak_morning_demand.rou.xml"/>
        <additional-files value="detectors.add.xml"/>
    </input>
    <time>
        <begin value="32400"/> <!-- 9:00 AM in seconds -->
        <end value="43200"/>   <!-- 12:00 PM in seconds -->
        <step-length value="1.0"/>
    </time>
    <report>
        <no-step-log value="true"/>
        <duration-log.disable value="true"/>
    </report>
</configuration>`,

  traci: `# Python TraCI Adaptive Signal & Route Control Bridge
import os, sys
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import traci
import pandas as pd
import joblib

# Load Trained ML Model (Planned Integration)
ml_model = joblib.load("traffic_classifier_model.pkl")

def run_adaptive_traci_simulation():
    traci.start(["sumo", "-c", "nagpur_sitabuldi.sumocfg"])
    step = 0
    
    while step < 10800: # 3-hour peak simulation
        traci.simulationStep()
        
        # Read real-time queue & flow from E2 loop detectors
        queue_len = traci.edge.getLastStepHaltingNumber("wardha_rd_north")
        avg_speed = traci.edge.getLastStepMeanSpeed("wardha_rd_north") * 3.6
        veh_count = traci.edge.getLastStepVehicleNumber("wardha_rd_north")
        
        # Predict Congestion using ML model
        features = [[veh_count, avg_speed, queue_len, 1]] # Morning Peak
        prediction = ml_model.predict(features)[0] # 0: Low, 1: Medium, 2: High
        
        # Adjust signal phase & dynamic rerouting via TraCI
        if prediction == 2 and queue_len > 100:
            traci.trafficlight.setPhaseDuration("TLS_01", 65.0)
            
        step += 1
    traci.close()

if __name__ == "__main__":
    run_adaptive_traci_simulation()`,

  rou: `<?xml version="1.0" encoding="UTF-8"?>
<!-- Peak Demand Routes (.rou.xml) - Nagpur Sitabuldi Corridor -->
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <vType id="car" accel="2.6" decel="4.5" length="4.5" maxSpeed="13.89" vClass="passenger"/>
    <vType id="two_wheeler" accel="3.2" decel="5.0" length="1.8" maxSpeed="15.2" vClass="motorcycle"/>
    <vType id="auto_rickshaw" accel="2.0" decel="4.0" length="2.6" maxSpeed="11.1" vClass="taxi"/>
    <vType id="bus" accel="1.2" decel="3.5" length="10.5" maxSpeed="10.0" vClass="bus"/>

    <!-- Peak Demand Flows (9:00 AM - 12:00 PM) -->
    <flow id="flow_wardha_north" type="car" begin="32400" end="43200" vehsPerHour="550" from="E_Wardha_S" to="E_ZeroMile_N"/>
    <flow id="flow_2w_north" type="two_wheeler" begin="32400" end="43200" vehsPerHour="400" from="E_Wardha_S" to="E_ZeroMile_N"/>
    <flow id="flow_central_ave" type="auto_rickshaw" begin="32400" end="43200" vehsPerHour="250" from="E_Central_E" to="E_Amravati_W"/>
</routes>`,

  net: `<?xml version="1.0" encoding="UTF-8"?>
<!-- Nagpur Sitabuldi Road Network (.net.xml) generated via Netconvert -->
<net version="1.16" junctionCornerDetail="5" limitTurnSpeed="5.50" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <location netOffset="0.00,0.00" convBoundary="79.081,21.142,79.098,21.155" origBoundary="79.081,21.142,79.098,21.155" projParameter="+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"/>

    <edge id="E_Wardha_S" from="J_AirportSq" to="J_VarietySq" priority="3" type="highway.primary">
        <lane id="E_Wardha_S_0" index="0" speed="13.89" length="620.5" shape="..."/>
        <lane id="E_Wardha_S_1" index="1" speed="13.89" length="620.5" shape="..."/>
    </edge>

    <tlLogic id="TLS_VarietySq" type="static" programID="0" offset="0">
        <phase duration="45" state="GGggrrrrGGggrrrr"/>
        <phase duration="5"  state="yyggrrrryyggrrrr"/>
        <phase duration="35" state="rrrrGGggrrrrGGgg"/>
    </tlLogic>
</net>`
};

// ==========================================================================
// MAIN REACT APP COMPONENT
// ==========================================================================
function App() {
  const [activeTab, setActiveTab] = useState('tab-dashboard');
  const [selectedArea, setSelectedArea] = useState('corridor-a');
  const [selectedTime, setSelectedTime] = useState('morning-peak'); // 'morning-peak' or 'evening-peak'
  const [selectedScenario, setSelectedScenario] = useState('baseline');
  
  // Stress testing / What-if multiplier
  const [demandMultiplier, setDemandMultiplier] = useState(1.0); // 1.0, 1.1 (+10%), 1.2 (+20%), 1.3 (+30%)
  const [laneClosureActive, setLaneClosureActive] = useState(false);

  // Modal Simulation State
  const [isSimulating, setIsSimulating] = useState(false);
  const [simProgress, setSimProgress] = useState(0);
  const [simStatusText, setSimStatusText] = useState('Initializing Nagpur OSM Network...');
  const [simLogs, setSimLogs] = useState(['[SYS] Initializing simulation request...']);

  // Real System Clock
  const [systemTimeStr, setSystemTimeStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setSystemTimeStr(now.toLocaleTimeString('en-US', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleRunSimulation = () => {
    setIsSimulating(true);
    setSimProgress(0);
    setSimStatusText('Loading nagpur_sitabuldi.net.xml network...');
    setSimLogs(['[SYS] Initializing simulation request (Demo Mode)...']);

    const steps = [
      { pct: 15, status: 'Loading nagpur_sitabuldi.net.xml network...', log: '[SUMO] Loaded network file with 4 intersections, 18 edges, 36 lanes.' },
      { pct: 35, status: `Generating peak demand flows (${selectedTime === 'morning-peak' ? '9 AM-12 PM' : '4 PM-7 PM'})...`, log: `[DEMAND] Calibrated vehicle trips: ${(950 * demandMultiplier).toFixed(0)} veh/hr.` },
      { pct: 55, status: 'Connecting TraCI Python socket bridge...', log: '[TraCI] Connected to SUMO engine via port 8813 (Prototype Interface).' },
      { pct: 75, status: 'Running ML Congestion Classifier...', log: '[ML AI] RandomForest predicted High Congestion (Demo Probability: 88.4%). Triggering adaptive signal & reroute strategy.' },
      { pct: 90, status: 'Applying phase adjustments & dynamic rerouting...', log: '[TRAFFIC] Phase 2 extended +18s on Wardha Rd & 20% traffic redirected to Ring Rd.' },
      { pct: 100, status: 'Simulation Complete! Updating illustrative metrics...', log: '[DONE] Demo delay reduced from 85s to 52s (↓38.8%). Queue cleared by 49m.' }
    ];

    let current = 0;
    const interval = setInterval(() => {
      if (current < steps.length) {
        const s = steps[current];
        setSimProgress(s.pct);
        setSimStatusText(s.status);
        setSimLogs(prev => [...prev, s.log]);
        current++;
      } else {
        clearInterval(interval);
        setTimeout(() => {
          setIsSimulating(false);
        }, 600);
      }
    }, 450);
  };

  // Get active scenario data
  const rawInfo = DEMO_SCENARIOS[selectedTime][selectedScenario];
  const scenarioInfo = {
    ...rawInfo,
    avgDelay: Math.round(rawInfo.avgDelay * demandMultiplier * (laneClosureActive ? 1.25 : 1.0)),
    queueLength: Math.round(rawInfo.queueLength * demandMultiplier * (laneClosureActive ? 1.3 : 1.0)),
    throughput: Math.round(rawInfo.throughput / (laneClosureActive ? 1.15 : 1.0))
  };

  return (
    <div className="app-wrapper">
      
      {/* Header */}
      <header className="app-header">
        <div className="header-container">
          <div className="brand-identity">
            <div className="brand-logo">
              <i className="fa-solid fa-traffic-light glowing-icon"></i>
            </div>
            <div className="brand-text">
              <h1 className="project-title">SMART TRAFFIC MANAGEMENT SYSTEM FOR UNEVEN TRAFFIC DISTRIBUTION</h1>
              <p className="project-subtitle">
                <span className="badge-nagpur"><i className="fa-solid fa-location-dot"></i> Nagpur City Urban Corridors</span>
                <span className="badge-3d"><i className="fa-solid fa-cubes"></i> Three.js 3D Engine</span>
                <span className="badge-demo"><i className="fa-solid fa-flask"></i> Demo / Illustrative Data</span>
              </p>
            </div>
          </div>
          
          <div className="header-actions">
            <div className="system-status">
              <span className="status-indicator online"></span>
              <span className="status-text">SUMO Integration: <strong>PROTOTYPE</strong></span>
            </div>
            
            {/* Dual Clock: System Time vs Simulation Time */}
            <div className="dual-clock-container">
              <div className="clock-card">
                <i className="fa-regular fa-clock"></i>
                <div>
                  <div className="clock-label">System Time</div>
                  <span>{systemTimeStr || '06:23:00 PM'}</span>
                </div>
              </div>

              <div className="clock-card sim-clock">
                <i className="fa-solid fa-stopwatch"></i>
                <div>
                  <div className="clock-label">Simulation Time</div>
                  <span>{scenarioInfo.simTime}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Menubars (5 Tabs) & Peak Switcher Bar */}
      <nav className="main-navbar">
        <div className="nav-container">
          <div className="nav-tabs-group">
            <button className={`nav-item ${activeTab === 'tab-dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('tab-dashboard')}>
              <i className="fa-solid fa-gauge-high"></i>
              <span>Control Panel</span>
            </button>
            <button className={`nav-item ${activeTab === 'tab-traffic-map' ? 'active' : ''}`} onClick={() => setActiveTab('tab-traffic-map')}>
              <i className="fa-solid fa-cubes"></i>
              <span>Nagpur Corridor Traffic Simulation</span>
            </button>
            <button className={`nav-item ${activeTab === 'tab-ml-engine' ? 'active' : ''}`} onClick={() => setActiveTab('tab-ml-engine')}>
              <i className="fa-solid fa-brain"></i>
              <span>ML Congestion AI</span>
            </button>
            <button className={`nav-item ${activeTab === 'tab-analytics' ? 'active' : ''}`} onClick={() => setActiveTab('tab-analytics')}>
              <i className="fa-solid fa-chart-column"></i>
              <span>Simulation Analytics</span>
            </button>
            <button className={`nav-item ${activeTab === 'tab-sumo-pipeline' ? 'active' : ''}`} onClick={() => setActiveTab('tab-sumo-pipeline')}>
              <i className="fa-solid fa-car-side"></i>
              <span>SUMO</span>
            </button>
          </div>

          {/* Morning vs Evening Peak Quick Switcher */}
          <div className="peak-switcher-bar">
            <button className={`peak-switch-btn ${selectedTime === 'morning-peak' ? 'active morning' : ''}`} onClick={() => setSelectedTime('morning-peak')}>
              <i className="fa-solid fa-sun"></i> Morning (09:00–12:00)
            </button>
            <button className={`peak-switch-btn ${selectedTime === 'evening-peak' ? 'active evening' : ''}`} onClick={() => setSelectedTime('evening-peak')}>
              <i className="fa-solid fa-moon"></i> Evening (16:00–19:00)
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'tab-dashboard' && (
          <ControlPanelTab
            selectedArea={selectedArea} setSelectedArea={setSelectedArea}
            selectedTime={selectedTime} setSelectedTime={setSelectedTime}
            selectedScenario={selectedScenario} setSelectedScenario={setSelectedScenario}
            demandMultiplier={demandMultiplier} setDemandMultiplier={setDemandMultiplier}
            laneClosureActive={laneClosureActive} setLaneClosureActive={setLaneClosureActive}
            onRunSimulation={handleRunSimulation}
            scenarioInfo={scenarioInfo}
          />
        )}

        {activeTab === 'tab-traffic-map' && (
          <TrafficMap3DTab selectedScenario={selectedScenario} setSelectedScenario={setSelectedScenario} />
        )}

        {activeTab === 'tab-ml-engine' && (
          <MLEngineTab selectedTime={selectedTime} />
        )}

        {activeTab === 'tab-analytics' && (
          <AnalyticsTab selectedScenario={selectedScenario} selectedTime={selectedTime} />
        )}

        {activeTab === 'tab-sumo-pipeline' && (
          <SumoTab />
        )}
      </main>

      {/* Modal Progress Dialog */}
      {isSimulating && (
        <div className="modal-overlay active">
          <div className="modal-content glass-panel">
            <div className="modal-header">
              <h3><i className="fa-solid fa-gear fa-spin text-cyan"></i> Running SUMO Simulation & TraCI ML Loop</h3>
              <span className="modal-subtitle">Nagpur Corridor Simulation Engine</span>
            </div>

            <div className="modal-body">
              <div className="sim-progress-box">
                <div className="progress-label-row">
                  <span>{simStatusText}</span>
                  <span>{simProgress}%</span>
                </div>
                <div className="progress-bar-track">
                  <div className="progress-bar-fill" style={{ width: `${simProgress}%` }}></div>
                </div>
              </div>

              <div className="sim-console-log">
                {simLogs.map((log, idx) => (
                  <div key={idx} className="log-line">{log}</div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

// ==========================================================================
// TAB 1: CONTROL PANEL COMPONENT
// ==========================================================================
function ControlPanelTab({ selectedArea, setSelectedArea, selectedTime, setSelectedTime, selectedScenario, setSelectedScenario, demandMultiplier, setDemandMultiplier, laneClosureActive, setLaneClosureActive, onRunSimulation, scenarioInfo }) {
  return (
    <section className="tab-panel active">
      <div className="dashboard-grid">
        
        {/* Sidebar Controls */}
        <div className="control-card glass-panel">
          <div className="card-header">
            <h3><i className="fa-solid fa-sliders"></i> Simulation Parameters</h3>
            <span className="badge-demo">Demo Setup</span>
          </div>

          <form onSubmit={(e) => e.preventDefault()}>
            <div className="form-group">
              <label><i className="fa-solid fa-road"></i> Select Corridor / Area (Nagpur):</label>
              <select value={selectedArea} onChange={(e) => setSelectedArea(e.target.value)} className="custom-select">
                <option value="corridor-a">Corridor A: Sitabuldi Junction & Variety Sq. Network (4 Intersections)</option>
                <option value="corridor-b">Corridor B: Wardha Road Highway (Airport Sq. to Rahate Colony)</option>
                <option value="corridor-c">Corridor C: Central Avenue Commercial Corridor (Dosar Bhavan to Telephone Exch.)</option>
                <option value="corridor-d">Corridor D: Amravati Road Axis (Law College Sq. to University Campus)</option>
              </select>
              <span className="field-hint">Simulates a representative 2.4 km corridor with connected signals.</span>
            </div>

            <div className="form-group">
              <label><i className="fa-regular fa-clock"></i> Select Time Window:</label>
              <select value={selectedTime} onChange={(e) => setSelectedTime(e.target.value)} className="custom-select">
                <option value="morning-peak">Morning Peak Window (09:00 AM – 12:00 PM)</option>
                <option value="evening-peak">Evening Peak Window (16:00 PM – 19:00 PM)</option>
              </select>
              <span className="field-hint">High density commuter windows identified in Nagpur synopsis.</span>
            </div>

            <div className="form-group">
              <label><i className="fa-solid fa-diagram-project"></i> Select Scenario:</label>
              <select value={selectedScenario} onChange={(e) => setSelectedScenario(e.target.value)} className="custom-select">
                <option value="baseline">Scenario 1: Baseline (Fixed Signal Timings)</option>
                <option value="proposed">Scenario 2: Proposed (ML Adaptive Control & Dynamic Route Redistribution)</option>
              </select>
              <span className="field-hint">Compare standard fixed cycle vs ML-optimized adaptive & rerouting strategies.</span>
            </div>

            <button type="button" onClick={onRunSimulation} className="btn-primary-action glowing-btn">
              <i className="fa-solid fa-play"></i> RUN SIMULATION
            </button>
          </form>
        </div>

        {/* Dashboard Overview */}
        <div className="overview-container">
          
          <div className="scenario-summary-banner glass-panel">
            <div className="banner-info">
              <div className="banner-tag">CURRENT SCENARIO: {scenarioInfo.title.toUpperCase()}</div>
              <h2>Sitabuldi Junction Network ({selectedTime === 'morning-peak' ? '09:00 AM – 12:00 PM' : '16:00 PM – 19:00 PM'})</h2>
              <p>{scenarioInfo.desc}</p>
              
              {/* Provenance Metadata Box */}
              <div className="provenance-box">
                <div className="provenance-item"><span>Source:</span> <strong>SUMO Microscopic Simulation</strong></div>
                <div className="provenance-item"><span>Run ID:</span> <strong>{scenarioInfo.runId}</strong></div>
                <div className="provenance-item"><span>Data Status:</span> <strong className="text-amber">Demo / Illustrative Data</strong></div>
              </div>
            </div>

            <div className={`congestion-indicator-pill ${scenarioInfo.pillClass}`}>
              <i className="fa-solid fa-triangle-exclamation"></i>
              <span>CONGESTION: {scenarioInfo.congestionClass} ({scenarioInfo.congestionProb})</span>
            </div>
          </div>

          {/* Key Metric Cards */}
          <div className="kpi-cards-grid">
            <div className="kpi-card glass-panel">
              <div className="kpi-icon red-glow"><i className="fa-solid fa-hourglass-half"></i></div>
              <div className="kpi-details">
                <span className="kpi-label">Average Delay (Demo)</span>
                <div className="kpi-value-row">
                  <span className="kpi-value">{scenarioInfo.avgDelay} sec</span>
                  <span className={`kpi-compare-badge ${selectedScenario === 'baseline' ? 'red' : 'green'}`}>
                    {selectedScenario === 'baseline' ? 'Baseline' : '↓ 38.8%'}
                  </span>
                </div>
                <span className="kpi-subtext">Extra delay per vehicle vs free flow</span>
              </div>
            </div>

            <div className="kpi-card glass-panel">
              <div className="kpi-icon orange-glow"><i className="fa-solid fa-align-left"></i></div>
              <div className="kpi-details">
                <span className="kpi-label">Max Queue Length (Demo)</span>
                <div className="kpi-value-row">
                  <span className="kpi-value">{scenarioInfo.queueLength} m</span>
                  <span className={`kpi-compare-badge ${selectedScenario === 'baseline' ? 'red' : 'green'}`}>
                    {selectedScenario === 'baseline' ? 'Baseline' : '↓ 35.0%'}
                  </span>
                </div>
                <span className="kpi-subtext">Physical length of waiting queue</span>
              </div>
            </div>

            <div className="kpi-card glass-panel">
              <div className="kpi-icon yellow-glow"><i className="fa-solid fa-route"></i></div>
              <div className="kpi-details">
                <span className="kpi-label">Travel Time (Demo)</span>
                <div className="kpi-value-row">
                  <span className="kpi-value">{scenarioInfo.travelTime} min</span>
                  <span className={`kpi-compare-badge ${selectedScenario === 'baseline' ? 'red' : 'green'}`}>
                    {selectedScenario === 'baseline' ? 'Baseline' : '↓ 25.0%'}
                  </span>
                </div>
                <span className="kpi-subtext">Time taken to pass 2.4 km corridor</span>
              </div>
            </div>

            <div className="kpi-card glass-panel">
              <div className="kpi-icon green-glow"><i className="fa-solid fa-truck-fast"></i></div>
              <div className="kpi-details">
                <span className="kpi-label">Throughput (Demo)</span>
                <div className="kpi-value-row">
                  <span className="kpi-value">{scenarioInfo.throughput.toLocaleString()}</span>
                  <span className="kpi-unit">veh/hr</span>
                </div>
                <span className="kpi-subtext">Vehicles cleared per hour</span>
              </div>
            </div>
          </div>

          {/* Metric Comparison Table */}
          <div className="comparison-preview-card glass-panel">
            <div className="card-header">
              <h3><i className="fa-solid fa-code-compare"></i> Synopsis Baseline vs Proposed Metrics</h3>
              <span className="badge-demo"><i className="fa-solid fa-circle-info"></i> Demo Illustrative Data</span>
            </div>
            
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Metric Parameter</th>
                    <th>Scenario 1 (Baseline)</th>
                    <th>Scenario 2 (Proposed ML)</th>
                    <th>Net Improvement</th>
                    <th>Status Impact</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><i className="fa-solid fa-hourglass-half text-red"></i> <strong>Avg. Delay</strong></td>
                    <td className="baseline-col">85 sec</td>
                    <td className="proposed-col">52 sec</td>
                    <td className="improvement-col positive">↓ 33 sec (38.8%)</td>
                    <td><span className="badge-status success"><i className="fa-solid fa-arrow-down"></i> Delay Reduced</span></td>
                  </tr>
                  <tr>
                    <td><i className="fa-solid fa-align-left text-orange"></i> <strong>Queue Length</strong></td>
                    <td className="baseline-col">140 m</td>
                    <td className="proposed-col">91 m</td>
                    <td className="improvement-col positive">↓ 49 m (35.0%)</td>
                    <td><span className="badge-status success"><i className="fa-solid fa-arrow-down"></i> Queue Cleared</span></td>
                  </tr>
                  <tr>
                    <td><i className="fa-solid fa-route text-yellow"></i> <strong>Travel Time</strong></td>
                    <td className="baseline-col">12 min</td>
                    <td className="proposed-col">9 min</td>
                    <td className="improvement-col positive">↓ 3 min (25.0%)</td>
                    <td><span className="badge-status success"><i className="fa-solid fa-arrow-down"></i> Fast Flow</span></td>
                  </tr>
                  <tr>
                    <td><i className="fa-solid fa-truck-fast text-green"></i> <strong>Throughput</strong></td>
                    <td className="baseline-col">1,200 veh/h</td>
                    <td className="proposed-col">1,450 veh/h</td>
                    <td className="improvement-col positive">↑ 250 veh/h (20.8%)</td>
                    <td><span className="badge-status success"><i className="fa-solid fa-arrow-up"></i> Capacity Boost</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* P1: What-If Stress Testing Sandbox Card */}
          <div className="whatif-card glass-panel">
            <h3><i className="fa-solid fa-vial-circle-check"></i> What-If Scenario Stress Testing Sandbox</h3>
            <p>Simulate extreme network stress conditions (Demand Spikes & Lane Closures):</p>
            
            <div className="whatif-controls-row">
              <button className={`stress-btn ${demandMultiplier === 1.0 ? 'active' : ''}`} onClick={() => setDemandMultiplier(1.0)}>
                Standard Demand (100%)
              </button>
              <button className={`stress-btn ${demandMultiplier === 1.1 ? 'active' : ''}`} onClick={() => setDemandMultiplier(1.1)}>
                <i className="fa-solid fa-arrow-trend-up"></i> +10% Spike
              </button>
              <button className={`stress-btn ${demandMultiplier === 1.2 ? 'active' : ''}`} onClick={() => setDemandMultiplier(1.2)}>
                <i className="fa-solid fa-arrow-trend-up"></i> +20% Spike
              </button>
              <button className={`stress-btn ${demandMultiplier === 1.3 ? 'active' : ''}`} onClick={() => setDemandMultiplier(1.3)}>
                <i className="fa-solid fa-arrow-trend-up"></i> +30% Extreme Surge
              </button>
              <button className={`stress-btn ${laneClosureActive ? 'active' : ''}`} onClick={() => setLaneClosureActive(!laneClosureActive)}>
                <i className="fa-solid fa-road-barrier"></i> {laneClosureActive ? 'Variety Sq Lane Closed [ON]' : 'Simulate Variety Sq Lane Closure'}
              </button>
            </div>
          </div>

          {/* P1: Traffic Imbalance & Capacity Utilization Meter */}
          <div className="glass-panel">
            <h3><i className="fa-solid fa-scale-unbalanced"></i> Corridor Traffic Imbalance & Utilization</h3>
            <p>Uneven volume distribution across primary Wardha Road vs secondary Ring Road bypass:</p>

            <div className="imbalance-grid">
              <div className="imbalance-card glass-panel">
                <div className="imbalance-header">
                  <span><strong>Wardha Road Trunk Corridor</strong></span>
                  <span className="text-red font-bold">92% Capacity (Saturated)</span>
                </div>
                <div className="imbalance-bar-track">
                  <div className="imbalance-bar-fill high" style={{ width: '92%' }}></div>
                </div>
                <span className="field-hint">Requires signal extension + reroute diversion.</span>
              </div>

              <div className="imbalance-card glass-panel">
                <div className="imbalance-header">
                  <span><strong>Ring Road Bypass Corridor</strong></span>
                  <span className="text-green font-bold">34% Capacity (Underutilized)</span>
                </div>
                <div className="imbalance-bar-track">
                  <div className="imbalance-bar-fill low" style={{ width: '34%' }}></div>
                </div>
                <span className="field-hint">Available capacity to absorb diverted vehicles.</span>
              </div>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
}

// ==========================================================================
// TAB 2: NAGPUR 3D TRAFFIC MAP COMPONENT (THREE.JS WEBGL 3D ENGINE)
// ==========================================================================
function TrafficMap3DTab({ selectedScenario, setSelectedScenario }) {
  const mountRef = useRef(null);
  const [inspectNode, setInspectNode] = useState('node-1');

  useEffect(() => {
    const container = mountRef.current;
    if (!container || typeof THREE === 'undefined') return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 520;

    // 1. Three.js Scene Setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x030712);
    scene.fog = new THREE.FogExp2(0x030712, 0.008);

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 110, 160);
    camera.lookAt(0, 0, 0);

    // 3. Renderer Setup
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 4. OrbitControls
    let controls = null;
    if (typeof THREE.OrbitControls !== 'undefined') {
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;
      controls.maxPolarAngle = Math.PI / 2 - 0.05;
    }

    // 5. Lighting Setup
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.2);
    dirLight.position.set(100, 150, 50);
    scene.add(dirLight);

    // 6. Ground Grid Mesh
    const gridHelper = new THREE.GridHelper(300, 30, 0x38bdf8, 0x1e293b);
    gridHelper.position.y = -0.1;
    scene.add(gridHelper);

    // 7. Create 3D Roads
    const roadMaterial = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.8 });
    
    // East-West Main Corridor Road
    const ewGeo = new THREE.BoxGeometry(260, 0.4, 24);
    const ewRoad = new THREE.Mesh(ewGeo, roadMaterial);
    scene.add(ewRoad);

    // North-South Vertical Road
    const nsGeo = new THREE.BoxGeometry(24, 0.4, 260);
    const nsRoad = new THREE.Mesh(nsGeo, roadMaterial);
    scene.add(nsRoad);

    // 8. Create 4 Nagpur 3D Intersection Nodes with Light Spheres
    const nodePositions = [
      { id: 'node-1', x: -60, z: 0, label: 'Variety Sq' },
      { id: 'node-2', x: 0, z: 0, label: 'Samvidhan Sq' },
      { id: 'node-3', x: 60, z: 0, label: 'Zero Mile Sq' },
      { id: 'node-4', x: 0, z: -60, label: 'Rani Jhansi Sq' }
    ];

    const isBaseline = (selectedScenario === 'baseline');
    const nodeSpheres = [];

    nodePositions.forEach(pos => {
      // 3D Pillar
      const pillarGeo = new THREE.CylinderGeometry(6, 6, 4, 16);
      const isBottleneck = isBaseline && (pos.id === 'node-1' || pos.id === 'node-3');
      const nodeColor = isBottleneck ? 0xf87171 : 0x4ade80;

      const pillarMat = new THREE.MeshStandardMaterial({
        color: nodeColor,
        emissive: nodeColor,
        emissiveIntensity: isBottleneck ? 0.6 : 0.3
      });
      const pillar = new THREE.Mesh(pillarGeo, pillarMat);
      pillar.position.set(pos.x, 2, pos.z);
      scene.add(pillar);

      // 3D Traffic Light Beacon Tower
      const towerGeo = new THREE.CylinderGeometry(0.8, 0.8, 16, 8);
      const towerMat = new THREE.MeshStandardMaterial({ color: 0x475569 });
      const tower = new THREE.Mesh(towerGeo, towerMat);
      tower.position.set(pos.x, 10, pos.z);
      scene.add(tower);

      const lightSphereGeo = new THREE.SphereGeometry(2.5, 16, 16);
      const lightSphereMat = new THREE.MeshBasicMaterial({ color: nodeColor });
      const lightSphere = new THREE.Mesh(lightSphereGeo, lightSphereMat);
      lightSphere.position.set(pos.x, 18, pos.z);
      scene.add(lightSphere);
      nodeSpheres.push(lightSphere);
    });

    // 9. Create 3D Moving Vehicles
    const vehicles = [];
    const total3DVehicles = 32;

    for (let i = 0; i < total3DVehicles; i++) {
      const isCar = Math.random() > 0.3;
      const vehGeo = isCar ? new THREE.BoxGeometry(4, 2, 2.2) : new THREE.BoxGeometry(7, 3, 2.8);
      const vehColor = isBaseline ? 0xf87171 : (isCar ? 0x38bdf8 : 0x4ade80);
      const vehMat = new THREE.MeshStandardMaterial({ color: vehColor, roughness: 0.2 });
      const mesh = new THREE.Mesh(vehGeo, vehMat);

      const isEW = Math.random() > 0.4;
      mesh.position.y = isCar ? 1.2 : 1.7;

      if (isEW) {
        mesh.position.x = (Math.random() - 0.5) * 240;
        mesh.position.z = Math.random() > 0.5 ? 4 : -4;
        mesh.userData = { axis: 'x', dir: Math.random() > 0.5 ? 1 : -1, speed: 0.4 + Math.random() * 0.5 };
      } else {
        mesh.position.x = Math.random() > 0.5 ? 4 : -4;
        mesh.position.z = (Math.random() - 0.5) * 240;
        mesh.rotation.y = Math.PI / 2;
        mesh.userData = { axis: 'z', dir: Math.random() > 0.5 ? 1 : -1, speed: 0.4 + Math.random() * 0.5 };
      }
      scene.add(mesh);
      vehicles.push(mesh);
    }

    // 10. Animation Loop
    let animId = null;
    const animate = () => {
      animId = requestAnimationFrame(animate);

      if (controls) controls.update();

      // Move 3D vehicles
      vehicles.forEach(v => {
        const speed = isBaseline ? v.userData.speed * 0.35 : v.userData.speed;
        if (v.userData.axis === 'x') {
          v.position.x += v.userData.dir * speed;
          if (v.position.x > 120) v.position.x = -120;
          if (v.position.x < -120) v.position.x = 120;
        } else {
          v.position.z += v.userData.dir * speed;
          if (v.position.z > 120) v.position.z = -120;
          if (v.position.z < -120) v.position.z = 120;
        }
      });

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || 800;
      const h = container.clientHeight || 520;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animId) cancelAnimationFrame(animId);
    };
  }, [selectedScenario]);

  const currentNode = NAGPUR_NODES[inspectNode] || NAGPUR_NODES['node-1'];
  const isBaseline = (selectedScenario === 'baseline');

  return (
    <section className="tab-panel active">
      <div className="map-view-container">
        
        <div className="map-header glass-panel">
          <div className="map-title-box">
            <h2><i className="fa-solid fa-cubes"></i> Nagpur Corridor Traffic Simulation (3D WebGL Scene)</h2>
            <p>3D animated microscopic traffic mesh depicting Ajni Sq / Wardha Rd / Sitabuldi corridor.</p>
          </div>
          <div className="map-controls">
            <div className="toggle-group">
              <button className={`toggle-btn ${selectedScenario === 'baseline' ? 'active' : ''}`} onClick={() => setSelectedScenario('baseline')}>
                Baseline (Fixed)
              </button>
              <button className={`toggle-btn ${selectedScenario === 'proposed' ? 'active' : ''}`} onClick={() => setSelectedScenario('proposed')}>
                Proposed (ML Managed)
              </button>
            </div>
          </div>
        </div>

        <div className="map-grid">
          
          {/* 3D WebGL Canvas Card */}
          <div className="canvas-card glass-panel">
            <div className="canvas-toolbar">
              <span className="corridor-indicator"><i className="fa-solid fa-diamond-turn-right"></i> Nagpur 3D Corridor: <strong>Ajni - Wardha Rd - Sitabuldi Axis</strong></span>
              <span className="sim-speed-badge"><i className="fa-solid fa-bolt"></i> Simulation Speed: 1.0x (Sim Time)</span>
            </div>
            
            <div className="canvas-wrapper-3d">
              <div ref={mountRef} id="threeCanvasContainer"></div>
              <div className="overlay-3d-hint"><i className="fa-solid fa-hand-pointer"></i> Drag to rotate 360° | Scroll to zoom 3D</div>
            </div>

            <div className="legend-bar">
              <span className="legend-title">Congestion States:</span>
              <span className="legend-item"><span className="dot green"></span> Normal Flow (&gt; 35 km/h)</span>
              <span className="legend-item"><span className="dot yellow"></span> Moderate Queue (25-35 km/h)</span>
              <span className="legend-item"><span className="dot red"></span> Severe Bottleneck (&lt; 15 km/h)</span>
            </div>
          </div>

          {/* Node Inspector */}
          <div className="map-sidebar glass-panel">
            <h3><i className="fa-solid fa-magnifying-glass-location"></i> Corridor Node Inspector</h3>
            
            <div className="intersection-selector-box form-group">
              <label>Select Nagpur Node:</label>
              <select value={inspectNode} onChange={(e) => setInspectNode(e.target.value)} className="custom-select">
                <option value="node-1">Intersection 1: Variety Square Junction</option>
                <option value="node-2">Intersection 2: Samvidhan Square (RBI Sq.)</option>
                <option value="node-3">Intersection 3: Zero Mile Landmark Sq.</option>
                <option value="node-4">Intersection 4: Rani Jhansi Square Corridor</option>
              </select>
            </div>

            <div className="node-metrics-card">
              <div className="node-header">
                <h4>{currentNode.name.split(': ')[1]}</h4>
                <span className={`badge-node-status ${isBaseline ? 'red' : 'green'}`}>
                  {isBaseline ? currentNode.status : 'Optimized Stream'}
                </span>
              </div>

              <div className="node-stats-list">
                <div className="stat-row">
                  <span>Current Volume:</span>
                  <strong>{isBaseline ? currentNode.baselineVol : currentNode.proposedVol}</strong>
                </div>
                <div className="stat-row">
                  <span>Average Speed:</span>
                  <strong>{isBaseline ? currentNode.baselineSpeed : currentNode.proposedSpeed}</strong>
                </div>
                <div className="stat-row">
                  <span>Queue Length:</span>
                  <strong>{isBaseline ? currentNode.baselineQueue : currentNode.proposedQueue}</strong>
                </div>
              </div>

              <div className="signal-diagram-box">
                <div className="signal-head">
                  <div className="light red"></div>
                  <div className="light yellow"></div>
                  <div className="light green active"></div>
                </div>
                <div className="signal-timer">
                  <span className="timer-label">Adaptive Phase Time</span>
                  <span className="timer-value">24s</span>
                </div>
              </div>
            </div>

            <div className="ml-action-box">
              <span className="box-title"><i className="fa-solid fa-robot"></i> ML Traffic Manager Action</span>
              <p>{currentNode.mlAction}</p>
              <span className="field-hint" style={{ color: '#94a3b8', marginTop: '6px' }}>
                <strong>Justification:</strong> {currentNode.justification}
              </span>
            </div>

          </div>

        </div>

      </div>
    </section>
  );
}

// ==========================================================================
// TAB 3: ML CONGESTION AI COMPONENT (SCIENTIFICALLY RIGOROUS)
// ==========================================================================
function MLEngineTab({ selectedTime }) {
  const [volume, setVolume] = useState(950);
  const [speed, setSpeed] = useState(18);
  const [queue, setQueue] = useState(140);
  const chartRef = useRef(null);

  useEffect(() => {
    const ctx = document.getElementById('featureImportanceChart');
    if (!ctx || typeof Chart === 'undefined') return;

    if (chartRef.current) chartRef.current.destroy();

    chartRef.current = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Vehicle Flow (veh/h)', 'Average Speed (km/h)', 'Density (veh/km)', 'Occupancy (%)', 'Waiting Time (s)', 'Time Loss (s)'],
        datasets: [{
          label: 'Feature Weight (%)',
          data: [34, 26, 18, 12, 6, 4],
          backgroundColor: ['#38bdf8', '#818cf8', '#4ade80', '#fbbf24', '#f87171', '#ec4899'],
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#ffffff', font: { weight: 'bold' } } },
          y: { grid: { display: false }, ticks: { color: '#ffffff', font: { weight: 'bold' } } }
        }
      }
    });

    return () => {
      if (chartRef.current) chartRef.current.destroy();
    };
  }, []);

  // Compute Congestion Index Score & ML Class Probability
  let score = Math.round((volume / 1800) * 45 + ((60 - speed) / 60) * 35 + (queue / 300) * 20);
  score = Math.min(100, Math.max(0, score));
  const probIndex = (score / 100).toFixed(2);

  let predictedClass = 'HIGH';
  let classProb = '88.4%';
  let badgeClass = 'red';
  let stratText = 'Adaptive Signal Extension (+18s) & Dynamic Reroute Advisory';

  if (score >= 75) {
    predictedClass = 'CRITICAL / SEVERE'; classProb = '94.8%'; badgeClass = 'red'; stratText = 'Adaptive Signal Extension (+25s) & Reroute Diversion';
  } else if (score < 50 && score >= 30) {
    predictedClass = 'MEDIUM'; classProb = '82.5%'; badgeClass = 'green'; stratText = 'Standard Cycle Optimization';
  } else if (score < 30) {
    predictedClass = 'LOW'; classProb = '96.1%'; badgeClass = 'green'; stratText = 'Maintain Standard Phase Timing';
  }

  return (
    <section className="tab-panel active">
      <div className="ml-container">
        <div className="ml-header glass-panel">
          <div>
            <h2><i className="fa-solid fa-brain"></i> Machine Learning Congestion AI Engine (Prototype UI)</h2>
            <p>Targeting multi-class congestion classification (LOW, MEDIUM, HIGH, CRITICAL) using SUMO edge feature vectors.</p>
          </div>
          <span className="badge-ml-model"><i className="fa-solid fa-flask"></i> Model Architecture Prepared</span>
        </div>

        {/* P0 & P4: Model Specs & Performance Card */}
        <div className="model-spec-card glass-panel">
          <div className="card-header">
            <h3><i className="fa-solid fa-microchip"></i> Planned ML Model Metrics & Validation Specs</h3>
            <span className="badge-demo">Hiten's ML Pipeline Setup</span>
          </div>

          <div className="spec-grid">
            <div className="spec-box"><span className="lbl">Model Algorithm</span><span className="val text-cyan">Random Forest</span></div>
            <div className="spec-box"><span className="lbl">Test Accuracy (Demo)</span><span className="val text-green">91.7%</span></div>
            <div className="spec-box"><span className="lbl">Macro F1-Score</span><span className="val text-green">0.89</span></div>
            <div className="spec-box"><span className="lbl">Validation Strategy</span><span className="val">5-Fold CV</span></div>
            <div className="spec-box"><span className="lbl">Test Dataset Samples</span><span className="val">1,842</span></div>
          </div>
        </div>

        <div className="ml-simulator-card glass-panel">
          <h3><i className="fa-solid fa-sliders"></i> Live Prediction Classifier Sandbox</h3>
          <p>Adjust SUMO edge feature values to test real-time classification probability:</p>

          <form className="simulator-form" onSubmit={(e) => e.preventDefault()}>
            <div className="slider-group">
              <div className="slider-label-row">
                <label><i className="fa-solid fa-car"></i> Vehicle Flow (veh/hr):</label>
                <span className="slider-val">{volume}</span>
              </div>
              <input type="range" min="100" max="1800" value={volume} onChange={(e) => setVolume(parseInt(e.target.value))} className="custom-range" />
            </div>

            <div className="slider-group">
              <div className="slider-label-row">
                <label><i className="fa-solid fa-gauge-simple-high"></i> Average Speed (km/h):</label>
                <span className="slider-val">{speed}</span>
              </div>
              <input type="range" min="5" max="60" value={speed} onChange={(e) => setSpeed(parseInt(e.target.value))} className="custom-range" />
            </div>

            <div className="slider-group">
              <div className="slider-label-row">
                <label><i className="fa-solid fa-road-barrier"></i> Queue Length (meters):</label>
                <span className="slider-val">{queue}</span>
              </div>
              <input type="range" min="0" max="300" value={queue} onChange={(e) => setQueue(parseInt(e.target.value))} className="custom-range" />
            </div>

            <div className="slider-group">
              <div className="slider-label-row">
                <label><i className="fa-solid fa-clock-rotate-left"></i> Peak Hour Window:</label>
                <span className="slider-val">{selectedTime === 'morning-peak' ? '09:00 AM – 12:00 PM' : '16:00 PM – 19:00 PM'}</span>
              </div>
              <input type="text" readOnly value={selectedTime === 'morning-peak' ? 'Morning Peak Window' : 'Evening Peak Window'} className="custom-select" />
            </div>
          </form>

          {/* ML Result Box */}
          <div className="ml-result-output-box">
            <div className="ml-result-header">
              <span className="result-title">Live Classification Output:</span>
              <span className={`badge-congestion ${badgeClass}`}><i className="fa-solid fa-triangle-exclamation"></i> CONGESTION CLASS: {predictedClass}</span>
            </div>
            
            <div className="ml-metrics-row">
              <div className="ml-metric-item">
                <span className="label">Class Probability:</span>
                <span className="value text-cyan">{classProb}</span>
              </div>
              <div className="ml-metric-item">
                <span className="label">Congestion Index:</span>
                <span className="value text-orange">{probIndex} / 1.00</span>
              </div>
              <div className="ml-metric-item">
                <span className="label">Triggered Strategy:</span>
                <span className="value text-green">{stratText}</span>
              </div>
            </div>
          </div>

        </div>

        {/* SUMO Feature Importance Chart */}
        <div className="feature-chart-card glass-panel">
          <h3><i className="fa-solid fa-chart-bar"></i> SUMO Edge Feature Importance Breakdown</h3>
          <p>Relative weight assigned by the machine learning classifier to extracted SUMO edge features.</p>
          <div className="chart-container">
            <canvas id="featureImportanceChart"></canvas>
          </div>
        </div>

      </div>
    </section>
  );
}

// ==========================================================================
// TAB 4: SIMULATION ANALYTICS COMPONENT (WITH SEPARATE UNIT CHARTS)
// ==========================================================================
function AnalyticsTab({ selectedScenario, selectedTime }) {
  const delayChartRef = useRef(null);
  const queueChartRef = useRef(null);
  const travelChartRef = useRef(null);
  const throughputChartRef = useRef(null);

  useEffect(() => {
    if (typeof Chart === 'undefined') return;

    // 1. Separate Delay Chart
    const dCtx = document.getElementById('delayChart');
    if (dCtx) {
      if (delayChartRef.current) delayChartRef.current.destroy();
      delayChartRef.current = new Chart(dCtx, {
        type: 'bar',
        data: {
          labels: ['Baseline (Fixed)', 'Proposed (ML Managed)'],
          datasets: [{ label: 'Average Delay (seconds)', data: [85, 52], backgroundColor: ['#f87171', '#4ade80'], borderRadius: 6 }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: '#ffffff', font: { weight: 'bold' } } },
            y: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#ffffff', font: { weight: 'bold' } } }
          }
        }
      });
    }

    // 2. Separate Queue Chart
    const qCtx = document.getElementById('queueChart');
    if (qCtx) {
      if (queueChartRef.current) queueChartRef.current.destroy();
      queueChartRef.current = new Chart(qCtx, {
        type: 'bar',
        data: {
          labels: ['Baseline (Fixed)', 'Proposed (ML Managed)'],
          datasets: [{ label: 'Max Queue Length (meters)', data: [140, 91], backgroundColor: ['#fbbf24', '#4ade80'], borderRadius: 6 }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: '#ffffff', font: { weight: 'bold' } } },
            y: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#ffffff', font: { weight: 'bold' } } }
          }
        }
      });
    }

    // 3. Separate Travel Time Chart
    const tCtx = document.getElementById('travelChart');
    if (tCtx) {
      if (travelChartRef.current) travelChartRef.current.destroy();
      travelChartRef.current = new Chart(tCtx, {
        type: 'bar',
        data: {
          labels: ['Baseline (Fixed)', 'Proposed (ML Managed)'],
          datasets: [{ label: 'Travel Time (minutes)', data: [12, 9], backgroundColor: ['#facc15', '#4ade80'], borderRadius: 6 }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: '#ffffff', font: { weight: 'bold' } } },
            y: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#ffffff', font: { weight: 'bold' } } }
          }
        }
      });
    }

    // 4. Separate Throughput Chart
    const tpCtx = document.getElementById('throughputChart');
    if (tpCtx) {
      if (throughputChartRef.current) throughputChartRef.current.destroy();
      throughputChartRef.current = new Chart(tpCtx, {
        type: 'bar',
        data: {
          labels: ['Baseline (Fixed)', 'Proposed (ML Managed)'],
          datasets: [{ label: 'Throughput (veh/hr)', data: [1200, 1450], backgroundColor: ['#38bdf8', '#4ade80'], borderRadius: 6 }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: '#ffffff', font: { weight: 'bold' } } },
            y: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#ffffff', font: { weight: 'bold' } } }
          }
        }
      });
    }

    return () => {
      if (delayChartRef.current) delayChartRef.current.destroy();
      if (queueChartRef.current) queueChartRef.current.destroy();
      if (travelChartRef.current) travelChartRef.current.destroy();
      if (throughputChartRef.current) throughputChartRef.current.destroy();
    };
  }, [selectedScenario, selectedTime]);

  const handleExportCSV = () => {
    const csvContent = "data:text/csv;charset=utf-8," 
      + "Metric,Baseline,Proposed_ML,Improvement\n"
      + "Average Delay (sec),85,52,-38.8%\n"
      + "Max Queue Length (m),140,91,-35.0%\n"
      + "Corridor Travel Time (min),12,9,-25.0%\n"
      + "Vehicle Throughput (veh/h),1200,1450,+20.8%\n";

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "Nagpur_SUMO_Simulation_Metrics.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <section className="tab-panel active">
      <div className="analytics-container">
        <div className="analytics-header glass-panel">
          <div>
            <h2><i className="fa-solid fa-chart-line"></i> Simulation Performance & Analytics</h2>
            <p>Comparing Baseline vs Proposed across distinct metric units ({selectedTime === 'morning-peak' ? 'Morning 09:00–12:00' : 'Evening 16:00–19:00'}).</p>
          </div>
          <button onClick={handleExportCSV} className="btn-secondary">
            <i className="fa-solid fa-file-csv"></i> Export Metrics CSV
          </button>
        </div>

        {/* 4 Detail Cards */}
        <div className="metrics-detail-grid">
          <div className="detail-card glass-panel">
            <div className="detail-header"><i className="fa-solid fa-hourglass-half text-red"></i><h4>Average Delay</h4></div>
            <div className="detail-comparison">
              <div className="comp-box"><span className="lbl">Baseline</span><span className="val">85 sec</span></div>
              <div className="comp-arrow"><i className="fa-solid fa-right-long"></i></div>
              <div className="comp-box proposed"><span className="lbl">Proposed</span><span className="val text-green">52 sec</span></div>
            </div>
            <div className="improvement-bar-wrapper"><div className="improvement-bar" style={{ width: '38.8%' }}></div></div>
            <span className="improvement-text text-green"><i className="fa-solid fa-circle-arrow-down"></i> 38.8% Delay Reduction (33s saved/veh)</span>
          </div>

          <div className="detail-card glass-panel">
            <div className="detail-header"><i className="fa-solid fa-align-left text-orange"></i><h4>Queue Length</h4></div>
            <div className="detail-comparison">
              <div className="comp-box"><span className="lbl">Baseline</span><span className="val">140 m</span></div>
              <div className="comp-arrow"><i className="fa-solid fa-right-long"></i></div>
              <div className="comp-box proposed"><span className="lbl">Proposed</span><span className="val text-green">91 m</span></div>
            </div>
            <div className="improvement-bar-wrapper"><div className="improvement-bar" style={{ width: '35.0%' }}></div></div>
            <span className="improvement-text text-green"><i className="fa-solid fa-circle-arrow-down"></i> 35.0% Queue Reduction (49m cleared)</span>
          </div>

          <div className="detail-card glass-panel">
            <div className="detail-header"><i className="fa-solid fa-route text-yellow"></i><h4>Corridor Travel Time</h4></div>
            <div className="detail-comparison">
              <div className="comp-box"><span className="lbl">Baseline</span><span className="val">12 min</span></div>
              <div className="comp-arrow"><i className="fa-solid fa-right-long"></i></div>
              <div className="comp-box proposed"><span className="lbl">Proposed</span><span className="val text-green">9 min</span></div>
            </div>
            <div className="improvement-bar-wrapper"><div className="improvement-bar" style={{ width: '25.0%' }}></div></div>
            <span className="improvement-text text-green"><i className="fa-solid fa-circle-arrow-down"></i> 25.0% Travel Time Saved (3 min saved/trip)</span>
          </div>

          <div className="detail-card glass-panel">
            <div className="detail-header"><i className="fa-solid fa-truck-fast text-green"></i><h4>Network Throughput</h4></div>
            <div className="detail-comparison">
              <div className="comp-box"><span className="lbl">Baseline</span><span className="val">1,200</span></div>
              <div className="comp-arrow"><i className="fa-solid fa-right-long"></i></div>
              <div className="comp-box proposed"><span className="lbl">Proposed</span><span className="val text-green">1,450</span></div>
            </div>
            <div className="improvement-bar-wrapper"><div className="improvement-bar" style={{ width: '20.8%' }}></div></div>
            <span className="improvement-text text-green"><i className="fa-solid fa-circle-arrow-up"></i> 20.8% Capacity Boost (+250 veh/h)</span>
          </div>
        </div>

        {/* Separate Unit Charts Grid */}
        <div className="separate-charts-grid">
          <div className="separate-chart-card glass-panel">
            <h3><i className="fa-solid fa-hourglass-half text-red"></i> Average Delay Comparison (seconds)</h3>
            <div className="chart-container"><canvas id="delayChart"></canvas></div>
          </div>

          <div className="separate-chart-card glass-panel">
            <h3><i className="fa-solid fa-align-left text-orange"></i> Max Queue Length Comparison (meters)</h3>
            <div className="chart-container"><canvas id="queueChart"></canvas></div>
          </div>

          <div className="separate-chart-card glass-panel">
            <h3><i className="fa-solid fa-route text-yellow"></i> Corridor Travel Time Comparison (minutes)</h3>
            <div className="chart-container"><canvas id="travelChart"></canvas></div>
          </div>

          <div className="separate-chart-card glass-panel">
            <h3><i className="fa-solid fa-truck-fast text-green"></i> Vehicle Throughput Comparison (veh/hr)</h3>
            <div className="chart-container"><canvas id="throughputChart"></canvas></div>
          </div>
        </div>

        {/* Bottleneck Ranking Table */}
        <div className="table-card glass-panel">
          <h3><i className="fa-solid fa-list-ol"></i> Nagpur Bottleneck Ranking & Impact Table</h3>
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Nagpur Node Name</th>
                  <th>Baseline Delay</th>
                  <th>Proposed Delay</th>
                  <th>Baseline Queue</th>
                  <th>Proposed Queue</th>
                  <th>Throughput Gain</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>#1</strong></td>
                  <td><strong>Variety Square (Wardha Rd)</strong></td>
                  <td>92 sec</td>
                  <td className="text-green font-bold">54 sec</td>
                  <td>155 m</td>
                  <td className="text-green font-bold">98 m</td>
                  <td>+22% veh/h</td>
                  <td><span class="badge-status success">Optimized</span></td>
                </tr>
                <tr>
                  <td><strong>#2</strong></td>
                  <td><strong>Zero Mile Landmark Sq</strong></td>
                  <td>88 sec</td>
                  <td className="text-green font-bold">53 sec</td>
                  <td>142 m</td>
                  <td className="text-green font-bold">90 m</td>
                  <td>+21% veh/h</td>
                  <td><span className="badge-status success">Optimized</span></td>
                </tr>
                <tr>
                  <td><strong>#3</strong></td>
                  <td><strong>Rani Jhansi Square</strong></td>
                  <td>82 sec</td>
                  <td className="text-green font-bold">51 sec</td>
                  <td>135 m</td>
                  <td className="text-green font-bold">88 m</td>
                  <td>+20% veh/h</td>
                  <td><span className="badge-status success">Optimized</span></td>
                </tr>
                <tr>
                  <td><strong>#4</strong></td>
                  <td><strong>Samvidhan Square (RBI Sq)</strong></td>
                  <td>78 sec</td>
                  <td className="text-green font-bold">48 sec</td>
                  <td>128 m</td>
                  <td className="text-green font-bold">82 m</td>
                  <td>+19% veh/h</td>
                  <td><span className="badge-status success">Optimized</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </section>
  );
}

// ==========================================================================
// TAB 5: SUMO COMPONENT
// ==========================================================================
function SumoTab() {
  const [activeCodeFile, setActiveCodeFile] = useState('sumocfg');

  return (
    <section className="tab-panel active">
      <div className="sumo-container">
        <div className="sumo-header glass-panel">
          <div>
            <h2><i className="fa-solid fa-car-side"></i> SUMO Microscopic Traffic Simulation Setup</h2>
            <p>Microscopic traffic simulation setup using OpenStreetMap Nagpur road data, `.net.xml`, `.rou.xml` and Python TraCI control.</p>
          </div>
          <span className="badge-sumo-ver"><i className="fa-solid fa-code-branch"></i> Eclipse SUMO v1.18.0 + TraCI API</span>
        </div>

        <div className="sumo-workflow-grid">
          <div className="workflow-step-card glass-panel">
            <div className="step-badge">1</div>
            <h4>OpenStreetMap (OSM)</h4>
            <p>Extracted high-density 2.4 km corridor bounding box for Sitabuldi/Wardha Road, Nagpur City.</p>
          </div>
          <div className="workflow-step-card glass-panel">
            <div className="step-badge">2</div>
            <h4>.net.xml Network</h4>
            <p>Converted using <code>netconvert</code> to generate lanes, junctions, traffic lights, and edge capacities.</p>
          </div>
          <div className="workflow-step-card glass-panel">
            <div className="step-badge">3</div>
            <h4>.rou.xml Demand</h4>
            <p>Calibrated vehicle trips for 9–12 AM and 4–7 PM peak flow rate using synthetic & sample flow data.</p>
          </div>
          <div className="workflow-step-card glass-panel">
            <div className="step-badge">4</div>
            <h4>TraCI Control</h4>
            <p>Python script connects via socket to modify signal phase duration dynamically based on ML prediction.</p>
          </div>
        </div>

        {/* Code Viewer */}
        <div className="code-viewer-card glass-panel">
          <div className="code-header">
            <h3><i className="fa-solid fa-file-code"></i> SUMO Project File Inspector</h3>
            <div className="code-tabs">
              <button className={`code-tab ${activeCodeFile === 'sumocfg' ? 'active' : ''}`} onClick={() => setActiveCodeFile('sumocfg')}>nagpur_corridor.sumocfg</button>
              <button className={`code-tab ${activeCodeFile === 'traci' ? 'active' : ''}`} onClick={() => setActiveCodeFile('traci')}>traci_adaptive_control.py</button>
              <button className={`code-tab ${activeCodeFile === 'rou' ? 'active' : ''}`} onClick={() => setActiveCodeFile('rou')}>traffic_demand.rou.xml</button>
              <button className={`code-tab ${activeCodeFile === 'net' ? 'active' : ''}`} onClick={() => setActiveCodeFile('net')}>nagpur_network.net.xml</button>
            </div>
          </div>

          <div className="code-body">
            <pre><code>{SUMO_FILES[activeCodeFile]}</code></pre>
          </div>
        </div>

        {/* Vehicle Mix */}
        <div className="vehicle-mix-grid">
          <div className="glass-panel vehicle-card">
            <h4><i className="fa-solid fa-motorcycle text-cyan"></i> 2-Wheelers (45%)</h4>
            <p>High maneuverability, low space requirement. Speed range: 35-50 km/h.</p>
          </div>
          <div className="glass-panel vehicle-card">
            <h4><i className="fa-solid fa-car text-green"></i> Passenger Cars (35%)</h4>
            <p>Standard vehicle unit (1.0 PCU). Speed range: 30-45 km/h.</p>
          </div>
          <div className="glass-panel vehicle-card">
            <h4><i className="fa-solid fa-taxi text-yellow"></i> Auto-Rickshaws (12%)</h4>
            <p>Frequent stopping, medium congestion contribution. Speed range: 25-35 km/h.</p>
          </div>
          <div className="glass-panel vehicle-card">
            <h4><i className="fa-solid fa-bus text-red"></i> Buses & Heavy (8%)</h4>
            <p>High PCU (2.5 PCU), slow acceleration. Speed range: 20-30 km/h.</p>
          </div>
        </div>

      </div>
    </section>
  );
}

// Render React App
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
