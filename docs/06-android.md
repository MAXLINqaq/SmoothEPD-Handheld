# 06 · Android 路线评估

> 回答一个问题：**想在这台设备上跑 Android、装微信读书/京东读书这类 APK，需要什么？值不值得？**

## 1. 结论先行

| 问题 | 答案 |
|---|---|
| ESP32-S3 能跑 Android 吗 | **不能**。无 MMU、512 KB SRAM，Android 最低要求是带 MMU 的 ARMv7/ARM64 应用处理器 |
| 跑 Android 的最低硬件 | 4×Cortex-A35 @1.3 GHz、2 GB RAM、16 GB eMMC、Android 9–11 |
| 舒适配置 | RK3566（4×A55 @1.8 GHz + Mali-G52）、4 GB RAM、Android 11 |
| 难的是性能吗 | **不是**。难的是**显示栈**：Android 输出 RGBA 帧，墨水屏要 4 bit 灰度 + 波形 + 刷新策略 |
| 做出来能有多少帧率 | 全屏刷新 ~100–250 ms（约 4–10 fps），**达不到 30 fps** |
| 推荐 | **不要放进首版**。阅读用"现成 Android 墨水屏"或"Linux + 网页版"，DIY 部分专注高刷掌机 |

## 2. 硬件门槛

Android 的启动和 App 运行对硬件的硬性要求：

| 项 | 最低 | 舒适 | 说明 |
|---|---|---|---|
| CPU | 4×A35 @1.3 GHz | 4×A55 @1.8 GHz | 微信读书的翻页动画吃单核性能 |
| RAM | 2 GB | 4 GB | Android 11 系统本身占 1.2–1.5 GB |
| 存储 | 16 GB eMMC | 32 GB | App + 书库 |
| MMU | **必须** | 必须 | 这是 MCU 与 AP 的分界线 |
| 显示 | 需要能输出 4bit 灰度 / 1bit 的控制器 | 带 EBC 的 SoC | 见下节 |
| 触摸 | 建议有 | 必须 | Android 的交互模型依赖触摸 |

**SoC 候选**

| SoC | 规格 | 价格 | 备注 |
|---|---|---|---|
| RK3326 / PX30 | 4×A35 1.5 GHz | 核心板 ¥80–120 | 老，Android 8.1/9 BSP，够读书但卡 |
| **RK3566** | 4×A55 1.8 GHz + Mali-G52 | 核心板 ¥150–250 | **内置 EBC（E-Book Controller）**，墨水屏 Android 设备的标配 |
| RK3568 | 同 RK3566，接口更多 | ¥200–300 | 同 |
| 全志 H700 / T113 | 4×A53 | ¥60–120 | 无 EBC，要自己搭 EPD 时序，不推荐 |

## 3. 为什么 Android + 墨水屏是个"显示栈"问题

Android 的画面从应用到屏幕要经过：`App → SurfaceFlinger 合成 → HWC → 显示驱动 → 面板`。

墨水屏需要的是完全不同的东西：

1. **格式**：Android 合成出来是 RGBA8888，墨水屏控制器要 4 bit 灰度（Y4）或 1 bit；
2. **波形**：文字、图片、视频需要**不同的 LUT**——这正是本项目在 ESP32 上手工做的事，在 Android 上要变成一个"刷新策略服务"；
3. **局部刷新**：Android 会持续重绘状态栏、光标、动画，如果每次都整屏刷，屏幕会一直闪；需要按区域分类（这块是文字→高质量波形，那块是动画→A2 快刷）；
4. **残影管理**：Android 不知道"直流应力"，需要自己记账并在合适时机全刷（而"合适时机"对每个 App 都不同）。

**这就是 Boox、汉王这些厂商的核心竞争力**——他们的"极速刷新""X 模式"是闭源的自研显示服务，不是 Android 自带的能力。

### 好消息：Rockchip 有硬件 EBC

RK3566/RK3568 内置 **EBC（E-Book Controller）**：

