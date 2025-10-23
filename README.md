# M3.5 Compositor — revB (M3'対応・Jules/CI対応)

M0が出力した **前景BGRAフレーム** を、**背景動画**に **t_msベース** で合成する軽量コンポジタです。
- **revBのポイント**
  - `M3_TIMELINE_JSON` を **`POSE_TIMELINE_JSON`** に改名（中立化）
  - **正規化bbox/座標(0..1)** を **キャンバス座標へ射影**して利用
  - **`frames.index.csv` (t_ms,path)** による **前景フレームの厳密同期**をサポート
  - **STRICT_BG_SYNC** で **t_ms→背景フレーム** をシーク（`bg_start_ms`, `bg_fps`で制御）

## 1) 依存関係
```bash
pip install -r requirements.txt
```

## 2) 主要入出力
- 入力：
  - **POSE_TIMELINE_JSON**: `t_ms, bbox{x,y,w,h}, yaw,pitch,roll[, cx,cy,scale][, lm]`
    - bbox/座標が **0..1正規化** でも **ピクセル**でもOK（自動判定）
  - **前景フレーム**: BGRA `%08d.png` もしくは `frames.index.csv (t_ms,path)`
  - **背景動画**: MP4（`bg_fps`, `bg_start_ms`で同期）
- 出力：
  - 合成MP4, ログCSV（適用した `scale,rot,tx,ty`）

## 3) すぐ試す（ダミーデータ）
```bash
# ダミー生成 + ルールベース実行
python scripts/demo_colab_like.py
# 生成物: out/m3_5_composite.mp4, out/m3_5_composite.log.csv
```

## 4) 実運用CLI例
```bash
python -m m3_5.cli   --pose_json /path/to/timeline.pose.json   --fg_dir    /path/to/m0_frames   --bg_video  /path/to/bg.mp4   --out_dir   /path/to/out   --mode rule   --strict_bg_sync   --bg_fps 25   --bg_start_ms 0
```

`frames.index.csv` がある場合：
```bash
python -m m3_5.cli   --pose_json /path/to/timeline.pose.json   --fg_index  /path/to/frames.index.csv   --bg_video  /path/to/bg.mp4   --out_dir   /path/to/out
```

## 5) テスト（ローカル/Jules/CI）
- ローカル:
```bash
pytest -q
```
- Jules/CI は `jules/run.sh` / `.github/workflows/ci.yml` を参照。

## 6) 構成
```
m3_5_revB/
  m3_5/
    __init__.py
    compositor.py
    utils.py
    cli.py
    configs/default.yaml
    assets/base/front/front.png (ダミーBGRA)
  scripts/
    demo_colab_like.py
    generate_dummy_timeline.py
  tests/
    smoke_test.py
  jules/
    run.sh
  .github/workflows/
    ci.yml
  requirements.txt
  README.md
  LICENSE
```
