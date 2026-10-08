"""
Universal Video Stream Adapter & Dynamic Synthetic Scene Generator
Supports physical webcams, uploaded video files, and rich multi-subject synthetic procedural streams.
"""

from typing import Tuple, Optional, Dict, Any, List
import time
import math
import cv2
import numpy as np

class VideoStreamManager:
    def __init__(self, width: int = 960, height: int = 540):
        self.width = width
        self.height = height
        self.cap: Optional[cv2.VideoCapture] = None
        self.current_source: str = "synthetic"  # "synthetic" | "webcam" | "file"
        self.file_path: Optional[str] = None
        
        # Synthetic simulation state
        self.sim_frame_count = 0
        self.sim_start_time = time.time()

    def set_source(self, source_type: str, file_path: Optional[str] = None):
        """Switches the active video ingestion source."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.current_source = source_type
        self.file_path = file_path

        if source_type == "webcam":
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("[VideoStreamManager] Could not open webcam, falling back to synthetic stream.")
                self.current_source = "synthetic"
        elif source_type == "file" and file_path:
            self.cap = cv2.VideoCapture(file_path)
            if not self.cap.isOpened():
                print(f"[VideoStreamManager] Could not open video file {file_path}, falling back to synthetic.")
                self.current_source = "synthetic"
        else:
            self.current_source = "synthetic"

    def get_frame(self) -> Tuple[np.ndarray, bool]:
        """Returns the next BGR frame and a boolean indicating whether the stream is active."""
        if self.current_source in ["webcam", "file"] and self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and frame is not None:
                # Resize if needed
                if frame.shape[1] != self.width or frame.shape[0] != self.height:
                    frame = cv2.resize(frame, (self.width, self.height))
                return frame, True
            else:
                # Video file loop
                if self.current_source == "file":
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        frame = cv2.resize(frame, (self.width, self.height))
                        return frame, True
                # If webcam failed or file ended
                return self._render_synthetic_scene(), True

        # Render synthetic simulation scene
        return self._render_synthetic_scene(), True

    def _render_synthetic_scene(self) -> np.ndarray:
        """Renders an interactive multi-person workspace simulation with realistic movements & postures."""
        self.sim_frame_count += 1
        t = (time.time() - self.sim_start_time)
        
        # Base canvas: Modern tech office environment (Dark Slate Blue gradient)
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Subtle gradient background & perspective floor
        for y in range(self.height):
            ratio = y / float(self.height)
            b = int(18 + 15 * ratio)
            g = int(22 + 18 * ratio)
            r = int(32 + 25 * ratio)
            canvas[y, :] = (b, g, r)

        # Draw office floor grid lines
        grid_color = (45, 52, 70)
        cv2.line(canvas, (0, int(self.height * 0.72)), (self.width, int(self.height * 0.72)), grid_color, 1)
        for gx in range(0, self.width, 80):
            cv2.line(canvas, (gx, int(self.height * 0.72)), (int(gx * 1.3 - self.width * 0.15), self.height), grid_color, 1)

        # Subject 1: Seated at desk (Desk Operator)
        # Periodically transitions: using_laptop (0-15s) -> drinking (15-20s) -> texting (20-30s) -> using_laptop
        cycle_1 = t % 30.0
        s1_x, s1_y = 260, 290
        
        # Desk surface
        cv2.rectangle(canvas, (180, 360), (380, 460), (35, 42, 58), -1)
        cv2.rectangle(canvas, (180, 360), (380, 460), (60, 72, 98), 2)
        
        # Subject 1 Body
        head_bob = int(math.sin(t * 3.0) * 2)
        # Torso
        cv2.rectangle(canvas, (s1_x - 35, s1_y + 40 + head_bob), (s1_x + 35, s1_y + 130 + head_bob), (70, 90, 130), -1)
        # Head
        cv2.circle(canvas, (s1_x, s1_y + head_bob), 28, (210, 180, 160), -1)
        
        if cycle_1 < 15.0:
            # Action: using_laptop
            # Laptop base & screen with glow
            cv2.rectangle(canvas, (240, 345), (320, 360), (140, 140, 150), -1)
            cv2.line(canvas, (240, 345), (230, 310), (180, 180, 190), 3)
            # Screen glow
            pts = np.array([[230, 310], [280, 305], [280, 345], [240, 345]], np.int32)
            cv2.fillPoly(canvas, [pts], (180, 220, 255))
            # Arms on keyboard
            cv2.line(canvas, (s1_x - 25, s1_y + 80), (250, 348), (210, 180, 160), 8)
            cv2.line(canvas, (s1_x + 25, s1_y + 80), (280, 348), (210, 180, 160), 8)
        elif cycle_1 < 20.0:
            # Action: drinking (mug lifted to head)
            arm_lift = int((cycle_1 - 15.0) * 8)
            cv2.circle(canvas, (s1_x + 18, s1_y + 15 + head_bob), 10, (80, 180, 220), -1)  # Cup
            cv2.line(canvas, (s1_x + 25, s1_y + 80), (s1_x + 18, s1_y + 15 + head_bob), (210, 180, 160), 8)
            cv2.line(canvas, (s1_x - 25, s1_y + 80), (230, 350), (210, 180, 160), 8)
        else:
            # Action: texting (holding smartphone near chest, looking down)
            cv2.rectangle(canvas, (s1_x - 8, s1_y + 60), (s1_x + 8, s1_y + 80), (30, 30, 40), -1)  # Phone
            cv2.line(canvas, (s1_x - 25, s1_y + 80), (s1_x - 5, s1_y + 70), (210, 180, 160), 8)
            cv2.line(canvas, (s1_x + 25, s1_y + 80), (s1_x + 5, s1_y + 70), (210, 180, 160), 8)

        # Subject 2: Walking / Dynamic Subject in foreground/middle
        # Walks left to right, stops, calls, or claps
        s2_t = t % 24.0
        if s2_t < 12.0:
            # Walking across room
            s2_x = int(520 + (s2_t - 6.0) * 35)
            s2_y = 270
            bob = int(math.sin(s2_t * 8.0) * 4)
            # Legs walking
            leg_phase = math.sin(s2_t * 8.0) * 20
            cv2.line(canvas, (s2_x - 12, s2_y + 130), (int(s2_x - 12 - leg_phase), s2_y + 200), (40, 50, 70), 9)
            cv2.line(canvas, (s2_x + 12, s2_y + 130), (int(s2_x + 12 + leg_phase), s2_y + 200), (40, 50, 70), 9)
            # Torso
            cv2.rectangle(canvas, (s2_x - 30, s2_y + 35 + bob), (s2_x + 30, s2_y + 130 + bob), (160, 70, 90), -1)
            # Head
            cv2.circle(canvas, (s2_x, s2_y + bob), 26, (215, 185, 165), -1)
            # Arms swinging
            cv2.line(canvas, (s2_x - 20, s2_y + 60), (int(s2_x - 20 + leg_phase), s2_y + 110), (215, 185, 165), 7)
            cv2.line(canvas, (s2_x + 20, s2_y + 60), (int(s2_x + 20 - leg_phase), s2_y + 110), (215, 185, 165), 7)
        else:
            # Stopped, on a call: phone to ear
            s2_x = 730
            s2_y = 270
            bob = 0
            # Standing legs
            cv2.line(canvas, (s2_x - 12, s2_y + 130), (s2_x - 12, s2_y + 200), (40, 50, 70), 9)
            cv2.line(canvas, (s2_x + 12, s2_y + 130), (s2_x + 12, s2_y + 200), (40, 50, 70), 9)
            # Torso
            cv2.rectangle(canvas, (s2_x - 30, s2_y + 35), (s2_x + 30, s2_y + 130), (160, 70, 90), -1)
            # Head
            cv2.circle(canvas, (s2_x, s2_y), 26, (215, 185, 165), -1)
            # Arm raised holding phone to ear
            cv2.line(canvas, (s2_x + 20, s2_y + 60), (s2_x + 22, s2_y), (215, 185, 165), 7)
            cv2.rectangle(canvas, (s2_x + 18, s2_y - 12), (s2_x + 26, s2_y + 10), (20, 20, 30), -1)  # Phone
            cv2.line(canvas, (s2_x - 20, s2_y + 60), (s2_x - 20, s2_y + 110), (215, 185, 165), 7)

        # Subtle noise / camera sensor grain
        noise = np.random.randint(0, 12, (self.height, self.width, 3), dtype=np.uint8)
        canvas = cv2.add(canvas, noise)

        return canvas

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
