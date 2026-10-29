# 08 · 自研 2D 引擎（路线 A）

> 目标：用 C 写一个够用的 2D 引擎，把 Godot 游戏逐个重写过来。**不做通用引擎**，只做这四类游戏需要的东西。

## 1. 四类游戏的适配结论

| 类型 | 适配度 | 关键约束 | 设计规则 |
|---|---|---|---|
| 解谜 / 推箱子 / 棋盘 | ★★★★★ | 几乎无 | 一格一动，带 100 ms 动画；整屏静态时零功耗 |
| 卡牌 / 战棋 | ★★★★★ | 无 | 卡面翻转变换用"两帧替换"，不要做 3D 翻转 |
| 文字冒险 / 视觉小说 | ★★★★★ | 中文字库 | 局部刷新只刷文字区；对话逐字显示要限速 |
| 平台跳跃 / 横版动作 | ★★☆☆☆ | **拖影** | 见下 |

### 平台跳跃为什么只有两星

用 `tools/preview/epd_smear_sim.py` 算出来的实际观感：

![拖影预览](img/sim_zoom.png)

左边是目标帧，右边是真正显示出来的样子（4 帧剂量、30 fps、90 px/s）。三件事发生了：

1. **前后边缘变灰**：运动方向的拖尾长约 `速度(px/帧) × 剂量(帧)`；
2. **小特征消失**：16×16 角色的眼睛只有 3 px，移动时一直是灰的——**小于 4 px 的细节在运动中不存在**；
3. **静态元素完全清晰**：只要不动，就是纯 1bit，非常锐利。

**平台跳跃要做的改造**：
- 角色 ≥ 24×24，细节 ≥ 4 px；
- 水平速度 ≤ 4 px/帧（120 px/s）；
- **不要平滑卷轴**：用"整屏切换"（一屏一屏地走），或者摄像机延迟 1 屏；
- 跳跃轨迹用少量离散帧（离地 → 上升 → 顶点 → 下落），不要 60 Hz 连续插值；
- 背景必须完全静态（视差滚动会整屏拖影）。

## 2. 引擎结构

```
app/
├── main.c            初始化、主循环、场景切换
├── gfx/
│   ├── fb.c          1bpp 帧缓冲（400x300 = 15 KB）
│   ├── blit.c        sprite / tile / rect / 文字
│   ├── text.c        位图字库（ASCII + GB2312 子集）
│   └── dirty.c       脏矩形 → 行范围
├── core/
│   ├── entity.c      实体池
│   ├── scene.c       场景栈
│   ├── input.c       按键 + 边沿检测 + 连发
│   ├── anim.c        帧动画
│   ├── save.c        二进制存档
│   └── audio.c       PWM 方波/噪声
├── games/            每个游戏一个目录
└── assets/           打包后的资源（flash / SD）
```

### 内存预算（全部放内部 SRAM 也够）

| 项 | 大小 | 位置 |
|---|---|---|
| front / back 帧缓冲 | 2 × 15 KB | SRAM |
| 背景缓存（静态层预渲染） | 15 KB | SRAM |
| 实体池（64 个 × 32 B） | 2 KB | SRAM |
| 位图字库（ASCII + 3755 汉字 16×16） | ~130 KB | Flash（只读映射） |
| 图块/精灵 | 按需 | Flash / PSRAM |

**15 KB 的帧缓冲意味着整屏拷贝只要 ~15 µs 量级**，CPU 完全不是瓶颈——瓶颈永远是面板。

### 主循环

```c
for (;;) {
    input_poll();                       // 60 Hz
    scene_update(dt);                   // 逻辑 60 Hz
    if (frame_due()) {                  // 显示 20–30 Hz
        scene_draw(back_fb);            // 只画脏区
        dirty_t d = dirty_diff(front_fb, back_fb);
        epd_present(back_fb, d);        // 异步，返回即继续算
        swap(front_fb, back_fb);
    }
}
```

## 3. 关键 API（草案）

