"""
System Configuration & Hyperparameters for OmniAction AI
"""

from pydantic import BaseModel
import torch

class SystemConfig(BaseModel):
    # Device
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Human Detection & MOT
    det_confidence_threshold: float = 0.45
    iou_tracker_threshold: float = 0.30
    max_lost_frames: int = 30
    crop_padding_factor: float = 0.18  # 18% adaptive contextual expansion
    
    # Action Recognition (15-class HAR)
    input_resolution: int = 224
    min_action_confidence: float = 0.50
    
    # Temporal Smoothing & Hysteresis State Machine
    ema_alpha: float = 0.35  # Smoothing factor between 0.1 (very smooth) and 0.9 (instant)
    hysteresis_enter_threshold: float = 0.60
    hysteresis_min_consecutive_frames: int = 4
    
    # Complex Event Processing (Rules)
    fighting_alert_threshold: float = 0.65
    sedentary_alert_seconds: float = 1800.0  # 30 mins
    distraction_ratio_warning: float = 0.40  # If texting/calling > 40% of time
    
    # Streaming & Server
    host: str = "0.0.0.0"
    port: int = 8000
    target_stream_fps: int = 25
    synthetic_stream_width: int = 960
    synthetic_stream_height: int = 540

settings = SystemConfig()
