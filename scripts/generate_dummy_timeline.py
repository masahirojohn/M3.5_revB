import json, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=150)
    ap.add_argument("--fps", type=int, default=25)
    args = ap.parse_args()

    frames = []
    for i in range(args.frames):
        t_ms = int(1000 * i / args.fps)
        cx = 0.5 + 0.15*math.sin(2*math.pi*i/args.frames)
        cy = 0.5 + 0.05*math.sin(4*math.pi*i/args.frames)
        w, h = 0.33, 0.33
        bbox = {"x":cx - w/2, "y":cy - h/2, "w":w, "h":h}
        yaw = 15*math.sin(2*math.pi*i/args.frames)
        roll= 5*math.sin(2*math.pi*i/args.frames)
        frames.append({"t_ms":t_ms, "bbox":bbox, "yaw":yaw, "pitch":0.0, "roll":roll})
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"frames":frames}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
