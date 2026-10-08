"""
FastAPI Application Entry Point for OmniAction AI
Initializes the Computer Vision subsystem and attaches singleton state.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from .config import settings
from .core.detector import MultiObjectTracker
from .core.crop_extractor import ContextAwareCropExtractor
from .core.classifier import ActionClassifier
from .core.temporal_smoother import TemporalSmoothingEngine
from .core.event_rules import ComplexEventProcessor
from .core.video_streamer import VideoStreamManager
from .api.routes import router as api_router
from .api.websocket import websocket_endpoint

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("  [START] Initializing OmniAction AI Computer Vision Engine")
    print(f"  * Execution Device: {settings.device}")
    print(f"  * Detection Threshold: {settings.det_confidence_threshold}")
    print(f"  * Target Stream FPS: {settings.target_stream_fps}")
    print("=" * 60)

    # Instantiate core singletons
    app.state.tracker = MultiObjectTracker(
        iou_threshold=settings.iou_tracker_threshold,
        max_lost_frames=settings.max_lost_frames
    )
    app.state.crop_extractor = ContextAwareCropExtractor(
        target_resolution=settings.input_resolution,
        padding_factor=settings.crop_padding_factor
    )
    app.state.classifier = ActionClassifier(device=settings.device)
    app.state.smoother = TemporalSmoothingEngine(
        alpha=settings.ema_alpha,
        enter_threshold=settings.hysteresis_enter_threshold,
        min_consecutive_frames=settings.hysteresis_min_consecutive_frames
    )
    app.state.cep = ComplexEventProcessor(
        fighting_threshold=settings.fighting_alert_threshold,
        sedentary_threshold_sec=settings.sedentary_alert_seconds
    )
    app.state.streamer = VideoStreamManager(
        width=settings.synthetic_stream_width,
        height=settings.synthetic_stream_height
    )
    
    yield
    
    print("[OmniAction] Shutting down video streamer and releasing resources...")
    app.state.streamer.release()

app = FastAPI(
    title="OmniAction AI Vision Engine",
    description="Spatial-Temporal Human Behavior Telemetry & HAR Inference API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.include_router(api_router)

# Mount WebSocket endpoint
app.add_api_websocket_route("/ws/stream", websocket_endpoint)
