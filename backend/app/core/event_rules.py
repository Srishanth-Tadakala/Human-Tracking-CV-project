"""
Complex Event Processing (CEP) & Behavioral Business Rules Engine
Evaluates real-time health, security, and productivity telemetry.
"""

from typing import List, Dict, Any, Optional
import time

class ComplexEventProcessor:
    def __init__(
        self, 
        fighting_threshold: float = 0.65, 
        sedentary_threshold_sec: float = 60.0  # 60s for demo responsiveness
    ):
        self.fighting_threshold = fighting_threshold
        self.sedentary_threshold_sec = sedentary_threshold_sec
        self.events_log: List[Dict[str, Any]] = []
        self.drinking_counters: Dict[int, int] = {}
        self.cumulative_activity_sec: Dict[str, float] = {}

    def process_frame(
        self, 
        tracks_telemetry: List[Dict[str, Any]], 
        timestamp: float
    ) -> List[Dict[str, Any]]:
        """Evaluates rules across all active tracks and returns newly triggered alerts."""
        new_alerts = []

        for track in tracks_telemetry:
            tid = track["id"]
            action = track["action"]
            conf = track["confidence"]
            duration = track.get("duration_seconds", 0.0)
            transition_occurred = track.get("transition_occurred", False)

            # Update global activity accumulator
            self.cumulative_activity_sec[action] = self.cumulative_activity_sec.get(action, 0.0) + 0.04

            # Rule 1: Physical Altercation Alert (Fighting)
            if action == "fighting" and conf >= self.fighting_threshold:
                alert = {
                    "id": f"alert_fight_{tid}_{int(timestamp*1000)}",
                    "timestamp": timestamp,
                    "level": "critical",
                    "title": "Security Alert: Altercation Detected",
                    "message": f"Subject #{tid} flagged for aggressive physical interaction ({int(conf*100)}% conf).",
                    "track_id": tid,
                    "action": "fighting"
                }
                new_alerts.append(alert)
                self.events_log.insert(0, alert)

            # Rule 2: Prolonged Sedentary Warning
            if action in ["sitting", "using_laptop"] and duration >= self.sedentary_threshold_sec:
                # Trigger warning every 60s interval
                if int(duration) % 30 == 0:
                    alert = {
                        "id": f"alert_sedentary_{tid}_{int(timestamp)}",
                        "timestamp": timestamp,
                        "level": "warning",
                        "title": "Ergonomic Alert: Sedentary Posture",
                        "message": f"Subject #{tid} has been seated continuously for {int(duration)}s without a stretch break.",
                        "track_id": tid,
                        "action": action
                    }
                    new_alerts.append(alert)
                    self.events_log.insert(0, alert)

            # Rule 3: Hydration Event Trigger
            if transition_occurred and track.get("previous_action") == "drinking":
                count = self.drinking_counters.get(tid, 0) + 1
                self.drinking_counters[tid] = count
                event = {
                    "id": f"event_hydration_{tid}_{int(timestamp*1000)}",
                    "timestamp": timestamp,
                    "level": "success",
                    "title": "Wellness Event: Hydration Logged",
                    "message": f"Subject #{tid} completed hydration sequence (Log #{count} today).",
                    "track_id": tid,
                    "action": "drinking"
                }
                new_alerts.append(event)
                self.events_log.insert(0, event)

            # Rule 4: Action Transition Audit Log
            if transition_occurred:
                prev = track.get("previous_action", "unknown")
                event = {
                    "id": f"event_trans_{tid}_{int(timestamp*1000)}",
                    "timestamp": timestamp,
                    "level": "info",
                    "title": "Action State Transition",
                    "message": f"Subject #{tid} transitioned from [{prev}] to [{action}].",
                    "track_id": tid,
                    "action": action
                }
                self.events_log.insert(0, event)

        # Cap in-memory log
        if len(self.events_log) > 100:
            self.events_log = self.events_log[:100]

        return new_alerts

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Calculates global ergonomic and productivity metrics."""
        focus_sec = self.cumulative_activity_sec.get("using_laptop", 0.0) + self.cumulative_activity_sec.get("sitting", 0.0)
        distract_sec = self.cumulative_activity_sec.get("texting", 0.0) + self.cumulative_activity_sec.get("calling", 0.0)
        total_tracked = max(1.0, focus_sec + distract_sec)
        
        focus_score = round(min(100.0, (focus_sec / total_tracked) * 100.0), 1)
        
        return {
            "focus_score_percent": focus_score,
            "total_hydration_events": sum(self.drinking_counters.values()),
            "cumulative_activity_distribution": {k: round(v, 1) for k, v in self.cumulative_activity_sec.items()},
            "recent_events": self.events_log[:15]
        }
