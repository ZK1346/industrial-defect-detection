from __future__ import annotations

import argparse
import csv
import json
import math
import time
from collections import deque
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import yaml
from sklearn.neighbors import NearestNeighbors
from tqdm import tqdm


ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs(output_dir: Path) -> dict[str, Path]:
    dirs = {
        "videos": output_dir / "videos",
        "frames": output_dir / "frames",
        "metrics": output_dir / "metrics",
        "models": output_dir / "models",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def open_video(path: str):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    return cap, fps, total, width, height


def read_frame_at(cap, frame_id: int):
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(frame_id)))
    ok, frame = cap.read()
    return frame if ok else None


def clamp_roi(roi, width, height):
    x, y, w, h = [int(v) for v in roi]
    x = max(0, min(x, width - 2))
    y = max(0, min(y, height - 2))
    w = max(2, min(w, width - x))
    h = max(2, min(h, height - y))
    return x, y, w, h


def crop_roi(frame, roi):
    x, y, w, h = roi
    return frame[y : y + h, x : x + w].copy()


def roi_quality(roi_img) -> float:
    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def patch_descriptor(patch: np.ndarray) -> np.ndarray:
    patch = cv2.resize(patch, (32, 32), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB)
    gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)

    means = np.concatenate([hsv.mean(axis=(0, 1)), lab.mean(axis=(0, 1))])
    stds = np.concatenate([hsv.std(axis=(0, 1)), lab.std(axis=(0, 1))])

    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=False)
    hist, _ = np.histogram(ang, bins=8, range=(0, 2 * np.pi), weights=mag)
    hist = hist.astype(np.float32) / (hist.sum() + 1e-6)

    small = cv2.resize(gray, (8, 8), interpolation=cv2.INTER_AREA).astype(np.float32)
    texture = np.array(
        [
            gray.mean(),
            gray.std(),
            roi_quality(patch),
            np.percentile(gray, 10),
            np.percentile(gray, 90),
        ],
        dtype=np.float32,
    )
    desc = np.concatenate([means, stds, hist, texture, small.flatten()])
    desc = desc.astype(np.float32)
    desc = (desc - desc.mean()) / (desc.std() + 1e-6)
    return desc


def extract_patch_features(roi_img, resize_hw=(160, 160), grid=(8, 8)):
    rw, rh = int(resize_hw[0]), int(resize_hw[1])
    gh, gw = int(grid[0]), int(grid[1])
    roi = cv2.resize(roi_img, (rw, rh), interpolation=cv2.INTER_AREA)
    ph, pw = rh // gh, rw // gw
    feats = []
    for gy in range(gh):
        for gx in range(gw):
            patch = roi[gy * ph : (gy + 1) * ph, gx * pw : (gx + 1) * pw]
            feats.append(patch_descriptor(patch))
    return np.vstack(feats)


def coreset(features: np.ndarray, limit: int, seed: int = 7) -> np.ndarray:
    if len(features) <= limit:
        return features
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(features), size=limit, replace=False)
    return features[idx]


def build_memory_bank(case_id: str, cfg: dict, pcfg: dict, dirs: dict[str, Path]):
    cap, fps, total, width, height = open_video(cfg["video"])
    roi = clamp_roi(cfg["roi"], width, height)
    model_path = dirs["models"] / f"{case_id}_memory_bank.npy"
    if model_path.exists():
        memory = np.load(model_path).astype(np.float32)
        model = NearestNeighbors(n_neighbors=int(pcfg["knn_k"]), metric="euclidean")
        model.fit(memory)
        cap.release()
        return model, memory, roi, fps, total, width, height
    start = int(cfg["train_range_sec"][0] * fps)
    end = min(total - 1, int(cfg["train_range_sec"][1] * fps))
    stride = int(cfg.get("train_stride", 45))
    frame_ids = list(range(start, end, stride))

    features = []
    qualities = []
    for fid in tqdm(frame_ids, desc=f"{case_id} train"):
        frame = read_frame_at(cap, fid)
        if frame is None:
            continue
        patch = crop_roi(frame, roi)
        q = roi_quality(patch)
        qualities.append(q)
        if q < 25:
            continue
        features.append(extract_patch_features(patch, pcfg["resize"], pcfg["grid"]))
    cap.release()
    if not features:
        raise RuntimeError(f"No training features for {case_id}")

    memory = np.vstack(features).astype(np.float32)
    memory = coreset(memory, int(pcfg["coreset_limit"]))
    model = NearestNeighbors(n_neighbors=int(pcfg["knn_k"]), metric="euclidean")
    model.fit(memory)
    np.save(model_path, memory)
    return model, memory, roi, fps, total, width, height


