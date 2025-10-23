import os, math, glob
import numpy as np
import cv2
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .utils import (
    read_timeline, open_bg_capture, read_bg_frame, list_png,
    ensure_bgra, soft_feather, color_match, load_frame_index
)

@dataclass
class CanvasSpec:
    width: int = 1280
    height: int = 720

@dataclass
class RuleParams:
    scale_base: float = 1.0
    scale_per_bbox: float = 0.80
    rot_gain_yaw: float = 0.9
    rot_gain_roll: float = 1.0
    transl_gain: float = 1.0

@dataclass
class BlendParams:
    feather_px: int = 5
    alpha_bias: float = 1.0
    color_match: bool = True
    color_match_strength: float = 0.5

@dataclass
class SyncParams:
    demo_fps: int = 25
    strict_bg_sync: bool = True
    bg_fps: int = 25
    bg_start_ms: int = 0

def _norm_to_px(v, size):
    # if value <= 1, treat as normalized; else assume pixels
    return int(round(v * size)) if v <= 1.0 else int(round(v))

def solve_transform_rule(bbox: Dict, pose: Dict, canvas: CanvasSpec, r: RuleParams):
    # bbox may be normalized or pixels
    x = _norm_to_px(bbox["x"], canvas.width)
    y = _norm_to_px(bbox["y"], canvas.height)
    w = _norm_to_px(bbox["w"], canvas.width)
    h = _norm_to_px(bbox["h"], canvas.height)

    scale = r.scale_base * ((h / canvas.height) ** r.scale_per_bbox)
    rot = pose.get("roll", 0.0) * r.rot_gain_roll + pose.get("yaw", 0.0) * r.rot_gain_yaw * 0.25
    tx = (x + w * 0.5 - canvas.width * 0.5) * r.transl_gain
    ty = (y + h * 0.5 - canvas.height * 0.5) * r.transl_gain
    return scale, rot, (tx, ty)

def affine_from_params(scale: float, rot_deg: float, txy: Tuple[float, float], src_wh: Tuple[int,int], canvas: CanvasSpec):
    sw, sh = src_wh
    cx, cy = sw * 0.5, sh * 0.5
    M = cv2.getRotationMatrix2D((cx, cy), rot_deg, scale)
    M[:,2] += np.array([canvas.width*0.5 - cx + txy[0], canvas.height*0.5 - cy + txy[1]])
    return M

def composite_frame(bg_bgr, fg_bgra, M, blend: BlendParams):
    H, W = bg_bgr.shape[:2]
    warped = cv2.warpAffine(fg_bgra, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
    fg_bgr = warped[:,:,:3]
    alpha = warped[:,:,3]
    if blend.feather_px > 0:
        alpha = soft_feather(alpha, blend.feather_px)
    alpha = np.clip(alpha.astype(np.float32) * blend.alpha_bias / 255.0, 0.0, 1.0)

    # color match within mask region (simple)
    if blend.color_match and alpha.mean() > 0.01:
        mask3 = np.dstack([alpha]*3)
        ref = (mask3*bg_bgr + (1.0-mask3)*bg_bgr).astype(np.uint8)
        fg_bgr = color_match(fg_bgr, ref, blend.color_match_strength, enabled=True)

    out = (alpha[...,None]*fg_bgr + (1.0-alpha[...,None])*bg_bgr).astype(np.uint8)
    return out

def run(POSE_TIMELINE_JSON: str,
        FG_DIR: Optional[str],
        FG_INDEX_CSV: Optional[str],
        BG_VIDEO: str,
        OUT_DIR: str,
        canvas: CanvasSpec,
        sync: SyncParams,
        rule: RuleParams,
        blend: BlendParams,
        mode: str = "rule"):
    os.makedirs(OUT_DIR, exist_ok=True)
    out_mp4 = os.path.join(OUT_DIR, "m3_5_composite.mp4")
    log_csv = os.path.join(OUT_DIR, "m3_5_composite.log.csv")

    tl = read_timeline(POSE_TIMELINE_JSON)
    frames = tl["frames"] if isinstance(tl, dict) and "frames" in tl else tl  # allow array form

    cap = open_bg_capture(BG_VIDEO)
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), sync.demo_fps, (canvas.width, canvas.height))

    fg_index = load_frame_index(FG_INDEX_CSV) if FG_INDEX_CSV else None
    fg_files = list_png(FG_DIR) if (FG_DIR and os.path.isdir(FG_DIR)) else []
    use_dir = len(fg_files) > 0
    fidx = 0

    import pandas as pd
    rows = []

    for i, item in enumerate(frames):
        # Strict t_ms → BG frame sync
        t_ms = item.get("t_ms", int(i * 1000 / sync.demo_fps))
        if sync.strict_bg_sync:
            bg_idx = int(round((t_ms - sync.bg_start_ms) * sync.bg_fps / 1000.0))
            bg_idx = max(0, bg_idx)
            cap.set(cv2.CAP_PROP_POS_FRAMES, bg_idx)
        bg = read_bg_frame(cap, (canvas.width, canvas.height))
        if bg is None:
            break

        # Select FG frame
        fg_img = None
        if fg_index is not None:
            # exact or nearest
            if t_ms in fg_index:
                fp = fg_index[t_ms]
            else:
                nearest = min(fg_index.keys(), key=lambda k: abs(int(k)-int(t_ms)))
                fp = fg_index[nearest]
            fg_img = cv2.imread(fp, cv2.IMREAD_UNCHANGED)
        elif use_dir:
            if fidx >= len(fg_files):
                fidx = len(fg_files)-1
            fg_img = cv2.imread(fg_files[fidx], cv2.IMREAD_UNCHANGED); fidx += 1
        else:
            raise FileNotFoundError("No FG frames available (FG_DIR or FG_INDEX_CSV required).")

        if fg_img is None:
            raise FileNotFoundError("Failed to read FG frame.")

        if fg_img.ndim == 3 and fg_img.shape[2] == 3:
            fg_bgra = ensure_bgra(fg_img)
        else:
            fg_bgra = fg_img

        bbox = item.get("bbox", {"x":0.4,"y":0.3,"w":0.2,"h":0.3})
        pose = {k: item.get(k, 0.0) for k in ("yaw","pitch","roll")}
        scale, rot, txy = solve_transform_rule(bbox, pose, canvas, rule)
        M = affine_from_params(scale, rot, txy, (fg_bgra.shape[1], fg_bgra.shape[0]), canvas)

        comp = composite_frame(bg, fg_bgra, M, blend)
        vw.write(comp)

        rows.append({"frame": i, "t_ms": t_ms, "scale": scale, "rot": rot, "tx": txy[0], "ty": txy[1]})

    cap.release(); vw.release()
    pd.DataFrame(rows).to_csv(log_csv, index=False)
    return out_mp4, log_csv
