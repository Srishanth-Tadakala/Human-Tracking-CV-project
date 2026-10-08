/**
 * Live Vision Studio Module
 * Renders high-speed Canvas HUD overlays with glowing bounding boxes,
 * persistent subject tags, and motion trajectory trails.
 */

export class LiveStudio {
  constructor(wsClient, onAlertCallback = () => {}) {
    this.wsClient = wsClient;
    this.onAlert = onAlertCallback;
    this.canvas = document.getElementById('stream-canvas');
    this.ctx = this.canvas.getContext('2d');
    
    // Config state
    this.showBBoxes = true;
    this.showTrails = true;
    this.showGrid = true;
    this.activeSource = 'synthetic';

    this.imgBuffer = new Image();
    this.currentTracks = [];
    this.processedAlertIds = new Set();

    this.initDOM();
  }

  initDOM() {
    // Ingestion Source Buttons
    const btnSynth = document.getElementById('src-btn-synth');
    const btnWebcam = document.getElementById('src-btn-webcam');
    const btnUpload = document.getElementById('src-btn-upload');
    const fileInput = document.getElementById('video-file-input');

    const setBtnActive = (targetBtn, srcName) => {
      [btnSynth, btnWebcam, btnUpload].forEach(b => b.classList.remove('active'));
      targetBtn.classList.add('active');
      this.activeSource = srcName;
      document.getElementById('active-source-name').textContent = `SOURCE: ${srcName.toUpperCase()}`;
    };

    btnSynth.addEventListener('click', () => {
      setBtnActive(btnSynth, 'synthetic');
      this.wsClient.setSource('synthetic');
    });

    btnWebcam.addEventListener('click', () => {
      setBtnActive(btnWebcam, 'webcam');
      this.wsClient.setSource('webcam');
    });

    btnUpload.addEventListener('click', () => {
      fileInput.click();
    });

    fileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('/api/video/upload', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (data.success) {
          setBtnActive(btnUpload, 'uploaded video');
        }
      } catch (err) {
        console.error('Failed to upload video:', err);
      }
    });

    // Sliders
    const sliderEma = document.getElementById('slider-ema');
    const valEma = document.getElementById('val-ema-alpha');
    sliderEma.addEventListener('input', (e) => {
      valEma.textContent = e.target.value;
      this.wsClient.setAlpha(parseFloat(e.target.value));
    });

    const sliderConf = document.getElementById('slider-conf');
    const valConf = document.getElementById('val-conf-min');
    sliderConf.addEventListener('input', (e) => {
      valConf.textContent = e.target.value;
      this.wsClient.setThreshold(parseFloat(e.target.value));
    });

    // Toggles
    const toggleBBoxes = document.getElementById('toggle-bboxes');
    toggleBBoxes.addEventListener('change', (e) => this.showBBoxes = e.target.checked);

    const toggleTrails = document.getElementById('toggle-trails');
    toggleTrails.addEventListener('change', (e) => this.showTrails = e.target.checked);

    const toggleGrid = document.getElementById('toggle-grid');
    const hudGridOverlay = document.getElementById('hud-overlay-grid');
    toggleGrid.addEventListener('change', (e) => {
      this.showGrid = e.target.checked;
      hudGridOverlay.style.display = this.showGrid ? 'block' : 'none';
    });
  }

  handleFramePacket(packet) {
    // 1. Update Header Telemetry
    document.getElementById('header-fps-val').textContent = packet.fps.toFixed(1);
    document.getElementById('header-latency-val').textContent = packet.latency_ms.toFixed(1);
    document.getElementById('metric-active-subjects').textContent = packet.active_tracks_count;

    // 2. Render Frame & Canvas HUD
    if (packet.frame) {
      this.imgBuffer.onload = () => {
        this.ctx.drawImage(this.imgBuffer, 0, 0, this.canvas.width, this.canvas.height);
        if (this.showBBoxes && packet.tracks) {
          this.renderHUDOverlays(packet.tracks);
        }
      };
      this.imgBuffer.src = packet.frame;
    }

    this.currentTracks = packet.tracks || [];
    this.updateSideInspector(this.currentTracks);

    // 3. Process Event Alerts
    if (packet.alerts && packet.alerts.length > 0) {
      for (const alert of packet.alerts) {
        if (!this.processedAlertIds.has(alert.id)) {
          this.processedAlertIds.add(alert.id);
          this.appendAlertCard(alert);
          this.onAlert(alert);
        }
      }
    }
  }

  renderHUDOverlays(tracks) {
    for (const track of tracks) {
      const [x1, y1, x2, y2] = track.bbox;
      const w = Math.max(10, x2 - x1);
      const h = Math.max(10, y2 - y1);
      const color = track.color || '#00f2fe';

      // 1. Draw Motion Trails
      if (this.showTrails && track.history && track.history.length > 1) {
        this.ctx.beginPath();
        for (let i = 0; i < track.history.length; i++) {
          const [hx, hy] = track.history[i];
          if (i === 0) {
            this.ctx.moveTo(hx, hy);
          } else {
            this.ctx.lineTo(hx, hy);
          }
        }
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2;
        this.ctx.shadowColor = color;
        this.ctx.shadowBlur = 8;
        this.ctx.stroke();
        this.ctx.shadowBlur = 0;
      }

      // 2. Draw Bounding Box (Rounded Corners)
      this.ctx.save();
      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 2.5;
      this.ctx.shadowColor = color;
      this.ctx.shadowBlur = 10;
      this.drawRoundedRect(this.ctx, x1, y1, w, h, 6);
      this.ctx.stroke();

      // Corner Accents
      const cornerLen = Math.min(14, w * 0.2);
      this.ctx.lineWidth = 4;
      this.drawCornerAccents(this.ctx, x1, y1, w, h, cornerLen);
      this.ctx.restore();

      // 3. Overhead Label Tag
      const tagText = `ID #${track.id} • ${track.action.toUpperCase()} (${Math.round(track.confidence * 100)}%)`;
      this.ctx.font = '600 12px "JetBrains Mono", monospace';
      const textMetrics = this.ctx.measureText(tagText);
      const tagWidth = textMetrics.width + 16;
      const tagHeight = 22;
      const tagY = Math.max(8, y1 - tagHeight - 6);

      // Tag Background
      this.ctx.fillStyle = 'rgba(6, 8, 13, 0.88)';
      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 1;
      this.drawRoundedRect(this.ctx, x1, tagY, tagWidth, tagHeight, 4);
      this.ctx.fill();
      this.ctx.stroke();

      // Tag Text
      this.ctx.fillStyle = color;
      this.ctx.fillText(tagText, x1 + 8, tagY + 15);
    }
  }

  drawRoundedRect(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
  }

  drawCornerAccents(ctx, x, y, w, h, len) {
    ctx.beginPath();
    // Top-left
    ctx.moveTo(x, y + len); ctx.lineTo(x, y); ctx.lineTo(x + len, y);
    // Top-right
    ctx.moveTo(x + w - len, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + len);
    // Bottom-right
    ctx.moveTo(x + w, y + h - len); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w - len, y + h);
    // Bottom-left
    ctx.moveTo(x + len, y + h); ctx.lineTo(x, y + h); ctx.lineTo(x, y + h - len);
    ctx.stroke();
  }

  updateSideInspector(tracks) {
    const container = document.getElementById('active-subjects-list');
    document.getElementById('subject-count-tag').textContent = `${tracks.length} Active`;

    if (tracks.length === 0) {
      container.innerHTML = '<div style="font-size: 0.78rem; color: var(--text-muted); text-align: center; padding: 2rem 0;">No subjects currently in frame.</div>';
      return;
    }

    container.innerHTML = tracks.map(track => {
      const confPct = Math.round(track.confidence * 100);
      const color = track.color || '#00f2fe';
      const duration = Math.round(track.duration_seconds || 0);

      return `
        <div class="subject-item-card" style="border-left: 3px solid ${color};">
          <div class="subject-header-row">
            <span class="subject-id-badge">SUBJECT #${track.id}</span>
            <span class="subject-action-badge" style="background: ${color}22; color: ${color}; border: 1px solid ${color}44;">
              ${track.action.replace('_', ' ')}
            </span>
          </div>
          <div class="subject-meta-row">
            <span>Confidence: <strong>${confPct}%</strong></span>
            <span>Duration: <strong>${duration}s</strong></span>
          </div>
          <div class="subject-prob-bar-wrap">
            <div class="subject-prob-bar" style="width: ${confPct}%; background: ${color};"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  appendAlertCard(alert) {
    const container = document.getElementById('studio-alerts-container');
    const emptyNotice = container.querySelector('div[style*="Systems Nominal"]');
    if (emptyNotice) {
      emptyNotice.remove();
    }

    const timeStr = new Date(alert.timestamp * 1000).toLocaleTimeString();
    const item = document.createElement('div');
    item.className = `audit-event-item ${alert.level}`;
    item.innerHTML = `
      <div class="audit-time">${timeStr}</div>
      <div class="audit-content">
        <div class="audit-title">${alert.title}</div>
        <div class="audit-desc">${alert.message}</div>
      </div>
    `;

    container.insertBefore(item, container.firstChild);
    while (container.children.length > 20) {
      container.removeChild(container.lastChild);
    }

    const countPill = document.getElementById('alert-count-pill');
    countPill.textContent = `${container.children.length} Events`;
  }
}