- 8 bit 或 16 bit 数据总线，直接驱动裸屏；
- 硬件查表输出 4 bit 灰度，支持 LUT 装载；
- 配套 TPS65185 类 PMIC 产生高压；
- PineNote（10.3" 1872×1404）就是 RK3566 + EBC，且有社区在写上游 DRM 驱动（Samuel Holland 的 RFC 系列，2022 年起）。

所以"Android 跑在墨水屏上"在硬件层面是**已经被验证的**，问题是软件：上游只有 Linux DRM 驱动，Android 的 HWC/HAL 要自己写（或从厂商 BSP 里挖）。

## 4. 三条路径

### 路径 A · 双机（推荐）

- DIY 设备只做两件事：**高刷游戏 + 无 DRM 的自有书籍**（TXT/EPUB，公版书、自己买的无 DRM 电子书、Calibre 传输）；
- 正版 App 阅读交给一台现成的 Android 墨水屏（Boox Poke 系列 ~¥900，或二手 Kindle 装 KOReader）；
- 成本：多一台设备；收益：**DIY 项目的难度回到"一个人能完成"的范围**。

### 路径 B · Linux + 网页版（无反 APK，但正版）

微信读书、京东读书、掌阅都有**网页版**（`weread.qq.com` 等），账号登录即正版，不需要 APK。

- 硬件：RK3566 核心板 + EBC 驱动（PineNote 的 Linux 方案可直接借鉴）+ 4.7"/6" 屏；
- 软件：最小 Linux + Chromium kiosk 打开网页版；或用 KOReader 读本地书；
- 工作量：3–6 个月（内核驱动 + 根文件系统 + 显示策略）；
- 刷新：100–250 ms，翻页可接受，滚动勉强；
- **风险**：网页版对浏览器版本/字体有要求，Chromium 在 2 GB 内存上比较吃力。

### 路径 C · 自制 Android（研究级）

- 硬件：RK3566 核心板（**必须引出 EBC 引脚**，多数开发板没有）+ EPD 电源板 + 触摸；
- 软件：厂商 Android BSP（非公开）→ EBC 内核驱动 → gralloc Y4 格式 → HWC2 HAL → 刷新策略服务；
- 工作量：**6–12 个月**，且每个 App 都要单独适配；
- 刷新上限：仍达不到 30 fps（Android 合成管线 + 4 bit 灰度的物理限制）；
- 适合：把这件事当毕设/研究生课题，而不是"顺手做一台掌机"。

## 5. 建议

1. **主线不变**：ESP32-S3 高刷掌机（4.2" 验证 → 4.7" 主力），这是你能在 4–5 个月内做出来、并且有技术含量的部分；
2. **正版阅读先用路径 A**：买一台现成 Android 墨水屏，或者用手机；
3. **如果一定要"一台设备"**：走路径 B（Linux + 网页版），但要接受它是**另一个项目**，周期以月计，而且刷新率会从 30 fps 掉到 4–10 fps；
4. **别指望路径 C**：它不会给你 30 fps，只会给你一堆 Android 兼容性问题。

## 6. 如果将来真的做 Android：最小清单

- [ ] RK3566 核心板，**确认 EBC 引脚引出**（找"电子书方案"的板子，或 rk3566-evb2 类）
- [ ] EPD 电源板（TPS65185）+ 屏座
- [ ] 4 GB RAM / 32 GB eMMC
- [ ] 厂商 Android 11 BSP（含 ebc 驱动）
- [ ] 触摸（GT911）
- [ ] 先跑通 `dumpsys SurfaceFlinger` + 一个 Y4 输出的 HWC，再谈 App

## 7. 参考资料

- Rockchip EBC 上游驱动讨论（Samuel Holland，2022）  
  https://lkml.iu.edu/2204.1/08394.html
- PineNote（RK3566 + 10.3" EBC 墨水屏，Linux）  
  https://wiki.pine64.org/wiki/PineNote
- RK3568 墨水屏电子书开源硬件（立创开源广场）  
  https://oshwhub.com/eda_cflrsmlad/rk3568-mo-shui-ping-dian-zi-shu
- pinenotes：RK3566 eink dts 实践  
  https://github.com/foow/pinenotes
