import React from 'react';
import { RosProvider, useRos } from './services/RosContext';
import { GpsMap } from './components/GpsMap';
import { TelemetryPanel } from './components/TelemetryPanel';
import { PointCloudViewer } from './components/PointCloudViewer';
import './App.css';

const MainDashboard = () => {
  const { isConnected } = useRos();

  return (
    <div style={{ padding: '20px', fontFamily: 'Inter, sans-serif', backgroundColor: '#0d1117', minHeight: '100vh', color: '#c9d1d9' }}>
      <header style={{ marginBottom: '20px', borderBottom: '1px solid #30363d', paddingBottom: '10px' }}>
        <h1 style={{ margin: 0, color: '#f0f6fc' }}>UAV Autonomous Telemetry & Ground Control</h1>
        <p style={{ color: '#8b949e', margin: '5px 0 0 0' }}>Module 5.3 - Live WebGL 3D SLAM & Spatial Visualization</p>
      </header>

      {isConnected ? (
        <>
          <TelemetryPanel />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <GpsMap />
            <PointCloudViewer />
          </div>
        </>
      ) : (
        <div style={{ padding: '20px', backgroundColor: '#2d1517', color: '#f85149', borderRadius: '8px', border: '1px solid #8b0000' }}>
          Connecting to ROS 2 WebSocket Bridge (ws://localhost:9090)... Ensure <code>web_bridge.launch.py</code> is running.
        </div>
      )}
    </div>
  );
};

function App() {
  return (
    <RosProvider>
      <MainDashboard />
    </RosProvider>
  );
}

export default App;