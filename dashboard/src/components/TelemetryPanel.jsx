import React, { useEffect, useState } from 'react';
import * as ROSLIB from 'roslib';
import { useRos } from '../services/RosContext';

export const TelemetryPanel = () => {
  const { ros, isConnected } = useRos();
  const [alt, setAlt] = useState(0.0);
  const [velocity, setVelocity] = useState({ x: 0.0, y: 0.0, z: 0.0 });

  useEffect(() => {
    // CRITICAL: Block subscription until connected
    if (!isConnected || !ros) return;

    const odomTopic = new ROSLIB.Topic({
      ros: ros,
      name: '/drone/odometry',
      messageType: 'nav_msgs/Odometry'
    });

    odomTopic.subscribe((msg) => {
      setAlt(msg.pose.pose.position.z);
      setVelocity({
        x: msg.twist.twist.linear.x,
        y: msg.twist.twist.linear.y,
        z: msg.twist.twist.linear.z
      });
    });

    return () => odomTopic.unsubscribe();
  }, [isConnected, ros]);

  const totalSpeed = Math.sqrt(velocity.x ** 2 + velocity.y ** 2 + velocity.z ** 2).toFixed(2);

  return (
    <div className="telemetry-card" style={{ padding: '15px', background: '#1e1e2e', color: '#fff', borderRadius: '8px', marginBottom: '15px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>UAV Telemetry Feed</h2>
        <span style={{ color: isConnected ? '#00ff88' : '#ff4444', fontWeight: 'bold' }}>
          ● {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginTop: '10px' }}>
        <div style={{ background: '#2a2a3c', padding: '10px', borderRadius: '6px' }}>
          <small>Altitude (AGL)</small>
          <h3>{alt.toFixed(2)} m</h3>
        </div>
        <div style={{ background: '#2a2a3c', padding: '10px', borderRadius: '6px' }}>
          <small>Ground Speed</small>
          <h3>{totalSpeed} m/s</h3>
        </div>
        <div style={{ background: '#2a2a3c', padding: '10px', borderRadius: '6px' }}>
          <small>Vertical Speed</small>
          <h3>{velocity.z.toFixed(2)} m/s</h3>
        </div>
      </div>
    </div>
  );
};