import os, glob, json
import numpy as np
import pandas as pd
import cv2
import simplejson as sjson

def read_timeline(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return sjson.load(f)

def open_bg_capture(path: str):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Failed to open BG video: {path}")
    return cap

def read_bg_frame(cap, canvas_wh):
    ok, frame = cap.read()
    if not ok:
        return None
    W, H = canvas_wh
    return cv2.resize(frame, (W, H))

def list_png(dir_path: str):
    return sorted(glob.glob(os.path.join(dir_path, "*.png")))

def ensure_bgra(img, alpha=None):
    if img is None:
        return None
    if img.ndim == 3 and img.shape[2] == 4:
        return img
    if alpha is None:
        a = np.full(img.shape[:2], 255, dtype=np.uint8)
    else:
        a = alpha
    return np.dstack([img, a])

def soft_feather(alpha, radius):
    if radius <= 0: return alpha
    k = max(1, 2*radius+1)
    return cv2.GaussianBlur(alpha, (k, k), 0)

def color_stats(img_bgr):
    mean = img_bgr.reshape(-1, 3).mean(axis=0)
    std  = img_bgr.reshape(-1, 3).std(axis=0) + 1e-6
    return mean, std

def color_match(src_bgr, ref_bgr, strength, enabled=True):
    if not enabled or strength <= 0:
        return src_bgr
    sm, ss = color_stats(src_bgr)
    rm, rs = color_stats(ref_bgr)
    norm = (src_bgr - sm) / ss
    matched = norm * rs + rm
    out = (src_bgr * (1-strength) + matched * strength)
    return np.clip(out, 0, 255).astype(np.uint8)

def load_frame_index(csv_path: str):
    if not os.path.exists(csv_path):
        return None
    df = pd.read_csv(csv_path)
    mp = dict(zip(df["t_ms"].astype(int), df["path"].astype(str)))
    return mp
