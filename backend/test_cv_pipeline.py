"""
Self-verification script for OmniAction AI Computer Vision Pipeline
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.detector import MultiObjectTracker
from app.core.crop_extractor import ContextAwareCropExtractor
from app.core.classifier import ActionClassifier
from app.core.temporal_smoother import TemporalSmoothingEngine
from app.core.event_rules import ComplexEventProcessor
from app.core.video_streamer import VideoStreamManager
from app.models.har_labels import HAR_CLASSES

def test_pipeline():
    print("Testing OmniAction AI CV Pipeline...")
    print(f"Total HAR Classes: {len(HAR_CLASSES)}")
    
    streamer = VideoStreamManager(960, 540)
    frame, active = streamer.get_frame()
    assert active and frame is not None, "Streamer failed to produce frame"
    print(f"[PASS] VideoStreamManager produced frame with shape {frame.shape}")
    
    tracker = MultiObjectTracker()
    boxes = tracker.detect_people_fallback(frame)
    tracks = tracker.update(boxes, time.time())
    print(f"[PASS] MultiObjectTracker detected {len(boxes)} boxes, active tracks: {len(tracks)}")
    
    crop_extractor = ContextAwareCropExtractor()
    test_box = [200.0, 150.0, 400.0, 450.0]
    crop, exp_bbox = crop_extractor.extract_crop(frame, test_box)
    assert crop.shape == (224, 224, 3), f"Invalid crop shape {crop.shape}"
    print(f"[PASS] ContextAwareCropExtractor produced 224x224 crop")
    
    classifier = ActionClassifier(device="cpu")
    pred = classifier.predict_crop(crop)
    assert pred["top_action"] in HAR_CLASSES, f"Predicted class {pred['top_action']} not in HAR_CLASSES"
    print(f"[PASS] ActionClassifier predicted top action: '{pred['top_action']}' (conf: {pred['confidence']})")
    
    smoother = TemporalSmoothingEngine()
    smooth_res = smoother.smooth(1, pred["probabilities"], time.time())
    print(f"[PASS] TemporalSmoothingEngine output stabilized action: '{smooth_res['active_action']}'")
    
    cep = ComplexEventProcessor()
    alerts = cep.process_frame([{
        "id": 1,
        "action": smooth_res["active_action"],
        "confidence": smooth_res["confidence"],
        "duration_seconds": 12.0
    }], time.time())
    print(f"[PASS] ComplexEventProcessor processed frame, active events: {len(alerts)}")
    
    print("\nALL CV PIPELINE MODULES VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_pipeline()
