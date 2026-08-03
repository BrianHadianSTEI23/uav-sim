import React, { createContext, useContext, useEffect, useState } from 'react';
import rosService from './rosbridge';

const RosContext = createContext({ ros: null, isConnected: false });

export const RosProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(rosService.isConnected);
  const ros = rosService.getRos();

  useEffect(() => {
    let isMounted = true;

    const handleConnect = () => {
      if (isMounted) setIsConnected(true);
    };

    const handleClose = () => {
      if (isMounted) setIsConnected(false);
    };

    const handleError = () => {
      if (isMounted) setIsConnected(false);
    };

    ros.on('connection', handleConnect);
    ros.on('close', handleClose);
    ros.on('error', handleError);

    // Initial connection call
    if (!rosService.isConnected && !rosService.isConnecting) {
      rosService.connect('ws://localhost:9090').catch((err) => {
        console.warn('[ROS Context] Connection failed:', err);
      });
    }

    return () => {
      isMounted = false;
      ros.off('connection', handleConnect);
      ros.off('close', handleClose);
      ros.off('error', handleError);
    };
  }, [ros]);

  return (
    <RosContext.Provider value={{ ros, isConnected }}>
      {children}
    </RosContext.Provider>
  );
};

export const useRos = () => useContext(RosContext);