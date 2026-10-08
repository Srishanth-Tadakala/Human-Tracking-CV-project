/**
 * Behavioral Telemetry & Gantt Timeline Module
 * Visualizes temporal activity transitions, focus metrics, and cumulative distributions.
 */

export class TelemetryView {
  constructor() {
    this.ganttContainer = document.getElementById('gantt-chart-wrapper');
    this.activityBarsContainer = document.getElementById('activity-breakdown-bars');
    this.fullAuditStream = document.getElementById('full-audit-stream');
    this.gaugeCircle = document.getElementById('gauge-progress-circle');
    this.gaugeScoreText = document.getElementById('gauge-score-value');

    this.focusTimeText = document.getElementById('focus-time-text');
    this.distractTimeText = document.getElementById('distract-time-text');

    // In-memory track history for Gantt visualization
    this.tracksHistory = new Map();
    this.activityTimeMap = new Map();
    this.processedAuditIds = new Set();
  }

  updateFromPacket(packet) {
    if (!packet.tracks) return;

    // 1. Accumulate timeline data for each track
    for (const track of packet.tracks) {
      if (!this.tracksHistory.has(track.id)) {
        this.tracksHistory.set(track.id, {
          id: track.id,
          currentAction: track.action,
          currentColor: track.color,
          blocks: []
        });
      }

      const history = this.tracksHistory.get(track.id);
      history.currentAction = track.action;
      history.currentColor = track.color;

      // Accumulate activity time
      const curTotal = this.activityTimeMap.get(track.action) || 0;
      this.activityTimeMap.set(track.action, curTotal + 0.04);
    }

    // 2. Render Gantt Timeline
    this.renderGanttChart(packet.tracks);

    // 3. Render Activity Bars & Calculate Focus
    this.renderActivityBreakdown();

    // 4. Update Audit Log
    if (packet.alerts && packet.alerts.length > 0) {
      for (const alert of packet.alerts) {
        if (!this.processedAuditIds.has(alert.id)) {
          this.processedAuditIds.add(alert.id);
          this.appendAuditEntry(alert);
        }
      }
    }
  }

  renderGanttChart(activeTracks) {
    if (this.tracksHistory.size === 0) {
      this.ganttContainer.innerHTML = '<div style="font-size: 0.8rem; color: var(--text-muted); text-align: center; padding: 2rem 0;">Awaiting telemetry data...</div>';
      return;
    }

    let html = '';
    for (const [tid, hist] of this.tracksHistory.entries()) {
      // Find current active track
      const active = activeTracks.find(t => t.id === tid);
      const currentDur = active ? Math.round(active.duration_seconds || 0) : 0;
      const curAction = active ? active.action : hist.currentAction;
      const curColor = active ? (active.color || '#00f2fe') : hist.currentColor;

      html += `
        <div class="gantt-track-row">
          <div class="gantt-subject-label">
            <span class="pulse-dot" style="background: ${curColor}; box-shadow: 0 0 6px ${curColor};"></span>
            SUB #${tid}
          </div>
          <div class="gantt-bar-track">
            <!-- Simulated historical segments -->
            <div class="gantt-block" style="width: 25%; background: rgba(16, 185, 129, 0.75);">
              sitting (15s)
            </div>
            <div class="gantt-block" style="width: 20%; background: rgba(20, 184, 166, 0.75);">
              drinking (5s)
            </div>
            <div class="gantt-block" style="width: 15%; background: rgba(245, 158, 11, 0.75);">
              texting (10s)
            </div>
            <!-- Active running segment -->
            <div class="gantt-block" style="flex: 1; background: ${curColor}; color: #06080d; font-weight: 700;">
              ${curAction.replace('_', ' ')} (Active: ${currentDur}s)
            </div>
          </div>
        </div>
      `;
    }

    this.ganttContainer.innerHTML = html;
  }

  renderActivityBreakdown() {
    let totalSec = 0;
    for (const [act, sec] of this.activityTimeMap.entries()) {
      totalSec += sec;
    }
    if (totalSec <= 0) return;

    // Focus vs Distraction Calculation
    const focusSec = (this.activityTimeMap.get('using_laptop') || 0) + (this.activityTimeMap.get('sitting') || 0);
    const distractSec = (this.activityTimeMap.get('texting') || 0) + (this.activityTimeMap.get('calling') || 0);
    const focusRatio = Math.min(100, Math.round((focusSec / Math.max(1, focusSec + distractSec)) * 100));

    // Update Circular Gauge
    // Circumference = 2 * PI * 45 ≈ 283
    const offset = 283 - (283 * focusRatio) / 100;
    this.gaugeCircle.style.strokeDashoffset = offset;
    this.gaugeScoreText.textContent = `${focusRatio}%`;
    document.getElementById('metric-focus-score').textContent = focusRatio;

    this.focusTimeText.textContent = `${Math.floor(focusSec / 60)}m ${Math.round(focusSec % 60)}s`;
    this.distractTimeText.textContent = `${Math.floor(distractSec / 60)}m ${Math.round(distractSec % 60)}s`;

    // Sort Top 4 Activities
    const sorted = Array.from(this.activityTimeMap.entries()).sort((a, b) => b[1] - a[1]).slice(0, 5);

    let barsHtml = '';
    const colors = ['#10b981', '#38bdf8', '#f59e0b', '#14b8a6', '#ef4444'];
    sorted.forEach(([act, sec], idx) => {
      const pct = Math.round((sec / totalSec) * 100);
      const col = colors[idx % colors.length];
      barsHtml += `
        <div class="activity-bar-row">
          <div class="activity-bar-meta">
            <span style="text-transform: capitalize;">${act.replace('_', ' ')}</span>
            <span><strong>${pct}%</strong> (${Math.round(sec)}s)</span>
          </div>
          <div class="activity-bar-outer">
            <div class="activity-bar-inner" style="width: ${pct}%; background: ${col};"></div>
          </div>
        </div>
      `;
    });

    this.activityBarsContainer.innerHTML = barsHtml;
  }

  appendAuditEntry(alert) {
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

    this.fullAuditStream.insertBefore(item, this.fullAuditStream.firstChild);
    while (this.fullAuditStream.children.length > 30) {
      this.fullAuditStream.removeChild(this.fullAuditStream.lastChild);
    }
  }
}
