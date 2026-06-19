# Quick Start Guide

## Prerequisites

- Python 3.8+
- pip

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd <repo-name>

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Setup Data

1. Place your video files in the `data/` directory:
   ```
   data/
   ├── case2.mp4
   └── case4.mp4
   ```

2. Verify paths in configuration files are correct (they should already point to `data/case2.mp4` and `data/case4.mp4`)

## Run PatchCore Method

```bash
python scripts/run_patchcore_resnet_style.py --config configs/assignment03.yaml
```

**Expected outputs:**
- Videos in `outputs/videos/`
- Frames in `outputs/frames/`
- Metrics in `outputs/metrics/`
- Models in `outputs/models/`

## Run Rule-Based Method

```bash
python scripts/render_stable_v2.py
```

**Expected outputs:**
- Videos in `outputs/videos_stable_v2/`
- Frames in `outputs/frames_stable_v2/`
- Metrics in `outputs/metrics_stable_v2/`

## Troubleshooting

### Video not found error
Make sure your video files are in the `data/` directory and the paths in config files are correct.

### Module not found error
Run `pip install -r requirements.txt` again to ensure all dependencies are installed.

### Out of memory error
Reduce `coreset_limit` in `configs/assignment03.yaml` (e.g., from 2200 to 1000).

## Configuration Tips

- **Training range**: Use only normal/defect-free segments
- **Testing range**: Include both normal and defective samples
- **ROI coordinates**: Adjust based on your video resolution and inspection area
- **Threshold quantile**: Higher values = stricter detection (fewer false positives, more false negatives)

For detailed parameter explanations, see the main [README.md](../README.md).
