/**
 * OmniAction AI Main Controller Entrypoint
 * Bootstraps WebSocket stream, orchestrates view panels, and manages notification toasts.
 */

import { StreamWebSocketClient } from './modules/wsClient.js';
import { LiveStudio } from './modules/liveStudio.js';
import { TelemetryView } from './modules/telemetryView.js';
import { DiagnosticView } from './modules/diagnosticView.js';
import { DatasetView } from './modules/datasetView.js';

class OmniActionApp {
  constructor() {
    this.toastContainer = document.getElementById('toast-container');
    this.initToasts();
    this.initNavTabs();
    this.bootstrapSubsystems();
  }

  showToast(title, message, level = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${level}`;
    
    const iconMap = {
      critical: '🚨',
      warning: '⚠️',
      success: '✅',
      info: 'ℹ️'
    };
    
    toast.innerHTML = `
      <div style="font-size: 1.1rem;">${iconMap[level] || 'ℹ️'}</div>
      <div>
        <div style="font-weight: 700; font-size: 0.85rem; margin-bottom: 0.15rem;">${title}</div>
        <div style="font-size: 0.78rem; color: var(--text-secondary);">${message}</div>
      </div>
    `;

    this.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4500);
  }

  initToasts() {
    // Welcome Notification
    setTimeout(() => {
      this.showToast('OmniAction AI Initialized', '15-Class Spatial-Temporal Vision Engine connected.', 'success');
    }, 800);
  }

  initNavTabs() {
    const navButtons = document.querySelectorAll('.nav-tab-btn');
    const viewPanels = document.querySelectorAll('.view-panel');

    navButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetViewId = btn.getAttribute('data-view');

        // Toggle active button
        navButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Toggle active view panel
        viewPanels.forEach(panel => {
          if (panel.id === targetViewId) {
            panel.classList.add('active');
          } else {
            panel.classList.remove('active');
          }
        });
      });
    });
  }

  bootstrapSubsystems() {
    // 1. Initialize Views
    this.telemetryView = new TelemetryView();
    this.diagnosticView = new DiagnosticView((title, msg, lvl) => this.showToast(title, msg, lvl));
    this.datasetView = new DatasetView();

    // 2. Initialize WebSocket Client
    const wsStatusText = document.getElementById('ws-status-text');
    const wsPulseDot = document.getElementById('ws-pulse-dot');

    this.wsClient = new StreamWebSocketClient({
      onStatusChange: (connected) => {
        if (connected) {
          wsStatusText.textContent = 'WS: CONNECTED';
          wsPulseDot.classList.remove('disconnected');
        } else {
          wsStatusText.textContent = 'WS: RECONNECTING';
          wsPulseDot.classList.add('disconnected');
        }
      },
      onFrame: (packet) => {
        // Feed frame to Live Studio
        this.liveStudio.handleFramePacket(packet);

        // Feed telemetry to Telemetry View
        this.telemetryView.updateFromPacket(packet);

        // Update Dominant Action in top metric bar
        if (packet.tracks && packet.tracks.length > 0) {
          const dom = packet.tracks[0].action;
          document.getElementById('metric-dominant-action').textContent = dom.replace('_', ' ');
        }
      }
    });

    // 3. Initialize Live Studio with Alert Forwarder
    this.liveStudio = new LiveStudio(this.wsClient, (alert) => {
      this.showToast(alert.title, alert.message, alert.level);
    });

    // 4. Connect Stream
    this.wsClient.connect();
  }
}

// Bootstrap on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.__omniApp = new OmniActionApp();
});
