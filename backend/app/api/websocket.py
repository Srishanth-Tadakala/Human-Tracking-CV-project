"""
Real-Time WebSocket Streaming Endpoint
Delivers low-latency video frames along with synchronized bounding boxes, 
action predictions, and complex event alerts.
"""

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import time
import json
import base64
import cv2
import numpy as np

from ..models.har_labels import get_class_info

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app = websocket.app
    tracker = app.state.tracker
    crop_extractor = app.state.crop_extractor
    classifier = app.state.classifier
    smoother = app.state.smoother
    cep = app.state.cep
    streamer = app.state.streamer

    frame_count = 0
    start_time = time.time()
    last_fps_time = time.time()
    current_fps = 30.0

    async def receive_commands():
        """Listens for client control messages without blocking stream."""
        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                cmd = msg.get("command")
                if cmd == "set_source":
                    src = msg.get("source", "synthetic")
                    streamer.set_source(src)
                elif cmd == "set_alpha":
                    alpha = float(msg.get("alpha", 0.35))
                    smoother.alpha = alpha
                elif cmd == "set_threshold":
                    thresh = float(msg.get("threshold", 0.50))
                    smoother.enter_threshold = thresh
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"[WebSocket] Command receiver error: {e}")

    receiver_task = asyncio.create_task(receive_commands())

    try:
        while True:
            t_loop_start = time.time()
            
            # 1. Fetch next video frame
            frame_bgr, active = streamer.get_frame()
            if not active or frame_bgr is None:
                await asyncio.sleep(0.04)
                continue

            frame_count += 1
            now = time.time()
            
            # FPS tracking
            if now - last_fps_time >= 1.0:
                current_fps = round(frame_count / (now - start_time), 1)
                last_fps_time = now

            # 2. Detect and track subjects
            detected_boxes = tracker.detect_people_fallback(frame_bgr)
            tracked_subjects = tracker.update(detected_boxes, now)

            # 3. Process crops & run HAR inference
            tracks_payload = []
            crops_to_classify = []
            crops_tracks = []

            for subject in tracked_subjects:
                crop, exp_bbox = crop_extractor.extract_crop(frame_bgr, subject.bbox)
                crops_to_classify.append(crop)
                crops_tracks.append((subject, exp_bbox))

            if crops_to_classify:
                raw_predictions = classifier.predict_batch(crops_to_classify)
                
                for (subject, exp_bbox), pred in zip(crops_tracks, raw_predictions):
                    # 4. Temporal smoothing & state machine
                    smooth_res = smoother.smooth(subject.id, pred["probabilities"], now)
                    action_name = smooth_res["active_action"]
                    action_meta = get_class_info(action_name)
                    
                    track_dict = subject.to_dict()
                    track_dict.update({
                        "action": action_name,
                        "confidence": smooth_res["confidence"],
                        "duration_seconds": smooth_res["duration_seconds"],
                        "transition_occurred": smooth_res["transition_occurred"],
                        "previous_action": smooth_res["previous_action"],
                        "category": action_meta["category"],
                        "severity": action_meta["severity"],
                        "color": action_meta["color"],
                        "icon": action_meta["icon"],
                        "probabilities": smooth_res["smoothed_probabilities"]
                    })
                    tracks_payload.append(track_dict)

            # 5. Clean up stale smoother states
            active_ids = [s.id for s in tracked_subjects]
            smoother.cleanup(active_ids)

            # 6. Evaluate Complex Event Processor
            alerts = cep.process_frame(tracks_payload, now)

            # 7. Compress frame to JPEG
            _, jpeg_buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 72])
            frame_b64 = base64.b64encode(jpeg_buf).decode("utf-8")

            t_loop_end = time.time()
            latency_ms = round((t_loop_end - t_loop_start) * 1000, 1)

            # 8. Send payload packet
            packet = {
                "frame_id": frame_count,
                "timestamp": round(now, 3),
                "fps": current_fps,
                "latency_ms": latency_ms,
                "source": streamer.current_source,
                "active_tracks_count": len(tracks_payload),
                "tracks": tracks_payload,
                "alerts": alerts,
                "frame": f"data:image/jpeg;base64,{frame_b64}"
            }

            await websocket.send_text(json.dumps(packet))

            # Maintain ~25 FPS
            elapsed = time.time() - t_loop_start
            sleep_duration = max(0.005, (1.0 / 25.0) - elapsed)
            await asyncio.sleep(sleep_duration)

    except WebSocketDisconnect:
        print("[WebSocket] Client disconnected cleanly.")
    except Exception as e:
        print(f"[WebSocket] Streaming loop terminated: {e}")
    finally:
        receiver_task.cancel()
