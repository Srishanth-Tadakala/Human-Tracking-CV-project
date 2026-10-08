"""
REST API Endpoints for OmniAction AI
Includes single-image diagnostics, video uploads, dataset inspection, and system metrics.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import time
import base64
import os
import shutil
import cv2
import numpy as np

from ..models.har_labels import HAR_CLASSES, HAR_CATEGORIES, CLASS_METADATA, get_class_info
from ..config import settings

router = APIRouter(prefix="/api", tags=["OmniAction API"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "OmniAction AI Vision Engine"
    }

@router.get("/system/stats")
async def get_system_stats(request: Request):
    cep = request.app.state.cep
    tracker = request.app.state.tracker
    metrics = cep.get_summary_metrics()
    
    return {
        "device": settings.device,
        "active_tracks_count": len([t for t in tracker.tracks.values() if t.lost_count == 0]),
        "total_tracks_registered": tracker.next_id - 1,
        "metrics": metrics,
        "config": {
            "fps": settings.target_stream_fps,
            "ema_alpha": settings.ema_alpha,
            "fighting_threshold": settings.fighting_alert_threshold,
            "min_confidence": settings.min_action_confidence
        }
    }

@router.get("/dataset/classes")
async def get_dataset_classes():
    """Returns catalog of all 15 HAR classes with visual descriptions and metadata."""
    return {
        "classes": HAR_CLASSES,
        "categories": HAR_CATEGORIES,
        "metadata": CLASS_METADATA,
        "total_classes": len(HAR_CLASSES)
    }

@router.post("/predict/image")
async def predict_single_image(request: Request, file: UploadFile = File(...)):
    """Runs single-image diagnostic analysis: detection, HAR classification, and Grad-CAM saliency."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Invalid image file format")

    classifier = request.app.state.classifier
    crop_extractor = request.app.state.crop_extractor
    tracker = request.app.state.tracker

    # Detect human region
    detected_boxes = tracker.detect_people_fallback(img_bgr)
    h, w = img_bgr.shape[:2]
    
    if not detected_boxes:
        # Fallback to center 80% crop
        detected_boxes = [[float(w * 0.1), float(h * 0.05), float(w * 0.9), float(h * 0.95)]]

    primary_box = detected_boxes[0]
    crop, exp_bbox = crop_extractor.extract_crop(img_bgr, primary_box)
    
    # Classify
    prediction = classifier.predict_crop(crop)
    
    # Generate Saliency Heatmap
    heatmap_blended = classifier.generate_saliency_heatmap(crop)
    
    # Encode crop and heatmap to Base64
    _, crop_buf = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
    _, heat_buf = cv2.imencode(".jpg", heatmap_blended, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    crop_b64 = base64.b64encode(crop_buf).decode("utf-8")
    heat_b64 = base64.b64encode(heat_buf).decode("utf-8")

    return {
        "success": True,
        "top_action": prediction["top_action"],
        "confidence": prediction["confidence"],
        "top5": prediction["top5"],
        "probabilities": prediction["probabilities"],
        "metadata": prediction["metadata"],
        "detected_bbox": [round(c, 1) for c in primary_box],
        "crop_b64": f"data:image/jpeg;base64,{crop_b64}",
        "heatmap_b64": f"data:image/jpeg;base64,{heat_b64}"
    }

@router.post("/video/upload")
async def upload_video(request: Request, file: UploadFile = File(...)):
    """Uploads a video file and activates it as the active stream source."""
    filename = f"upload_{int(time.time())}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    streamer = request.app.state.streamer
    streamer.set_source("file", file_path)

    return {
        "success": True,
        "message": f"Video {file.filename} loaded successfully.",
        "file_path": file_path
    }

@router.post("/stream/control")
async def control_stream(request: Request, payload: Dict[str, Any]):
    """Adjusts stream source or runtime hyperparameters."""
    streamer = request.app.state.streamer
    source_type = payload.get("source", "synthetic")
    
    if source_type in ["synthetic", "webcam"]:
        streamer.set_source(source_type)
        
    return {
        "success": True,
        "current_source": streamer.current_source
    }
