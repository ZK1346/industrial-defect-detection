# Data Directory

Place your video files here before running the scripts.

## Required Files

- `case2.mp4` - Video for Case 2 (round cap inspection)
- `case4.mp4` - Video for Case 4 (four small-cap inspection)

## Notes

1. These video files are **not included** in the repository due to their large size
2. Update the video paths in configuration files if you use different filenames or locations:
   - `configs/assignment03.yaml`
   - `scripts/render_stable_v2.py`
3. Supported formats: `.mp4`, `.avi`, `.mov`, `.mkv` (OpenCV compatible)

## Example Structure

```
data/
├── case2.mp4
└── case4.mp4
```
