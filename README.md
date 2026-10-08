# OmniAction AI • Spatial-Temporal Human Behavior & Action Intelligence Platform

<p align="center">
  <strong>Real-Time Multi-Object Tracking (MOT) • 15-Class Human Action Recognition • Anti-Flicker Temporal Hysteresis • Behavioral Telemetry</strong>
</p>

---

## 📌 Overview

**OmniAction AI** is an enterprise-grade Computer Vision and Human Behavioral Telemetry platform. It bridges continuous video streams (webcams, CCTV, or uploaded videos) with deep learning spatial tracking and the **15-class Human Action Recognition (HAR)** dataset (`meetnagadia/human-action-recognition-har-dataset`).

Rather than performing simple static frame classification, OmniAction AI implements a **spatio-temporal pipeline** that:
1. Detects and tracks multiple subjects continuously with persistent identities (`Subject #1`, `Subject #2`).
2. Applies dynamic contextual region-of-interest (ROI) expansion to preserve critical object interactions (e.g., cups, laptops, smartphones).
3. Infers actions across the 15 categories with deep convolutional networks.
4. Stabilizes predictions using an **Exponential Moving Average (EMA)** filter and a **Hysteresis State Machine** to eliminate frame-by-frame label flicker.
5. Evaluates complex behavioral rules (e.g., physical altercations, sedentary warnings, focus vs. distraction ratios, hydration logging).
6. Delivers real-time 60-FPS telemetry and interactive Canvas HUD overlays over high-speed WebSockets.

---

## 🌟 Key Platform Modules

### 1. 🎥 Live Vision Studio
* **Adaptive Ingestion**: Seamlessly switch between **Procedural Synthetic Simulation**, **Physical Webcam**, and **Uploaded Video Files**.
* **Canvas HUD Overlay**: High-speed HTML5 Canvas rendering bounding boxes with rounded corners, glowing status outlines, and overhead telemetry tags (`[ID #01] USING_LAPTOP (94%)`).
* **Motion History Trails**: Visualizes movement paths across space and time.
* **Control Dock**: Interactive sliders for EMA smoothing intensity ($\alpha$), detection confidence thresholds, and visual layer toggles.

### 2. 📊 Behavioral Telemetry & Multi-Subject Gantt Timeline
* **Interactive Gantt Chart**: Horizontal timeline bars mapping historical state transitions per tracked individual (e.g., `sitting` $\rightarrow$ `using_laptop` $\rightarrow$ `drinking` $\rightarrow$ `texting`).
* **Ergonomics & Focus Gauge**: Animated circular meter calculating real-time Focus Score vs. Distraction Ratio.
* **Cumulative Activity Distribution**: Dynamic breakdown of time spent across all 15 classes.
* **Chronological Audit Stream**: Real-time event feed capturing security alerts and posture transitions.

### 3. 🔬 Diagnostic Studio & Grad-CAM Explainability
* **Drag-and-Drop Inspector**: Test any still image or photo from the Kaggle HAR dataset.
* **Instant Presets**: Test pre-configured action poses (`using_laptop`, `calling`, `drinking`, `texting`, `fighting`, `running`).
* **Visual Attention Heatmap**: Side-by-side comparison of the extracted subject crop against Class Activation Mapping (Grad-CAM) saliency maps.
* **Top-5 Probability Spectrum**: Animated gradient distribution bars showing model prediction confidences.

### 4. 🗂️ 15-Class Catalog & Architecture Visualizer
* **Taxonomy Explorer**: Interactive catalog of all 15 classes grouped into logical categories (*Productive & Desk*, *Communication & Device*, *Wellness & Sustenance*, *Dynamic Movement*, *Social & Security*).
* **Pipeline Flowchart**: Dynamic node graph visualizing the end-to-end data pipeline from ingestion to presentation.

---

## 🏷️ The 15 Action Categories

| Category | Classes | Key Visual Cues |
| :--- | :--- | :--- |
| **Productive & Desk** | `using_laptop`, `sitting` | Hands forward on keyboard, seated posture, monitor glow |
| **Communication & Device** | `calling`, `texting`, `listeningtomusic` | Smartphone to ear, downward neck flexion, headphones |
| **Wellness & Sustenance** | `drinking`, `eating`, `sleeping`, `laughing` | Vessel to mouth, dining utensils, reclining posture |
| **Dynamic Movement** | `running`, `cycling`, `dancing` | Wide stride, kinetic limbs, pedaling motion |
| **Social & Security** | `fighting`, `hugging`, `clapping` | Combative stance (High Alert), mutual embrace, clapping |

