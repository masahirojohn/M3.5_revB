import os, cv2, numpy as np, json
from m3_5.compositor import CanvasSpec, RuleParams, BlendParams, SyncParams, run

def test_smoke(tmp_path):
    out_dir = tmp_path/"out"; out_dir.mkdir(parents=True, exist_ok=True)
    pose_json = out_dir/"timeline.pose.json"
    bg = out_dir/"bg.mp4"
    fg_dir = out_dir/"fg"; fg_dir.mkdir(parents=True, exist_ok=True)

    # tiny timeline
    frames = []
    for i in range(45):
        t_ms = i*40
        bbox = {"x":0.4, "y":0.3, "w":0.2, "h":0.3}
        frames.append({"t_ms":t_ms, "bbox":bbox, "yaw":0.0, "pitch":0.0, "roll":0.0})
    with open(pose_json, "w", encoding="utf-8") as f:
        json.dump({"frames":frames}, f)

    # fg sprite
    spr = np.zeros((240,240,4), np.uint8)
    cv2.circle(spr, (120,120), 90, (40,180,240,255), -1)
    cv2.imwrite(str(fg_dir/"00000000.png"), spr)
    for i in range(1,45):
        cv2.imwrite(str(fg_dir/f"{i:08d}.png"), spr)

    # bg
    vw = cv2.VideoWriter(str(bg), cv2.VideoWriter_fourcc(*"mp4v"), 25, (1280,720))
    for i in range(45):
        img = np.full((720,1280,3), 220, np.uint8); vw.write(img)
    vw.release()

    out_mp4, log_csv = run(
        POSE_TIMELINE_JSON=str(pose_json),
        FG_DIR=str(fg_dir),
        FG_INDEX_CSV=None,
        BG_VIDEO=str(bg),
        OUT_DIR=str(out_dir),
        canvas=CanvasSpec(1280,720),
        sync=SyncParams(demo_fps=25, strict_bg_sync=True, bg_fps=25, bg_start_ms=0),
        rule=RuleParams(),
        blend=BlendParams(),
        mode="rule"
    )
    assert os.path.exists(out_mp4)
    assert os.path.exists(log_csv)
