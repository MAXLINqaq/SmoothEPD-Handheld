# 99 · 参考资料

## 上游开源项目（必读）

| 项目 | 说明 | 链接 |
|---|---|---|
| **SmoothEPD** | 47 fps SSD1681 驱动，CH32H417/CH32V303，含脉冲预算与应力补偿。本项目直接的技术源头 | https://github.com/PinkiePie1/SmoothEPD |
| **InkBoy** | ESP32-S3 + 1.54" 屏跑 Game Boy，30 fps，四灰阶剂量模型。文档 `docs/how-it-works.md` 是全网最好的高刷墨水屏科普 | https://github.com/kuslota/InkBoy |
| **PaperBoy** | Wenting Zhang（Zephray），绕开控制器直接扫描裸屏，17.7 ms/帧（~57 fps） | https://gitlab.com/zephray/paperboy |
| **epdiy** | 裸屏并口驱动 + 16 灰阶波形，支持 ED047TC1 / ED060XC3 / ED078KC1 等，硬件开源 | https://github.com/vroland/epdiy |
| **LilyGO T5** | 4.7" ED047TC1 整板（ESP32 / ESP32-S3），espdiy 已支持 | https://github.com/Xinyuan-LilyGO/LilyGo-EPD47 |

## 数据手册与硬件资料

- **SSD1681** 数据手册（Solomon Systech）——LUT 结构、`0x32` 命令、partial window 寄存器
- **TPS65185**（TI）——EPD 专用 PMIC，VGH/VGL/±15V/VCOM
- **ED047TC1 / ED060XC3 / ED078KC1** 面板规格书——行数、行周期、FPC 引脚定义
- epdiy 硬件页（含各版本原理图、Gerber、BOM）：https://vroland.github.io/epdiy-hardware/
- 面板型号库（含引脚与驱动信息）：https://e-ink-reader.ru/chg_dsp_en.php

## 原理与逆向资料

- Essential Scrap：E-Ink 驱动逆向分析（讲清源极/栅极怎么动）  
  http://essentialscrap.com/eink/index.html
- SpriteMods：用 ESP32 驱动 6" 裸屏的早期尝试  
  http://spritesmods.com/?art=einkdisplay
- Linux sunxi：PocketBook 墨水屏引脚逆向  
  https://linux-sunxi.org/PocketBook_Touch_Lux_3

## 报道与科普

- Adafruit：PaperBoy 达到 60 FPS 像素绘制  
  https://blog.adafruit.com/2026/10/12/paperboy-reaches-60-fps-pixel-draws-without-a-full-refresh/
- The Register：30 fps 灰阶 Game Boy 开源  
  https://www.theregister.com/offbeat/2026/10/15/youtuber-built-30-frame-per-second-grayscale-game-boy-then-open-sourced-it-for-all-e-paper-displays/

## 软件依赖（计划使用）

| 组件 | 用途 | 许可 |
|---|---|---|
| ESP-IDF 5.x | 固件框架 | Apache-2.0 |
| Peanut-GB | Game Boy 模拟器核心 | MIT |
| miniz | EPUB（zip）解压 | MIT |
| stb_truetype（可选） | 矢量字体渲染 | MIT / Public Domain |

## 阅读顺序建议

1. [01 原理](01-principles.md) → 2. InkBoy 的 `how-it-works.md` → 3. SmoothEPD 的 `epd_fast.c`（对照着读，看它怎么把预算和 debt 记在代码里）→ 4. PaperBoy 的 `main/ui.c`（看它怎么做帧调度）
