/**
 * WebSocket Streaming Client for OmniAction AI
 * Handles low-latency frame streaming, reconnection, and control commands.
 */

export class StreamWebSocketClient {
  constructor(options = {}) {
    this.url = options.url || this.getDefaultUrl();
    this.onFrameCallback = options.onFrame || (() => {});
    this.onStatusChange = options.onStatusChange || (() => {});
    this.ws = null;
    this.reconnectTimer = null;
    this.isConnected = false;
    this.lastLatency = 0;
  }

  getDefaultUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // In Vite dev mode, route through Vite proxy /ws/stream or directly to 8000
    const host = window.location.port === '5173' ? '127.0.0.1:8000' : window.location.host;
    return `${protocol}//${host}/ws/stream`;
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.ws = new WebSocket(this.url);
    } catch (err) {
      console.warn('[StreamWS] Connection creation failed:', err);
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.isConnected = true;
      this.onStatusChange(true);
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        this.onFrameCallback(payload);
      } catch (err) {
        console.error('[StreamWS] Failed to parse message:', err);
      }
    };

    this.ws.onerror = (err) => {
      console.warn('[StreamWS] Socket error encountered:', err);
    };

    this.ws.onclose = () => {
      this.isConnected = false;
      this.onStatusChange(false);
      this.scheduleReconnect();
    };
  }

  scheduleReconnect() {
    if (!this.reconnectTimer) {
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, 2000);
    }
  }

  sendCommand(cmdObj) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(cmdObj));
    }
  }

  setSource(sourceType) {
    this.sendCommand({ command: 'set_source', source: sourceType });
  }

  setAlpha(alphaVal) {
    this.sendCommand({ command: 'set_alpha', alpha: alphaVal });
  }

  setThreshold(threshVal) {
    this.sendCommand({ command: 'set_threshold', threshold: threshVal });
  }
}
