# Industrial Defect Detection - PatchCore & Rule-Based Methods

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📖 Project Overview

This project implements two industrial defect detection approaches for quality inspection of manufactured products:

1. **PatchCore-based Anomaly Detection**: A memory-bank approach using ResNet-style local descriptors for unsupervised anomaly detection
2. **Rule-based Inspection**: Traditional computer vision methods using color segmentation, shape detection, and geometric constraints

Both methods are applied to detect defects in bottle caps and containers from video streams.

## ✨ Features

### Method 1: PatchCore with ResNet-style Descriptors
- **Unsupervised Learning**: Trains only on normal samples
- **Local Feature Extraction**: Multi-channel descriptors (HSV, LAB, gradients, texture)
- **Memory Bank + Coreset Sampling**: Efficient feature storage and retrieval
- **Temporal Voting**: Stable predictions through temporal smoothing
- **Heatmap Visualization**: Patch-level anomaly score visualization

### Method 2: Rule-Based Inspection
- **Color Segmentation**: HSV-based detection of specific colors (yellow lids, blue caps)
- **Shape Detection**: Circle detection and bounding box tracking
- **Geometric Constraints**: Position validation and spatial reasoning
- **Multi-check Verification**: Multiple inspection criteria per product
- **Stable Voting Mechanism**: Reduces false positives through temporal consistency

## 📁 Project Structure

```
.
├── configs/
│   └── assignment03.yaml          # Configuration file (video paths, parameters)
├── scripts/
│   ├── run_patchcore_resnet_style.py  # PatchCore implementation
│   └── render_stable_v2.py            # Rule-based inspection
├── outputs/
│   ├── frames/                    # Saved frame examples
│   ├── metrics/                   # Performance metrics and summaries
│   ├── models/                    # Trained memory banks
│   └── videos/                    # Output demo videos
├── data/                          # Place your video files here
│   ├── case2.mp4                  # Case 2: Round cap inspection
│   └── case4.mp4                  # Case 4: Four small-cap inspection
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <repo-name>
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 📝 Configuration

Before running the scripts, update the video paths in `configs/assignment03.yaml`:

```yaml
cases:
  case2:
    video: "data/case2.mp4"  # Update this path
    train_range_sec: [0, 120]
    test_range_sec: [350, 390]
    roi: [650, 260, 420, 420]
    # ... other parameters
  case4:
    video: "data/case4.mp4"  # Update this path
    # ... other parameters
```

Also update video paths in `scripts/render_stable_v2.py`:
```python
CASE2_VIDEO = "data/case2.mp4"  # TODO: Update with your video path
CASE4_VIDEO = "data/case4.mp4"  # TODO: Update with your video path
```

## ▶️ Usage

### Method 1: Run PatchCore Anomaly Detection

```bash
python scripts/run_patchcore_resnet_style.py --config configs/assignment03.yaml
```

**Output:**
- `outputs/videos/`: 15-second demo videos showing detection results
- `outputs/frames/`: Representative frames with OK/NG labels
- `outputs/metrics/`: CSV predictions, score curves, and summary JSON
- `outputs/models/`: Saved memory bank files (.npy)

### Method 2: Run Rule-Based Inspection

```bash
python scripts/render_stable_v2.py
```

**Output:**
- `outputs/videos_stable_v2/`: Demo videos with inspection overlays
- `outputs/frames_stable_v2/`: Key frames showing detection results
- `outputs/metrics_stable_v2/`: Performance metrics summary

## 🔧 Key Parameters

### PatchCore Configuration (`configs/assignment03.yaml`)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resize` | ROI resize dimensions | [160, 160] |
| `grid` | Patch grid size (rows, cols) | [8, 8] |
| `coreset_limit` | Maximum memory bank size | 2200 |
| `knn_k` | K-nearest neighbors for scoring | 3 |
| `vote_window` | Temporal voting window size | 5 |
| `min_ng_votes` | Minimum NG votes for stable prediction | 2 |
| `threshold_quantile` | Anomaly threshold percentile | 0.90 |

### Training/Testing Ranges

Adjust `train_range_sec` and `test_range_sec` based on your video content:
- **Training range**: Should contain only normal/defect-free samples
- **Testing range**: Contains both normal and defective samples for evaluation

## 📊 Results

The system outputs comprehensive metrics including:
- Frame-level anomaly scores
- OK/NG classification results
- Processing speed (FPS estimates)
- Visual heatmaps highlighting anomalous regions
- Summary statistics in JSON format

Example output structure:
```json
{
  "case2": {
    "video": "outputs/videos/case2_demo.mp4",
    "frames": 225,
    "fps_estimate": 12.4,
    "ok_frames": 75,
    "ng_frames": 150
  }
}
```

## 🎯 Use Cases

This project demonstrates industrial quality inspection for:
- **Case 2**: Round bottle cap inspection (yellow lid detection)
- **Case 4**: Multi-cap container inspection (transparent/blue cap detection)

The methods can be adapted for other manufacturing scenarios requiring:
- Surface defect detection
- Missing component identification
- Color/shape verification
- Assembly quality control

## 🛠️ Technical Details

### PatchCore Approach
1. **Feature Extraction**: Extracts multi-channel descriptors from image patches
   - Color features (HSV, LAB mean/std)
   - Gradient orientation histograms
   - Texture statistics
   - Raw pixel values (downsampled)

2. **Memory Bank Construction**: 
   - Collects features from normal training samples
   - Applies coreset sampling to limit memory size
   - Builds KNN index for efficient nearest neighbor search

3. **Anomaly Scoring**:
   - Computes distance to nearest normal features
   - Aggregates top-K patch scores for robustness
   - Applies temporal voting for stable predictions

### Rule-Based Approach
1. **Object Localization**: Uses color segmentation and geometric constraints
2. **Quality Metrics**: Calculates coverage ratios, edge strength, color saturation
3. **Multi-criteria Decision**: Combines multiple checks per product
4. **Temporal Smoothing**: Maintains stable predictions across frames

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

Computer Vision Course Project

## 🙏 Acknowledgments

- PatchCore method inspired by anomaly detection research
- OpenCV for computer vision operations
- scikit-learn for nearest neighbor search

---

**Note**: This is an academic project for educational purposes. For production use, consider additional validation and optimization.