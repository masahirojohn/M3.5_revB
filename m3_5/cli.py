import argparse, os, yaml
from .compositor import CanvasSpec, RuleParams, BlendParams, SyncParams, run

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pose_json", required=True)
    ap.add_argument("--fg_dir", default=None)
    ap.add_argument("--fg_index", default=None)
    ap.add_argument("--bg_video", required=True)
    ap.add_argument("--out_dir", default="out")
    ap.add_argument("--mode", choices=["rule"], default="rule")

    ap.add_argument("--canvas_w", type=int, default=None)
    ap.add_argument("--canvas_h", type=int, default=None)
    ap.add_argument("--strict_bg_sync", action="store_true")
    ap.add_argument("--bg_fps", type=float, default=None)
    ap.add_argument("--bg_start_ms", type=int, default=None)

    ap.add_argument("--feather_px", type=int, default=None)
    ap.add_argument("--alpha_bias", type=float, default=None)
    ap.add_argument("--color_match", action="store_true")
    ap.add_argument("--no-color_match", dest="color_match", action="store_false")
    ap.set_defaults(color_match=None)

    ap.add_argument("--cfg", default=os.path.join(os.path.dirname(__file__), "configs", "default.yaml"))
    args = ap.parse_args()

    with open(args.cfg, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    canvas = CanvasSpec(
        width  = args.canvas_w or cfg["canvas"]["width"],
        height = args.canvas_h or cfg["canvas"]["height"]
    )
    sync = SyncParams(
        demo_fps      = cfg["sync"]["demo_fps"],
        strict_bg_sync= args.strict_bg_sync if args.strict_bg_sync else cfg["sync"]["strict_bg_sync"],
        bg_fps        = args.bg_fps or cfg["sync"]["bg_fps"],
        bg_start_ms   = args.bg_start_ms if args.bg_start_ms is not None else cfg["sync"]["bg_start_ms"]
    )
    blend = BlendParams(
        feather_px = args.feather_px if args.feather_px is not None else cfg["blend"]["feather_px"],
        alpha_bias = args.alpha_bias if args.alpha_bias is not None else cfg["blend"]["alpha_bias"],
        color_match= cfg["blend"]["color_match"] if args.color_match is None else args.color_match,
        color_match_strength = cfg["blend"]["color_match_strength"]
    )
    rule = RuleParams(
        scale_base    = cfg["rule_params"]["scale_base"],
        scale_per_bbox= cfg["rule_params"]["scale_per_bbox"],
        rot_gain_yaw  = cfg["rule_params"]["rot_gain_yaw"],
        rot_gain_roll = cfg["rule_params"]["rot_gain_roll"],
        transl_gain   = cfg["rule_params"]["transl_gain"]
    )

    out_mp4, log_csv = run(
        POSE_TIMELINE_JSON = args.pose_json,
        FG_DIR  = args.fg_dir,
        FG_INDEX_CSV = args.fg_index,
        BG_VIDEO= args.bg_video,
        OUT_DIR = args.out_dir,
        canvas  = canvas,
        sync    = sync,
        rule    = rule,
        blend   = blend,
        mode    = args.mode
    )
    print(f"Saved: {out_mp4}\nLog: {log_csv}")

if __name__ == "__main__":
    main()