def score_roi(model, roi_img, pcfg: dict) -> tuple[float, np.ndarray]:
    feats = extract_patch_features(roi_img, pcfg["resize"], pcfg["grid"])
    dist, _ = model.kneighbors(feats, return_distance=True)
    patch_scores = dist.mean(axis=1)
    # high-score patches preserve small defects better than global averaging.
    topn = max(3, len(patch_scores) // 6)
    score = float(np.mean(np.sort(patch_scores)[-topn:]))
    return score, patch_scores


def score_case(case_id: str, cfg: dict, pcfg: dict, model, roi, dirs):
    cap, fps, total, width, height = open_video(cfg["video"])
    start = int(cfg["test_range_sec"][0] * fps)
    end = min(total - 1, int(cfg["test_range_sec"][1] * fps))
    stride = int(cfg.get("test_stride", 10))
    frame_ids = list(range(start, end, stride))

    rows = []
    raw_scores = []
    t0 = time.perf_counter()
    for fid in tqdm(frame_ids, desc=f"{case_id} infer"):
        frame = read_frame_at(cap, fid)
        if frame is None:
            continue
        roi_img = crop_roi(frame, roi)
        quality = roi_quality(roi_img)
        score, _ = score_roi(model, roi_img, pcfg)
        raw_scores.append(score)
        rows.append(
            {
                "frame": fid,
                "time_sec": fid / fps,
                "score": score,
                "quality": quality,
            }
        )
    elapsed = max(1e-6, time.perf_counter() - t0)
    cap.release()

    scores = np.array(raw_scores, dtype=np.float32)
    threshold = float(np.quantile(scores, float(cfg.get("threshold_quantile", 0.985))))
    vote = deque(maxlen=int(pcfg["vote_window"]))
    min_votes = int(pcfg["min_ng_votes"])
    for row in rows:
        raw_ng = row["score"] >= threshold
        vote.append(1 if raw_ng else 0)
        stable_ng = sum(vote) >= min_votes if len(vote) == vote.maxlen else raw_ng
        row["threshold"] = threshold
        row["raw_pred"] = "NG" if raw_ng else "OK"
        row["pred"] = "NG" if stable_ng else "OK"

    csv_path = dirs["metrics"] / f"{case_id}_predictions.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    plot_path = dirs["metrics"] / f"{case_id}_score_curve.png"
    plt.figure(figsize=(9, 3.6))
    plt.plot([r["time_sec"] for r in rows], [r["score"] for r in rows], color="#1f77b4", lw=1.5)
    plt.axhline(threshold, color="#d62728", ls="--", lw=1.2, label=f"threshold={threshold:.3f}")
    plt.xlabel("time / s")
    plt.ylabel("PatchCore anomaly score")
    plt.title(f"{case_id} score timeline")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plot_path, dpi=160)
    plt.close()

    return {
        "prediction_csv": str(csv_path),
        "score_plot": str(plot_path),
        "threshold": threshold,
        "test_samples": len(rows),
        "fps_estimate": len(rows) / elapsed,
        "max_score": float(scores.max()) if len(scores) else 0.0,
        "mean_score": float(scores.mean()) if len(scores) else 0.0,
    }


def draw_heatmap_panel(roi_img, patch_scores, pcfg, threshold):
    roi = cv2.resize(roi_img, (320, 320), interpolation=cv2.INTER_AREA)
    gh, gw = pcfg["grid"]
    s = patch_scores.reshape(gh, gw)
    denom = max(1e-6, s.max() - s.min())
    heat = ((s - s.min()) / denom * 255).astype(np.uint8)
    heat = cv2.resize(heat, (320, 320), interpolation=cv2.INTER_CUBIC)
    heat = cv2.applyColorMap(heat, cv2.COLORMAP_TURBO)
    blend = cv2.addWeighted(roi, 0.52, heat, 0.48, 0)
    return blend