---

## 📐 System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Vite + Vanilla CSS)                             │
│  ┌──────────────────────┐  ┌─────────────────────────┐  ┌───────────────────────────┐  │
│  │  Live Vision Studio  │  │ Behavioral Telemetry &  │  │ Model Diagnostic Studio   │  │
│  │ (Canvas HUD Overlay) │  │  Gantt Timeline Chart   │  │   & Grad-CAM Heatmaps     │  │
│  └──────────▲───────────┘  └────────────▲────────────┘  └─────────────▲─────────────┘  │
└─────────────┼───────────────────────────┼─────────────────────────────┼────────────────┘
              │                           │                             │
              │ WebSockets (30 FPS Telemetry)                           │ REST API
              ▼                           ▼                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI + PyTorch)                               │
│                                                                                        │
│  ┌─────────────────┐       ┌────────────────────────┐       ┌───────────────────────┐  │
│  │ Ingestion &     │ ────► │ Multi-Object Tracking  │ ────► │ Contextual Dynamic    │  │
│  │ Video Streamer  │       │ (Spatial Detector+MOT) │       │ ROI Crop Extractor    │  │
│  └─────────────────┘       └────────────────────────┘       └───────────┬───────────┘  │
│                                                                         │              │
│  ┌─────────────────┐       ┌────────────────────────┐       ┌───────────▼───────────┐  │
│  │ Complex Event   │ ◄──── │ Temporal Smoothing &   │ ◄──── │ 15-Class HAR Model    │  │
│  │ Processor (CEP) │       │ Hysteresis Engine (EMA)│       │ (Pure PyTorch CNN)    │  │
│  └────────┬────────┘       └────────────────────────┘       └───────────────────────┘  │
│           ▼                                                                            │
│  [Time-Series Event Bus & In-Memory Session Registry]                                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

* **Backend**:
  * [Python 3.10+](https://python.org)
  * [FastAPI](https://fastapi.tiangolo.com) & [Uvicorn](https://www.uvicorn.org)
  * [PyTorch](https://pytorch.org) (MobileNet-style inverted bottleneck convolutional backbone)
  * [OpenCV](https://opencv.org) (Fast BGR tensor transforms, frame decoding)
  * [WebSockets](https://websockets.readthedocs.io) (Low-latency bidirectional streaming)
* **Frontend**:
  * [Vite](https://vitejs.dev)
  * Modern Vanilla JavaScript (ES Modules)
  * Bespoke **Vanilla CSS Design System** (Cyber-Obsidian glassmorphic theme, neon accents, Google Fonts *Plus Jakarta Sans* & *JetBrains Mono*)
  * HTML5 Canvas for zero-overhead 60 FPS HUD rendering

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Srishanth-Tadakala/Human-Tracking-CV-project.git
cd Human-Tracking-CV-project
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run self-verification test suite
python test_cv_pipeline.py

# Launch FastAPI backend server
python run_server.py
```
*Backend runs on `http://127.0.0.1:8000` (API documentation available at `/docs`).*

### 3. Frontend Setup
In a new terminal:
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```
*Frontend runs on `http://localhost:5173`.*

---

## 📡 REST API & WebSocket Specifications

### Endpoints
* `GET /api/health` — System health and status check.
* `GET /api/system/stats` — Hardware telemetry, active track count, and focus scores.
* `GET /api/dataset/classes` — 15-class catalog metadata and visual cues.
* `POST /api/predict/image` — Single-image diagnostic analysis with Grad-CAM heatmap.
* `POST /api/video/upload` — Video file upload for continuous stream tracking.
* `WS /ws/stream` — Bidirectional real-time stream carrying video frames and synchronized telemetry.

---

## 📄 Dataset Reference
* **Dataset**: [Human Action Recognition (HAR) Dataset](https://www.kaggle.com/datasets/meetnagadia/human-action-recognition-har-dataset) by Meet Nagadia on Kaggle.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
