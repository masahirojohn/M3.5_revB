# Quick demo similar to the Colab flow (no external deps except requirements.txt)
import os, cv2, numpy as np, json
from m3_5.compositor import CanvasSpec, RuleParams, BlendParams, SyncParams, run
from m3_5.utils import list_png

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "out")
ASSETS_FRONT = os.path.join(ROOT, "m3_5", "assets", "base", "front", "front.png")
POSE_JSON = os.path.join(ROOT, "out", "timeline.pose.json")
FG_DIR = os.path.join(ROOT, "out", "fg")
BG = os.path.join(ROOT, "out", "bg.mp4")  # tiny background we synthesize

os.makedirs(OUT, exist_ok=True)
os.makedirs(FG_DIR, exist_ok=True)

# 1) dummy pose timeline
def write_dummy_timeline(path, n_frames=150, fps=25, canvas=(1280,720)):
    W,H = canvas
    frames = []
    for i in range(n_frames):
        t_ms = int(1000 * i / fps)
        cx = 0.5 + 0.15*np.sin(2*np.pi*i/n_frames)
        cy = 0.5 + 0.05*np.sin(4*np.pi*i/n_frames)
        w, h = 0.33, 0.33
        bbox = {"x":cx - w/2, "y":cy - h/2, "w":w, "h":h}
        pose = {"yaw": 15*np.sin(2*np.pi*i/n_frames), "pitch": 0.0, "roll": 5*np.sin(2*np.pi*i/n_frames)}
        frames.append({"t_ms":t_ms, "bbox":bbox, **pose})
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"frames":frames}, f, ensure_ascii=False, indent=2)

# 2) placeholder FG (copy sprite -> per-frame)
def prime_fg(dir_path, n_frames=150, sprite_path=ASSETS_FRONT):
    spr = cv2.imread(sprite_path, cv2.IMREAD_UNCHANGED)
    for i in range(n_frames):
        cv2.imwrite(os.path.join(dir_path, f"{i:08d}.png"), spr)

# 3) tiny BG video
def write_bg(path, n_frames=150, fps=25, canvas=(1280,720)):
    W,H = canvas
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W,H))
    for i in range(n_frames):
        img = np.full((H,W,3), 200, np.uint8)
        cv2.putText(img, f"BG t={i/fps:.2f}s", (30,60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,0,0), 3, cv2.LINE_AA)
        vw.write(img)
    vw.release()

if __name__ == "__main__":
    write_dummy_timeline(POSE_JSON)
    prime_fg(FG_DIR)
    write_bg(BG)

    out_mp4, log_csv = run(
        POSE_TIMELINE_JSON=POSE_JSON,
        FG_DIR=FG_DIR,
        FG_INDEX_CSV=None,
        BG_VIDEO=BG,
        OUT_DIR=OUT,
        canvas=CanvasSpec(1280,720),
        sync=SyncParams(demo_fps=25, strict_bg_sync=True, bg_fps=25, bg_start_ms=0),
        rule=RuleParams(),
        blend=BlendParams(),
        mode="rule"
    )
    print(out_mp4, log_csv)