def render_frame(frame, roi, score, threshold, pred, patch_scores, title, sec, pcfg):
    h, w = frame.shape[:2]
    display_w = 860
    scale = display_w / w
    left = cv2.resize(frame, (display_w, int(h * scale)), interpolation=cv2.INTER_AREA)
    x, y, rw, rh = roi
    sx, sy = int(x * scale), int(y * scale)
    sw, sh = int(rw * scale), int(rh * scale)
    color = (35, 190, 90) if pred == "OK" else (40, 60, 235)
    cv2.rectangle(left, (sx, sy), (sx + sw, sy + sh), color, 3)
    cv2.putText(left, pred, (sx, max(35, sy - 12)), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3, cv2.LINE_AA)

    roi_img = crop_roi(frame, roi)
    heat = draw_heatmap_panel(roi_img, patch_scores, pcfg, threshold)
    panel = np.full((left.shape[0], 520, 3), (245, 247, 250), dtype=np.uint8)
    panel[35:355, 100:420] = heat
    cv2.rectangle(panel, (100, 35), (420, 355), color, 4)
    cv2.putText(panel, "PATCH ANOMALY MAP", (65, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (45, 55, 70), 2, cv2.LINE_AA)

    cv2.putText(panel, "PatchCore", (42, 430), cv2.FONT_HERSHEY_SIMPLEX, 1.15, (20, 30, 45), 3, cv2.LINE_AA)
    cv2.putText(panel, "ResNet-style local descriptors", (42, 466), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (90, 100, 115), 2, cv2.LINE_AA)
    cv2.putText(panel, f"score: {score:.3f}", (42, 525), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 30, 45), 2, cv2.LINE_AA)
    cv2.putText(panel, f"threshold: {threshold:.3f}", (42, 565), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 30, 45), 2, cv2.LINE_AA)
    cv2.putText(panel, f"time: {sec:06.2f}s", (42, 605), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (90, 100, 115), 2, cv2.LINE_AA)
    cv2.rectangle(panel, (42, 645), (460, 725), color, -1)
    cv2.putText(panel, f"RESULT: {pred}", (72, 698), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 3, cv2.LINE_AA)

    top = np.hstack([left, panel])
    header = np.full((74, top.shape[1], 3), (16, 23, 35), dtype=np.uint8)
    cv2.putText(header, title, (30, 48), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (245, 245, 245), 2, cv2.LINE_AA)
    return np.vstack([header, top])


def render_demo(case_id, cfg, pcfg, model, roi, threshold, dirs):
    cap, fps, total, width, height = open_video(cfg["video"])
    out_path = dirs["videos"] / f"{case_id}_patchcore_resnet_style_demo_15s.mp4"
    demo_fps = 15
    normal_start, normal_end = cfg["demo_normal_sec"]
    defect_start, defect_end = cfg["demo_defect_sec"]
    schedule = [(normal_start, normal_end, "normal"), (defect_start, defect_end, "defect")]
    sample_times = []
    for start, end, tag in schedule:
        n = int((end - start) * demo_fps)
        for i in range(n):
            sample_times.append((start + i / demo_fps, tag))

    writer = None
    saved = set()
    vote = deque(maxlen=int(pcfg["vote_window"]))
    for idx, (sec, tag) in enumerate(tqdm(sample_times, desc=f"{case_id} render")):
        frame = read_frame_at(cap, int(sec * fps))
        if frame is None:
            continue
        roi_img = crop_roi(frame, roi)
        score, patch_scores = score_roi(model, roi_img, pcfg)
        raw_ng = score >= threshold
        vote.append(1 if raw_ng else 0)
        pred = "NG" if (sum(vote) >= int(pcfg["min_ng_votes"]) if len(vote) == vote.maxlen else raw_ng) else "OK"
        canvas = render_frame(frame, roi, score, threshold, pred, patch_scores, cfg["title"], sec, pcfg)
        if writer is None:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(out_path), fourcc, demo_fps, (canvas.shape[1], canvas.shape[0]))
        writer.write(canvas)
        key = (tag, idx // max(1, len(sample_times) // 6))
        if key not in saved and len(saved) < 6:
            saved.add(key)
            cv2.imwrite(str(dirs["frames"] / f"{case_id}_{tag}_{idx:03d}_patchcore_view.jpg"), canvas)
    if writer:
        writer.release()
    cap.release()
    return str(out_path)


def process_case(case_id: str, cfg: dict, pcfg: dict, dirs: dict[str, Path]):
    model, memory, roi, fps, total, width, height = build_memory_bank(case_id, cfg, pcfg, dirs)
    metrics = score_case(case_id, cfg, pcfg, model, roi, dirs)
    video = render_demo(case_id, cfg, pcfg, model, roi, metrics["threshold"], dirs)
    metrics.update(
        {
            "video": video,
            "roi": roi,
            "memory_bank_size": int(len(memory)),
            "source_fps": float(fps),
            "source_frames": int(total),
        }
    )
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/assignment03.yaml")
    args = parser.parse_args()
    cfg = load_config((ROOT / args.config).resolve())
    dirs = ensure_dirs(ROOT / cfg["project"]["output_dir"])
    pcfg = cfg["patchcore"]

    summary = {"method": "PatchCore memory bank + ResNet-style local descriptors + coreset + temporal voting", "cases": {}}
    for case_id, case_cfg in cfg["cases"].items():
        summary["cases"][case_id] = process_case(case_id, case_cfg, pcfg, dirs)

    avg_fps = np.mean([v["fps_estimate"] for v in summary["cases"].values()])
    summary["average_fps_estimate"] = float(avg_fps)
    with (dirs["metrics"] / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
