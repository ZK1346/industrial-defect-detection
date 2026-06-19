# Project Structure

```
.
├── configs/                    # Configuration files
│   └── assignment03.yaml      # Main configuration (video paths, parameters)
│
├── scripts/                    # Python scripts
│   ├── run_patchcore_resnet_style.py  # PatchCore anomaly detection
│   └── render_stable_v2.py            # Rule-based inspection
│
├── data/                       # Video data directory (not in git)
│   ├── README.md              # Instructions for adding videos
│   ├── case2.mp4              # Case 2 video file
│   └── case4.mp4              # Case 4 video file
│
├── outputs/                    # Generated outputs (mostly not in git)
│   ├── videos/                # Demo videos from PatchCore
│   │   └── .gitkeep
│   ├── frames/                # Frame snapshots from PatchCore
│   │   └── .gitkeep
│   ├── metrics/               # Metrics and summaries from PatchCore
│   │   └── .gitkeep
│   ├── models/                # Trained memory banks
│   │   └── .gitkeep
│   ├── videos_stable_v2/      # Demo videos from rule-based method
│   ├── frames_stable_v2/      # Frame snapshots from rule-based method
│   └── metrics_stable_v2/     # Metrics from rule-based method
│
├── requirements.txt           # Python dependencies
├── README.md                  # Main documentation
├── QUICKSTART.md             # Quick start guide
├── LICENSE                   # MIT License
└── .gitignore               # Git ignore rules
```

## Directory Descriptions

### `configs/`
Contains YAML configuration files with:
- Video file paths
- Training/testing time ranges
- ROI coordinates
- Algorithm parameters

### `scripts/`
Main executable Python scripts:
- **run_patchcore_resnet_style.py**: Implements PatchCore-based anomaly detection
- **render_stable_v2.py**: Implements rule-based computer vision inspection

### `data/`
Directory for video input files (excluded from git due to size):
- Place your `.mp4` or other video files here
- Update paths in config files if using different locations

### `outputs/`
Generated output directories:
- **videos/**: 15-second demo videos showing detection results
- **frames/**: Key frame images with OK/NG labels
- **metrics/**: Performance metrics, CSV files, plots, JSON summaries
- **models/**: Saved memory bank files (.npy format)

Note: Most output files are excluded from git tracking per `.gitignore`

### Root Files
- **requirements.txt**: Python package dependencies
- **README.md**: Comprehensive project documentation
- **QUICKSTART.md**: Step-by-step setup and usage guide
- **LICENSE**: MIT license terms
- **.gitignore**: Rules for excluding files from version control
