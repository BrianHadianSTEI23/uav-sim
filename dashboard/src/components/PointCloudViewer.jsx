import React, { useEffect, useRef, useState } from 'react';
import * as ROS3D from 'ros3d';
import * as ROSLIB from 'roslib';
import { useRos } from '../services/RosContext';
import './PointCloudViewer.css';

export const PointCloudViewer = () => {
  const { ros, isConnected } = useRos();
  const containerRef = useRef(null);
  const viewerRef = useRef(null);
  const [pointSize, setPointSize] = useState(0.05);

  useEffect(() => {
    // CRITICAL: Ensure WebSocket is connected and DOM element exists
    if (!isConnected || !ros || !containerRef.current) return;

    // Prevent duplicate viewer instantiation
    if (viewerRef.current) return;

    const width = containerRef.current.clientWidth || 800;
    const height = 500;

    // 1. Initialize ROS3D Viewer Canvas
    const viewer = new ROS3D.Viewer({
      divID: containerRef.current.id,
      width: width,
      height: height,
      antialias: true,
      background: '#0d1117',
      cameraPosition: { x: 5, y: 5, z: 8 }
    });

    viewerRef.current = viewer;

    // 2. Add Ground Grid Reference Frame
    const grid = new ROS3D.Grid({
      num_cells: 20,
      color: '#21262d',
      lineWidth: 1.5
    });
    viewer.scene.add(grid);

    // 3. Initialize TF Client for spatial transforms
    const tfClient = new ROSLIB.TFClient({
      ros: ros,
      fixedFrame: 'map',
      angularThres: 0.01,
      transThres: 0.01,
      rate: 15.0
    });

    // 4. Stream Live SLAM Point Cloud (sensor_msgs/PointCloud2)
    const pointCloudClient = new ROS3D.PointCloud2({
      ros: ros,
      tfClient: tfClient,
      topic: '/drone/lidar/points',
      fixedFrame: 'map',
      max_pts: 50000,
      material: {
        size: pointSize,
        color: 0x00ffcc
      }
    });
    console.log(pointCloudClient.buffer)

    // 5. Display Active Target Waypoint Marker
    const targetMarkerClient = new ROS3D.MarkerClient({
      ros: ros,
      tfClient: tfClient,
      topic: '/drone/target_waypoint_marker',
      path: 'http://resources.robotwebtools.org/'
    });

    // Handle Window Resize
    const handleResize = () => {
      if (viewerRef.current && containerRef.current) {
        const newWidth = containerRef.current.clientWidth;
        viewerRef.current.resize(newWidth, height);
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
      viewerRef.current = null;
    };
  }, [isConnected, ros]);

  return (
    <div className="pointcloud-card">
      <div className="pointcloud-header">
        <h3>3D SLAM Point Cloud & Spatial Viewport</h3>
        <div className="pointcloud-controls">
          <label>Point Size: </label>
          <input
            type="range"
            min="0.01"
            max="0.2"
            step="0.01"
            value={pointSize}
            onChange={(e) => setPointSize(parseFloat(e.target.value))}
          />
          <span>{pointSize.toFixed(2)}m</span>
        </div>
      </div>
      
      <div
        id="ros3d-canvas-container"
        ref={containerRef}
        className="ros3d-viewport"
      />
    </div>
  );
};