"""
Temporal Smoothing & Hysteresis State Machine
Prevents frame-by-frame prediction chattering through exponential moving average (EMA)
and state transition thresholds.
"""

from typing import Dict, Any, List, Optional
import time
import numpy as np
from ..models.har_labels import HAR_CLASSES, get_class_info

class TrackTemporalState:
    def __init__(self, track_id: int, initial_probs: Dict[str, float], timestamp: float, alpha: float = 0.35):
        self.track_id = track_id
        self.alpha = alpha
        self.smooth_probs: Dict[str, float] = dict(initial_probs)
        
        # Determine initial top action
        top_act = max(initial_probs.items(), key=lambda x: x[1])[0]
        self.active_action = top_act
        self.active_since = timestamp
        self.last_update = timestamp
        
        # Hysteresis counters
        self.candidate_action = top_act
        self.candidate_count = 1
        
        # Transition history for Gantt timelines: [(start_ts, end_ts, action_name), ...]
        self.timeline_blocks: List[Dict[str, Any]] = []

    def update(
        self, 
        current_probs: Dict[str, float], 
        timestamp: float, 
        enter_threshold: float = 0.55, 
        min_consecutive_frames: int = 4
    ) -> Dict[str, Any]:
        """Applies EMA smoothing and evaluates hysteresis transitions."""
        # Update EMA probabilities
        for cls_name in HAR_CLASSES:
            cur = current_probs.get(cls_name, 0.0)
            prev = self.smooth_probs.get(cls_name, 0.0)
            self.smooth_probs[cls_name] = self.alpha * cur + (1.0 - self.alpha) * prev

        # Identify raw dominant action from smoothed vector
        raw_top_action, raw_top_conf = max(self.smooth_probs.items(), key=lambda x: x[1])
        
        transition_occurred = False
        old_action = self.active_action
        
        if raw_top_action == self.candidate_action:
            self.candidate_count += 1
        else:
            self.candidate_action = raw_top_action
            self.candidate_count = 1

        # Check if candidate qualifies for state transition
        if (
            self.candidate_action != self.active_action
            and self.candidate_count >= min_consecutive_frames
            and raw_top_conf >= enter_threshold
        ):
            # Commit transition
            duration = timestamp - self.active_since
            self.timeline_blocks.append({
                "action": self.active_action,
                "start": self.active_since,
                "end": timestamp,
                "duration_seconds": round(duration, 2)
            })
            if len(self.timeline_blocks) > 50:
                self.timeline_blocks.pop(0)

            old_action = self.active_action
            self.active_action = self.candidate_action
            self.active_since = timestamp
            transition_occurred = True

        self.last_update = timestamp
        current_duration = timestamp - self.active_since

        return {
            "active_action": self.active_action,
            "confidence": round(self.smooth_probs.get(self.active_action, 0.0), 4),
            "smoothed_probabilities": {k: round(v, 4) for k, v in self.smooth_probs.items()},
            "duration_seconds": round(current_duration, 2),
            "transition_occurred": transition_occurred,
            "previous_action": old_action if transition_occurred else None,
            "timeline_blocks": self.timeline_blocks
        }

class TemporalSmoothingEngine:
    def __init__(
        self, 
        alpha: float = 0.35, 
        enter_threshold: float = 0.55, 
        min_consecutive_frames: int = 4
    ):
        self.alpha = alpha
        self.enter_threshold = enter_threshold
        self.min_consecutive_frames = min_consecutive_frames
        self.states: Dict[int, TrackTemporalState] = {}

    def smooth(
        self, 
        track_id: int, 
        raw_probs: Dict[str, float], 
        timestamp: float
    ) -> Dict[str, Any]:
        """Processes raw prediction probabilities for a given track ID and returns stabilized action."""
        if track_id not in self.states:
            self.states[track_id] = TrackTemporalState(track_id, raw_probs, timestamp, self.alpha)

        state = self.states[track_id]
        return state.update(
            raw_probs, 
            timestamp, 
            enter_threshold=self.enter_threshold, 
            min_consecutive_frames=self.min_consecutive_frames
        )

    def cleanup(self, active_track_ids: List[int]):
        """Removes buffers for tracks that have disappeared."""
        active_set = set(active_track_ids)
        stale_ids = [tid for tid in self.states if tid not in active_set]
        for tid in stale_ids:
            del self.states[tid]
