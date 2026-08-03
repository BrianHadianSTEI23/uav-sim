import React from 'react';
import { RosProvider, useRos } from './services/RosContext';
import { GpsMap } from './components/GpsMap';
import { TelemetryPanel } from './components/TelemetryPanel';
import './App.css';

const MainDashboard = () => {
  const { isConnected } = useRos();

  return (
    <div className="app-container" style={{ padding: '20px', fontFamily: 'Arial, sans-serif', backgroundColor: '#12121c', minHeight: '100vh', color: '#fff' }}>
      <header style={{ marginBottom: '20px' }}>
        <h1 style={{ margin: 0 }}>UAV Autonomous Telemetry & Ground Control</h1>
        <p style={{ color: '#888', margin: '5px 0 0 0' }}>Module 5.2 - Leaflet GPS & Live Path Visualization Interface</p>
      </header>

      {isConnected ? (
        <>
          <TelemetryPanel />
          <GpsMap />
        </>
      ) : (
        <div style={{ padding: '20px', backgroundColor: '#2a1a1a', color: '#ff6666', borderRadius: '8px' }}>
          Connecting to ROS 2 WebSocket Bridge (ws://localhost:9090)... Ensure Module 5.1 launch file is running.
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