"""
Spatial Human Detector & Multi-Object Tracker (MOT)
Maintains persistent subject identities across frames with coordinate smoothing and velocity estimation.
"""

from typing import List, Dict, Tuple, Optional
import time
import numpy as np
import cv2

class TrackedPerson:
    def __init__(self, track_id: int, bbox: List[float], timestamp: float):
        self.id = track_id
        self.bbox = [float(x) for x in bbox]  # [x1, y1, x2, y2]
        self.raw_bbox = list(self.bbox)
        self.history: List[Tuple[float, float]] = []  # [(cx, cy), ...]
        self.lost_count = 0
        self.total_frames = 1
        self.velocity = [0.0, 0.0]  # [vx, vy] px/sec
        self.first_seen = timestamp
        self.last_seen = timestamp
        
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        self.history.append((cx, cy))

    def update(self, new_bbox: List[float], timestamp: float, alpha: float = 0.7):
        """Smoothly updates bounding box coordinates with EMA to eliminate camera jitter."""
        dt = max(1e-4, timestamp - self.last_seen)
        old_cx = (self.bbox[0] + self.bbox[2]) / 2.0
        old_cy = (self.bbox[1] + self.bbox[3]) / 2.0
        
        # Coordinate EMA smoothing
        for i in range(4):
            self.bbox[i] = alpha * new_bbox[i] + (1.0 - alpha) * self.bbox[i]
        self.raw_bbox = list(new_bbox)
        
        new_cx = (self.bbox[0] + self.bbox[2]) / 2.0
        new_cy = (self.bbox[1] + self.bbox[3]) / 2.0
        
        self.velocity = [(new_cx - old_cx) / dt, (new_cy - old_cy) / dt]
        self.history.append((new_cx, new_cy))
        if len(self.history) > 30:
            self.history.pop(0)
            
        self.lost_count = 0
        self.total_frames += 1
        self.last_seen = timestamp

    def mark_missed(self):
        self.lost_count += 1

    def to_dict(self) -> Dict:
        cx = (self.bbox[0] + self.bbox[2]) / 2.0
        cy = (self.bbox[1] + self.bbox[3]) / 2.0
        return {
            "id": self.id,
            "bbox": [round(c, 1) for c in self.bbox],
            "center": [round(cx, 1), round(cy, 1)],
            "velocity": [round(v, 1) for v in self.velocity],
            "history": [[round(x, 1), round(y, 1)] for x, y in self.history[-15:]],
            "age_seconds": round(self.last_seen - self.first_seen, 2),
            "total_frames": self.total_frames
        }

def compute_iou(boxA: List[float], boxB: List[float]) -> float:
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = max(1e-4, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = max(1e-4, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    iou = interArea / float(boxAArea + boxBArea - interArea)
    return max(0.0, min(1.0, iou))

class MultiObjectTracker:
    def __init__(self, iou_threshold: float = 0.25, max_lost_frames: int = 30):
        self.iou_threshold = iou_threshold
        self.max_lost_frames = max_lost_frames
        self.tracks: Dict[int, TrackedPerson] = {}
        self.next_id = 1
        
        # Built-in lightweight HOG person detector for CPU/GPU fallback
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect_people_fallback(self, frame: np.ndarray) -> List[List[float]]:
        """Fast fallback detector using OpenCV HOG + Contour saliency for robust multi-person detection."""
        h, w = frame.shape[:2]
        boxes = []
        
        # Scale down for speed
        scale = 1.0
        if w > 640:
            scale = 640.0 / w
            small_frame = cv2.resize(frame, (640, int(h * scale)))
        else:
            small_frame = frame
            
        rects, weights = self.hog.detectMultiScale(
            small_frame, 
            winStride=(8, 8), 
            padding=(4, 4), 
            scale=1.05
        )
        
        for (rx, ry, rw, rh), weight in zip(rects, weights):
            if weight > 0.15:
                x1 = float(rx / scale)
                y1 = float(ry / scale)
                x2 = float((rx + rw) / scale)
                y2 = float((ry + rh) / scale)
                boxes.append([x1, y1, x2, y2])
                
        # If no HOG detections, use foreground/movement saliency fallback
        if not boxes:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (21, 21), 0)
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find largest upright contour
            cand = []
            for cnt in contours:
                cx, cy, cw, ch = cv2.boundingRect(cnt)
                aspect = ch / max(1.0, float(cw))
                area = cw * ch
                if area > (w * h * 0.04) and aspect >= 1.0:
                    cand.append([float(cx), float(cy), float(cx + cw), float(cy + ch)])
            if cand:
                cand.sort(key=lambda b: (b[2]-b[0])*(b[3]-b[1]), reverse=True)
                boxes = cand[:2]
                
        return boxes

    def update(self, detected_boxes: List[List[float]], timestamp: float) -> List[TrackedPerson]:
        """Associates detections with active tracks using IoU cost matrix."""
        active_ids = list(self.tracks.keys())
        
        if not detected_boxes:
            for tid in active_ids:
                self.tracks[tid].mark_missed()
                if self.tracks[tid].lost_count > self.max_lost_frames:
                    del self.tracks[tid]
            return [t for t in self.tracks.values() if t.lost_count == 0]

        if not active_ids:
            for box in detected_boxes:
                new_track = TrackedPerson(self.next_id, box, timestamp)
                self.tracks[self.next_id] = new_track
                self.next_id += 1
            return list(self.tracks.values())

        # Construct IoU Matrix
        iou_matrix = np.zeros((len(active_ids), len(detected_boxes)), dtype=np.float32)
        for i, tid in enumerate(active_ids):
            for j, box in enumerate(detected_boxes):
                iou_matrix[i, j] = compute_iou(self.tracks[tid].bbox, box)

        # Greedy bipartite matching
        matched_tracks = set()
        matched_detections = set()

        while True:
            max_idx = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
            max_iou = iou_matrix[max_idx]
            if max_iou < self.iou_threshold:
                break
            
            track_idx, det_idx = max_idx
            tid = active_ids[track_idx]
            self.tracks[tid].update(detected_boxes[det_idx], timestamp)
            
            matched_tracks.add(tid)
            matched_detections.add(det_idx)
            
            iou_matrix[track_idx, :] = -1.0
            iou_matrix[:, det_idx] = -1.0

        # Mark unmatched tracks as missed
        for tid in active_ids:
            if tid not in matched_tracks:
                self.tracks[tid].mark_missed()
                if self.tracks[tid].lost_count > self.max_lost_frames:
                    del self.tracks[tid]

        # Register new detections as new tracks
        for j, box in enumerate(detected_boxes):
            if j not in matched_detections:
                new_track = TrackedPerson(self.next_id, box, timestamp)
                self.tracks[self.next_id] = new_track
                self.next_id += 1

        return [t for t in self.tracks.values() if t.lost_count <= 2]