```c
/* 帧缓冲 */
typedef struct { uint8_t *buf; int w, h, stride; } fb_t;
void fb_clear(fb_t *fb, int white);
void fb_pixel(fb_t *fb, int x, int y, int white);
void fb_rect(fb_t *fb, int x, int y, int w, int h, int white);
void fb_hline(fb_t *fb, int x, int y, int len, int white);

/* 精灵：1bpp + 透明掩码（两块位平面，和面板的双平面同构） */
typedef struct {
    int w, h;
    const uint8_t *bits;    // 1 = 白
    const uint8_t *mask;    // 1 = 绘制
} sprite_t;
void fb_sprite(fb_t *fb, const sprite_t *s, int x, int y);

/* 图块层 */
typedef struct { int tw, th; const uint8_t *tiles; uint16_t *map; int mw, mh; } tilemap_t;
void fb_tilemap(fb_t *fb, const tilemap_t *t, int cam_x, int cam_y);

/* 文字 */
void text_draw(fb_t *fb, const char *utf8, int x, int y, int scale);
int  text_width(const char *utf8, int scale);

/* 显示 */
void epd_present(const fb_t *fb, rect_t dirty);   // 异步
void epd_clean(void);                             // 强制全刷（清鬼影）
```

## 4. Godot → C 对照

| Godot | 本引擎 | 备注 |
|---|---|---|
| `Node2D` / `CharacterBody2D` | `entity_t` + 手写 AABB | 不要移植物理引擎 |
| `Sprite2D` | `sprite_t` | 1bpp 图 + 掩码 |
| `AnimatedSprite2D` | `anim_t`（帧表 + 时长） | |
| `TileMap` | `tilemap_t` | 背景层，静态 |
| `Area2D` | 矩形重叠测试 | |
| `Label` / `RichTextLabel` | `text_draw()` | 需要中文字库 |
| `Signal` | 回调函数 / 事件位 | |
| `Autoload` | 全局单例 | |
| `PackedScene` | `scene_t` 表 | |
| `AnimationPlayer` / `Tween` | 手写插值或状态机 | 动画越简单越好 |
| `save/load` | `save.c`（版本号 + CRC） | |

## 5. 资产管线（Python，一次性写好）

```
Godot 导出
   ├─ PNG 图集  ──[quantize.py]──> .spr（1bpp 位平面 + 掩码）
   ├─ TileMap   ──[tmx2bin.py]───> .map（tile 索引数组）
   ├─ TTF 字体  ──[fontgen.py]───> .fnt（16×16 点阵 + 索引）
   └─ WAV 音效  ──[wav2pcm.py]───> .pcm（8 bit 单声道）
                                      ↓
                               assets.bin（LittleFS / SD）
```

- **量化是艺术决策**：阈值量化适合像素画，Bayer 抖动适合照片/渐变（但动起来会"爬行"）；
- **中文字库**：16×16 点阵，GB2312 一级 3755 字约 120 KB，只打包游戏实际用到的字可以再省一半；
- **图集要求**：尺寸按 8 的倍数，透明用独立掩码位平面（和面板同构，blit 时有加速空间）。

## 6. 里程碑（调整后）

| # | 里程碑 | 内容 | 验收 |
|---|---|---|---|
| M0 | 点亮 | 4.2" 全刷 + 单帧 LUT 实测 | 测出真实单帧时间与可用的 SPI 时钟 |
| M1 | 引擎骨架 | 帧缓冲、blit、tilemap、文字、脏矩形；**PC 模拟器**可跑 | 电脑上能跑通 demo 并看到拖影预览 |
| M2 | 硬件掌机 | 屏 + 按键 + 电池 + 外壳 | 掌上可玩 |
| M3 | 第一个游戏 | 推箱子 / 卡牌（静态为主，最容易） | 完整可通关 |
| M4 | 文字量大的游戏 | 视觉小说（字库、存档、局部刷新） | 连续玩 30 分钟不闪 |
| M5 | 平台跳跃 | 按第 1 节的规则重设计 | 手感可接受（不追 60 fps） |

## 7. 第一个游戏的建议

**做推箱子，不要做平台跳跃。** 理由：

- 静态画面 → 几乎不触发拖影，能先把引擎、存档、UI 跑通；
- 每步只有角色和一个箱子变化 → 脏区极小 → 即使 20 fps 也感觉"瞬间响应"；
- 关卡数据是纯文本，改一版关卡不用重新编译资源。

平台跳跃留到 M5，那时你已经知道这块屏的脾气了。
