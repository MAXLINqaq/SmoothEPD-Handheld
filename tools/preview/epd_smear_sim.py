#!/usr/bin/env python3
"""
epd_smear_sim.py — 墨水屏"拖影"预览器

在上硬件之前，先把"400x300 / 1bit / 30fps + 剂量模型"下的画面观感算出来：
目标帧是清晰的 1bit，真正显示出来的是逐像素剂量推进过程中的灰度中间态。

模型（定性，不是面板仿真）：
  charge[c] ∈ [0,1]，0 = 纯黑，1 = 纯白
  目标像素变化 → remaining = budget
  每次扫描（一帧）→ charge += ±1/budget，remaining -= 1
  中途反向 → remaining 重置为 budget（和真实驱动一致：不给"半路"的像素记账）

用法：
  python tools/preview/epd_smear_sim.py --budget 4 --out docs/img
  python tools/preview/epd_smear_sim.py --budget 7 --speed 120
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

W, H = 400, 300


def build_background() -> Image.Image:
    """一张典型的横版场景：地面 + 平台 + 金币 + 边框。1 = 白。"""
    img = Image.new("1", (W, H), 1)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 262, W - 1, H - 1], fill=0)          # 地面
    d.rectangle([36, 200, 124, 207], fill=0)             # 平台 1
    d.rectangle([168, 166, 252, 173], fill=0)            # 平台 2
    d.rectangle([292, 212, 366, 219], fill=0)            # 平台 3
    for cx, cy in ((78, 150), (208, 120), (330, 160)):   # 金币
        d.rectangle([cx - 4, cy - 4, cx + 4, cy + 4], fill=0)
        d.rectangle([cx - 1, cy - 1, cx + 1, cy + 1], fill=1)
    d.rectangle([0, 0, W - 1, 2], fill=0)                # 顶栏
    return img


def draw_player(img: Image.Image, x: int, y: int) -> None:
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + 15, y + 15], fill=0)
    d.rectangle([x + 4, y + 3, x + 7, y + 6], fill=1)    # 眼睛
    d.rectangle([x + 10, y + 3, x + 13, y + 6], fill=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=4, help="每个像素从黑到白需要的帧数")
    ap.add_argument("--fps", type=int, default=30, help="显示帧率")
    ap.add_argument("--logic", type=int, default=60, help="逻辑帧率")
    ap.add_argument("--speed", type=float, default=90.0, help="水平速度 px/s")
    ap.add_argument("--ticks", type=int, default=24, help="模拟多少个显示帧")
    ap.add_argument("--out", default="docs/img")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    bg = build_background()

    charge = np.ones((H, W), dtype=np.float32)        # 初始全白
    goal = np.ones((H, W), dtype=bool)                # 目标：True = 白
    remaining = np.zeros((H, W), dtype=np.int16)

    x = 40.0
    y = 232
    vx = args.speed
    dt_logic = 1.0 / args.logic
    sub = max(1, args.logic // args.fps)

    captured = {}
    pos = {}
    trails = []

    for tick in range(args.ticks):
        for _ in range(sub):
            x += vx * dt_logic
            if x < 20 or x > W - 36:
                vx = -vx
                x = min(max(x, 20), W - 36)
        pos[tick] = int(x)

        frame = bg.copy()
        draw_player(frame, int(x), y)
        target = np.array(frame, dtype=bool)              # True = 白（mode "1"）

        # 目标变化 → 重新给预算
        changed = target != goal
        remaining[changed] = args.budget
        goal[changed] = target[changed]

        # 一次扫描
        drive = remaining > 0
        step = np.where(goal, 1.0, -1.0) / args.budget
        charge = np.clip(charge + np.where(drive, step, 0.0), 0.0, 1.0)
        remaining[drive] -= 1

        mid = np.count_nonzero((charge > 0.02) & (charge < 0.98))
        trails.append(mid)
        if tick in (0, 1, 2, 4, 8, 16):
            captured[tick] = (charge.copy(), target.copy())

    # 单帧输出（2 倍放大，便于看细节）
    for tick, (ch, tg) in captured.items():
        Image.fromarray((ch * 255).astype(np.uint8)).resize(
            (W * 2, H * 2), Image.NEAREST
        ).save(os.path.join(args.out, f"sim_{tick:02d}.png"))

    # 对比图：左 = 目标帧（理想），右 = 实际显示（含拖影）
    rows = sorted(captured.keys())
    pad = 8
    sheet = Image.new("RGB", (W * 2 + pad * 3, (H + pad) * len(rows) + pad), "white")
    for i, tick in enumerate(rows):
        ch, tg = captured[tick]
        ideal = Image.fromarray((tg * 255).astype(np.uint8)).convert("RGB")
        real = Image.fromarray((ch * 255).astype(np.uint8)).convert("RGB")
        yy = pad + i * (H + pad)
        sheet.paste(ideal, (pad, yy))
        sheet.paste(real, (W + pad * 2, yy))
    sheet.save(os.path.join(args.out, "sim_compare.png"))

    # 放大：只看玩家周围，拖影在这里最明显
    zt = 4 if 4 in captured else rows[-1]
    ch, tg = captured[zt]
    px = pos[zt]
    cx0, cy0 = max(0, px - 48), max(0, y - 8)
    cx1, cy1 = min(W, px + 56), min(H, y + 26)
    box = (cx0, cy0, cx1, cy1)
    zoom = Image.new("RGB", ((cx1 - cx0) * 6 * 2 + pad * 3, (cy1 - cy0) * 6 + pad * 2), "white")
    zoom.paste(
        Image.fromarray((tg * 255).astype(np.uint8)).convert("RGB").crop(box).resize(
            ((cx1 - cx0) * 6, (cy1 - cy0) * 6), Image.NEAREST
        ),
        (pad, pad),
    )
    zoom.paste(
        Image.fromarray((ch * 255).astype(np.uint8)).convert("RGB").crop(box).resize(
            ((cx1 - cx0) * 6, (cy1 - cy0) * 6), Image.NEAREST
        ),
        ((cx1 - cx0) * 6 + pad * 2, pad),
    )
    zoom.save(os.path.join(args.out, "sim_zoom.png"))

    print(f"budget={args.budget} fps={args.fps} speed={args.speed:.0f}px/s")
    print(f"半途像素数（拖影面积）：{trails}")
    print(f"输出目录：{os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
