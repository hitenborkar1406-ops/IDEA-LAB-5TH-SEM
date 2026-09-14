"""
ml/video_detect.py — YOLOv8 + ByteTrack vehicle detection on a traffic video.

Runs YOLOv8n on every frame, tracks vehicles with ByteTrack (via supervision),
and writes per-frame detection data to ml/video_detections.json.

Usage:
    python ml/video_detect.py --video <path_to_video>

Output (ml/video_detections.json):
    {
      "meta": { total_frames, avg_vehicles_per_frame, fps, ... },
      "frames": [
        {
          "frame_idx": int,
          "timestamp_sec": float,
          "vehicle_count": int,
          "vehicles": [
            { "track_id": int, "bbox": [x1,y1,x2,y2], "class": str, "confidence": float }
          ]
        }
      ]
    }
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    print("ERROR: ultralytics not installed. Run: pip install ultralytics")
    sys.exit(1)

try:
    import supervision as sv
except ImportError:
    print("ERROR: supervision not installed. Run: pip install supervision")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR  = Path(__file__).parent
OUTPUT_FILE = SCRIPT_DIR / "video_detections.json"

# COCO class IDs for vehicles (YOLOv8 COCO weights):
#   2=car  3=motorcycle  5=bus  7=truck
VEHICLE_CLASS_IDS = {2, 3, 5, 7}
CLASS_NAMES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

CONFIDENCE_THRESHOLD = 0.30
PRINT_EVERY          = 50


def run_detection(video_path: str, model_name: str = "yolov8n.pt") -> dict:
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    print(f"\n[DETECT] Loading model: {model_name}")
    model = YOLO(model_name)

    print(f"[DETECT] Opening video: {video_path}")
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps          = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_video  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"[DETECT] Video  : {width}x{height} @ {fps:.2f} fps  (~{total_video} frames)")
    print(f"[DETECT] Output : {OUTPUT_FILE}\n")

    # ByteTrack via supervision (new API in v0.28+)
    try:
        tracker = sv.ByteTrack(frame_rate=int(fps), minimum_matching_threshold=0.8)
    except TypeError:
        tracker = sv.ByteTrack()

    frames_data        = []
    frame_idx          = 0
    total_vehicles_sum = 0
    wall_start         = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp_sec = round(frame_idx / fps, 4)

        # YOLOv8 inference
        results = model(frame, verbose=False, conf=CONFIDENCE_THRESHOLD)[0]
        boxes   = results.boxes

        if boxes is not None and len(boxes):
            xyxy       = boxes.xyxy.cpu().numpy()
            confidence = boxes.conf.cpu().numpy()
            class_ids  = boxes.cls.cpu().numpy().astype(int)
            mask       = np.array([cid in VEHICLE_CLASS_IDS for cid in class_ids])
            xyxy       = xyxy[mask]
            confidence = confidence[mask]
            class_ids  = class_ids[mask]
        else:
            xyxy, confidence, class_ids = (
                np.empty((0, 4)), np.empty((0,)), np.empty((0,), dtype=int)
            )

        detections = sv.Detections(xyxy=xyxy, confidence=confidence, class_id=class_ids)
        tracked    = tracker.update_with_detections(detections)

        vehicle_list = []
        for i in range(len(tracked)):
            tid  = int(tracked.tracker_id[i]) if tracked.tracker_id is not None else -1
            bbox = [round(float(v), 1) for v in tracked.xyxy[i]]
            cid  = int(tracked.class_id[i]) if tracked.class_id is not None else 2
            conf = round(float(tracked.confidence[i]), 3) if tracked.confidence is not None else 0.0
            vehicle_list.append({
                "track_id":   tid,
                "bbox":       bbox,
                "class":      CLASS_NAMES.get(cid, "vehicle"),
                "confidence": conf
            })

        count               = len(vehicle_list)
        total_vehicles_sum += count

        frames_data.append({
            "frame_idx":     frame_idx,
            "timestamp_sec": timestamp_sec,
            "vehicle_count": count,
            "vehicles":      vehicle_list
        })

        if frame_idx % PRINT_EVERY == 0:
            elapsed  = time.time() - wall_start
            fps_proc = frame_idx / elapsed if elapsed > 0 else 0
            print(f"  Frame {frame_idx:5d}/{total_video} | t={timestamp_sec:.2f}s | "
                  f"vehicles={count:3d} | proc_fps={fps_proc:.1f}")

        frame_idx += 1

    cap.release()
    wall_elapsed = time.time() - wall_start

    total_frames_processed = frame_idx
    avg_veh = round(total_vehicles_sum / max(1, total_frames_processed), 2)

    print()
    print("=" * 60)
    print("DETECTION COMPLETE")
    print("=" * 60)
    print(f"  Total frames processed  : {total_frames_processed}")
    print(f"  Average vehicles/frame  : {avg_veh}")
    print(f"  Wall clock time         : {wall_elapsed:.1f}s")
    print(f"  Video duration          : {total_frames_processed/fps:.1f}s")

    output = {
        "meta": {
            "video_path":             str(video_path),
            "model":                  model_name,
            "total_frames":           total_frames_processed,
            "fps":                    fps,
            "duration_sec":           round(total_frames_processed / fps, 2),
            "width":                  width,
            "height":                 height,
            "avg_vehicles_per_frame": avg_veh,
            "vehicle_classes":        list(CLASS_NAMES.values()),
            "confidence_threshold":   CONFIDENCE_THRESHOLD,
        },
        "frames": frames_data
    }

    print(f"\n[DETECT] Writing {OUTPUT_FILE} ...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"))   # compact for speed

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"[DETECT] Done. File size: {size_mb:.2f} MB")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="YOLOv8 + ByteTrack vehicle detection on a traffic video"
    )
    parser.add_argument("--video",  required=True, help="Path to input video file")
    parser.add_argument("--model",  default="yolov8n.pt",
                        choices=["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"],
                        help="YOLOv8 model variant (default: yolov8n.pt)")
    args = parser.parse_args()

    result = run_detection(args.video, args.model)
    meta   = result["meta"]
    print("\n--- FINAL SUMMARY ---")
    print(f"  Frames processed        : {meta['total_frames']}")
    print(f"  Avg vehicles per frame  : {meta['avg_vehicles_per_frame']}")
    print(f"  Output file             : {OUTPUT_FILE}")
    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"  File size               : {size_kb:.1f} KB  ({size_kb/1024:.2f} MB)")
