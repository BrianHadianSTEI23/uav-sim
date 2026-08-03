import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import * as ROSLIB from 'roslib';
import { useRos } from '../services/RosContext';
import 'leaflet/dist/leaflet.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const createDroneIcon = (headingDeg) => {
  return L.divIcon({
    className: 'drone-custom-marker',
    html: `<div style="transform: rotate(${headingDeg}deg); transition: transform 0.1s linear; font-size: 28px; text-align: center;">🚁</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16]
  });
};

const MapRecenter = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center && center[0] !== 0) {
      map.setView(center, map.getZoom(), { animate: true });
    }
  }, [center, map]);
  return null;
};

export const GpsMap = () => {
  const { ros, isConnected } = useRos();
  const [dronePos, setDronePos] = useState([-6.1754, 106.8272]);
  const [heading, setHeading] = useState(0);
  const [flightHistory, setFlightHistory] = useState([]);
  const [plannedPath, setPlannedPath] = useState([]);

  useEffect(() => {
    // CRITICAL: Block subscription calls until WebSocket connection is fully established
    if (!isConnected || !ros) return;

    const gpsTopic = new ROSLIB.Topic({
      ros: ros,
      name: '/drone/gps/fix',
      messageType: 'sensor_msgs/NavSatFix'
    });

    const odomTopic = new ROSLIB.Topic({
      ros: ros,
      name: '/drone/odometry',
      messageType: 'nav_msgs/Odometry'
    });

    const pathTopic = new ROSLIB.Topic({
      ros: ros,
      name: '/drone/planned_path',
      messageType: 'nav_msgs/Path'
    });

    gpsTopic.subscribe((msg) => {
      if (msg.latitude && msg.longitude) {
        const newCoords = [msg.latitude, msg.longitude];
        setDronePos(newCoords);
        setFlightHistory((prev) => [...prev.slice(-200), newCoords]);
      }
    });

    odomTopic.subscribe((msg) => {
      const q = msg.pose.pose.orientation;
      const siny_cosp = 2.0 * (q.w * q.z + q.x * q.y);
      const cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z);
      const yawDeg = Math.atan2(siny_cosp, cosy_cosp) * (180 / Math.PI);
      setHeading(yawDeg);
    });

    pathTopic.subscribe((msg) => {
      const pathPoints = msg.poses.map((p) => {
        const latOffset = p.pose.position.y / 111111.0;
        const lonOffset = p.pose.position.x / (111111.0 * Math.cos(dronePos[0] * Math.PI / 180));
        return [dronePos[0] + latOffset, dronePos[1] + lonOffset];
      });
      setPlannedPath(pathPoints);
    });

    return () => {
      gpsTopic.unsubscribe();
      odomTopic.unsubscribe();
      pathTopic.unsubscribe();
    };
  }, [isConnected, ros, dronePos]);

  return (
    <div className="map-container" style={{ height: '500px', width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
      <MapContainer center={dronePos} zoom={18} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapRecenter center={dronePos} />
        <Polyline positions={flightHistory} color="#00ffcc" weight={4} opacity={0.8} />
        <Polyline positions={plannedPath} color="#ff9900" weight={3} dashArray="5, 10" />
        <Marker position={dronePos} icon={createDroneIcon(heading)}>
          <Popup>
            <div>
              <strong>UAV Status</strong><br />
              Lat: {dronePos[0].toFixed(6)}<br />
              Lon: {dronePos[1].toFixed(6)}<br />
              Heading: {heading.toFixed(1)}°
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
};