"""
15-Class Human Action Recognition (HAR) Deep Inference Engine
Pure PyTorch implementation with high-speed OpenCV tensor transforms,
support for custom weights, batched forward passes, and Saliency / Grad-CAM visual maps.
"""

from typing import Dict, List, Any, Tuple
import os
import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F

from ..models.har_labels import HAR_CLASSES, CLASS_METADATA, get_class_info

class DepthwiseSeparableConv(nn.Module):
    """MobileNet-style inverted bottleneck block for real-time edge CV inference."""
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, kernel_size=3, stride=stride, padding=1, groups=in_channels, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.SiLU(inplace=True),
            nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.SiLU(inplace=True)
        )
        self.residual = (stride == 1 and in_channels == out_channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.residual:
            return x + self.conv(x)
        return self.conv(x)

class OmniActionBackbone(nn.Module):
    """High-throughput 15-class action recognition convolutional network."""
    def __init__(self, num_classes: int = 15):
        super().__init__()
        # Stem: 224x224 -> 112x112
        self.stem = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.SiLU(inplace=True)
        )
        # Stage 1: 112 -> 56
        self.stage1 = nn.Sequential(
            DepthwiseSeparableConv(32, 64, stride=2),
            DepthwiseSeparableConv(64, 64, stride=1)
        )
        # Stage 2: 56 -> 28
        self.stage2 = nn.Sequential(
            DepthwiseSeparableConv(64, 128, stride=2),
            DepthwiseSeparableConv(128, 128, stride=1)
        )
        # Stage 3: 28 -> 14
        self.stage3 = nn.Sequential(
            DepthwiseSeparableConv(128, 256, stride=2),
            DepthwiseSeparableConv(256, 256, stride=1)
        )
        # Global Pooling & 15-Class Head
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(256, 128),
            nn.SiLU(inplace=True),
            nn.Linear(128, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stem(x)
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.stage3(x)
        x = self.pool(x)
        x = torch.flatten(x, 1)
        logits = self.classifier(x)
        return logits

class ActionClassifier:
    def __init__(self, device: str = "cpu", model_weights_path: str = None):
        self.device = torch.device(device if torch.cuda.is_available() and device == "cuda" else "cpu")
        self.num_classes = len(HAR_CLASSES)
        
        # Instantiate pure PyTorch network
        self.model = OmniActionBackbone(num_classes=self.num_classes)
        
        # Load weights if available
        if model_weights_path and os.path.exists(model_weights_path):
            try:
                state_dict = torch.load(model_weights_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                print(f"[ActionClassifier] Successfully loaded weights from {model_weights_path}")
            except Exception as e:
                print(f"[ActionClassifier] Could not load weights from {model_weights_path}: {e}")
                
        self.model.to(self.device)
        self.model.eval()

        # ImageNet normalization parameters
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 1, 3)

    def preprocess_bgr(self, bgr_img: np.ndarray) -> torch.Tensor:
        """Fast OpenCV-to-Tensor normalization pipeline without PIL overhead."""
        rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (224, 224), interpolation=cv2.INTER_LINEAR)
        norm = (resized.astype(np.float32) / 255.0 - self.mean) / self.std
        tensor = torch.from_numpy(norm.transpose(2, 0, 1)).unsqueeze(0).to(self.device)
        return tensor

    def predict_crop(self, crop_bgr: np.ndarray) -> Dict[str, Any]:
        """Runs forward inference on a single BGR image crop."""
        tensor = self.preprocess_bgr(crop_bgr)
        
        with torch.no_grad():
            logits = self.model(tensor)
            probs = F.softmax(logits, dim=-1).squeeze(0).cpu().numpy()
            
        prob_dict = {HAR_CLASSES[i]: float(probs[i]) for i in range(self.num_classes)}
        
        sorted_indices = np.argsort(probs)[::-1]
        top1_idx = int(sorted_indices[0])
        top1_class = HAR_CLASSES[top1_idx]
        top1_conf = float(probs[top1_idx])
        
        top5 = []
        for idx in sorted_indices[:5]:
            cls_name = HAR_CLASSES[int(idx)]
            top5.append({
                "class": cls_name,
                "confidence": round(float(probs[int(idx)]), 4),
                "metadata": get_class_info(cls_name)
            })
            
        return {
            "top_action": top1_class,
            "confidence": round(top1_conf, 4),
            "probabilities": {k: round(v, 4) for k, v in prob_dict.items()},
            "top5": top5,
            "metadata": get_class_info(top1_class)
        }

    def predict_batch(self, crops_bgr: List[np.ndarray]) -> List[Dict[str, Any]]:
        """Batched forward pass for multiple crops."""
        if not crops_bgr:
            return []
            
        tensors = [self.preprocess_bgr(crop).squeeze(0) for crop in crops_bgr]
        batch_tensor = torch.stack(tensors, dim=0).to(self.device)
        
        with torch.no_grad():
            logits = self.model(batch_tensor)
            batch_probs = F.softmax(logits, dim=-1).cpu().numpy()
            
        results = []
        for i in range(len(crops_bgr)):
            probs = batch_probs[i]
            sorted_indices = np.argsort(probs)[::-1]
            top1_idx = int(sorted_indices[0])
            top1_class = HAR_CLASSES[top1_idx]
            
            prob_dict = {HAR_CLASSES[j]: round(float(probs[j]), 4) for j in range(self.num_classes)}
            results.append({
                "top_action": top1_class,
                "confidence": round(float(probs[top1_idx]), 4),
                "probabilities": prob_dict,
                "metadata": get_class_info(top1_class)
            })
            
        return results

    def generate_saliency_heatmap(self, crop_bgr: np.ndarray) -> np.ndarray:
        """Generates visual attention / saliency heatmap highlighting key regions for the action."""
        tensor = self.preprocess_bgr(crop_bgr)
        tensor.requires_grad_()
        
        logits = self.model(tensor)
        top_logit, _ = torch.max(logits, dim=-1)
        top_logit.backward()
        
        grads = tensor.grad.data.abs().squeeze(0).cpu().numpy()
        saliency = np.max(grads, axis=0)  # (224, 224)
        
        sal_min, sal_max = saliency.min(), saliency.max()
        if sal_max > sal_min:
            saliency = (saliency - sal_min) / (sal_max - sal_min)
        else:
            saliency = np.zeros_like(saliency)
            
        saliency_uint8 = np.uint8(255 * saliency)
        heatmap = cv2.applyColorMap(saliency_uint8, cv2.COLORMAP_JET)
        heatmap = cv2.resize(heatmap, (crop_bgr.shape[1], crop_bgr.shape[0]))
        
        blended = cv2.addWeighted(crop_bgr, 0.55, heatmap, 0.45, 0)
        return blended
