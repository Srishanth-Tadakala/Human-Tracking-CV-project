"""
Context-Aware Adaptive Bounding Box Crop Extractor
Preserves surrounding spatial semantics (e.g. coffee cups, laptops, phones) for accurate HAR inference.
"""

from typing import Tuple, List
import numpy as np
import cv2

class ContextAwareCropExtractor:
    def __init__(self, target_resolution: int = 224, padding_factor: float = 0.18):
        self.target_resolution = target_resolution
        self.padding_factor = padding_factor

    def expand_bbox(self, bbox: List[float], img_width: int, img_height: int) -> List[int]:
        """Expands bounding box by padding_factor while clamping inside image boundaries."""
        x1, y1, x2, y2 = bbox
        w = max(1.0, x2 - x1)
        h = max(1.0, y2 - y1)
        
        pad_x = w * self.padding_factor
        pad_y = h * self.padding_factor
        
        exp_x1 = max(0, int(round(x1 - pad_x)))
        exp_y1 = max(0, int(round(y1 - pad_y)))
        exp_x2 = min(img_width, int(round(x2 + pad_x)))
        exp_y2 = min(img_height, int(round(y2 + pad_y)))
        
        # Ensure non-empty region
        if exp_x2 <= exp_x1:
            exp_x2 = min(img_width, exp_x1 + 10)
        if exp_y2 <= exp_y1:
            exp_y2 = min(img_height, exp_y1 + 10)
            
        return [exp_x1, exp_y1, exp_x2, exp_y2]

    def extract_crop(self, frame: np.ndarray, bbox: List[float]) -> Tuple[np.ndarray, List[int]]:
        """Extracts an expanded context crop and resizes it to target resolution."""
        h, w = frame.shape[:2]
        exp_bbox = self.expand_bbox(bbox, w, h)
        x1, y1, x2, y2 = exp_bbox
        
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            # Fallback black canvas
            crop = np.zeros((self.target_resolution, self.target_resolution, 3), dtype=np.uint8)
        else:
            crop = cv2.resize(crop, (self.target_resolution, self.target_resolution), interpolation=cv2.INTER_LINEAR)
            
        return crop, exp_bbox
