import * as ROSLIB from 'roslib';

class RosbridgeService {
  constructor() {
    this.ros = new ROSLIB.Ros();
    this.isConnected = false;
    this.isConnecting = false;

    this.ros.on('connection', () => {
      this.isConnected = true;
      this.isConnecting = false;
      console.log('[ROSBRIDGE] Connected successfully.');
    });

    this.ros.on('error', (err) => {
      this.isConnected = false;
      this.isConnecting = false;
      console.error('[ROSBRIDGE] Connection error:', err);
    });

    this.ros.on('close', () => {
      this.isConnected = false;
      this.isConnecting = false;
      console.log('[ROSBRIDGE] Connection closed.');
    });
  }

  connect(url = 'ws://localhost:9090') {
    // 1. Return immediately if already connected
    if (this.isConnected) {
      return Promise.resolve(true);
    }

    // 2. Prevent duplicate socket connections if a connection is currently pending
    if (this.isConnecting) {
      return new Promise((resolve, reject) => {
        this.ros.once('connection', () => resolve(true));
        this.ros.once('error', (err) => reject(err));
      });
    }

    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      const onConnect = () => {
        cleanup();
        resolve(true);
      };

      const onError = (err) => {
        cleanup();
        reject(err);
      };

      const cleanup = () => {
        this.ros.off('connection', onConnect);
        this.ros.off('error', onError);
      };

      this.ros.once('connection', onConnect);
      this.ros.once('error', onError);

      // Initiates single connection
      this.ros.connect(url);
    });
  }

  getRos() {
    return this.ros;
  }
}

// Export a true singleton instance
const rosService = new RosbridgeService();
export default rosService;