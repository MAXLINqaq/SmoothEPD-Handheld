# 11 · 开工指南（从零到 M0）

> 这份文档是"回家照着做"的操作清单。每一步都有**验收标准**，卡住了直接看第 5 节排错。
> 目标只有一个：**让屏上出图**。出图之后才谈高刷。

---

## 0. 现在的状态

| 项 | 状态 |
|---|---|
| 已下单 | ESP32-S3-DevKitC-1（N16R8）+ 微雪 1.54" e-Paper Module V2（200×200，SSD1681）+ 随包 8 根公对母排线 |
| 暂不需要 | 4.2" 屏、逻辑分析仪、电池、按键、外壳（全部等 M1 之后） |
| 目标 | **M0：屏能全刷出一张图** |
| 时间 | 装环境 1–2 小时，接线 + 出图 30 分钟 |

---

## 1. 装 ESP-IDF（最耗时的一步，先做）

### 1.1 前置条件

- Windows 10/11，**磁盘剩余 ≥ 10 GB**
- 安装路径**不能有中文、不能有空格**（用 `C:\Espressif` 或 `D:\esp`）
- 装好 [Git for Windows](https://git-scm.com/download/win)

### 1.2 两种装法，选一种

**方式 A：官方安装器（推荐，少踩坑）**

1. 打开 https://dl.espressif.com/dl/esp-idf/ ，下载 **ESP-IDF Installer**（Windows）；
2. 运行，版本选 **v5.4 或 v5.5**；
3. 目标芯片**只勾 `esp32s3`**（省一半下载量）；
4. 安装目录 `C:\Espressif`；
5. 装完开始菜单会出现 **"ESP-IDF PowerShell"** 快捷方式——以后都用它。

**方式 B：命令行**

```powershell
cd C:\
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
git checkout v5.4
.\install.bat esp32s3
.\export.bat
```

### 1.3 验收：环境能用

在 **ESP-IDF PowerShell** 里：

```powershell
idf.py --version
# 期望输出类似：ESP-IDF v5.4.x

python -c "import serial; print('pyserial', serial.__version__)"
```

两条都正常 → 环境 OK。

### 1.4 验收：能编译、能烧录

```powershell
cd C:\
idf.py create-project hello
cd hello
idf.py set-target esp32s3
idf.py build
```

build 成功（第一次 3–5 分钟）后，把板子插到 **`UART` 那个 USB 口**：

```powershell
idf.py -p COM3 flash monitor      # COM3 换成设备管理器里的实际端口
```

- 出现 `Hello world!` 和 `cpu_start` 日志 → **烧录链路通了**；
- 按 `Ctrl+]` 退出监视器。

### 1.5 验收：PSRAM 是 8 MB

```powershell
idf.py menuconfig
# Component config → ESP PSRAM → 勾选 "Support for external, SPI-connected RAM"
# 退出保存，重新 build + flash
```

启动日志里应出现类似 `SPI SRAM: 8MB` / `Found 8MB SPI RAM device`。**只有 2 MB 就是买错型号了**（N16R2 / N8R2）。

---

## 2. 硬件接线

### 2.1 清点

- [ ] 开发板 ×1（排针已焊）
- [ ] 1.54" 模块 ×1（**背面看一眼丝印**：`SSD1681` 还是 `SSD1608`）
- [ ] 公对母排线 8 根（随屏附送）

### 2.2 接线表（**按名字接，不要按位置**）

```
1.54" 模块（丝印从上到下）      ESP32-S3
BUSY  ──────────────────────  GPIO7
RST   ──────────────────────  GPIO8
DC    ──────────────────────  GPIO9
CS    ──────────────────────  GPIO10
CLK   ──────────────────────  GPIO12      （SPI SCK）
DIN   ──────────────────────  GPIO11      （SPI MOSI）
GND   ──────────────────────  GND
VCC   ──────────────────────  3V3         ← 不要接 5V
```

### 2.3 通电前三个检查

1. **BS 跳线在 `0`**（板上丝印：`1 = 3-line SPI`，`0 = 4-line SPI`）。我们要 4 线，必须有 DC 引脚参与。
2. **VCC 接 3V3**，不是 5V。
3. 万用表量模块 `VCC–GND`：**3.3 V**，且没有短路（电阻不是 0 Ω）。

> ⚠️ 接线时**断电操作**，接完再插 USB。热插拔排线容易瞬间打火。

---

## 3. M0：让屏出图

### 3.1 拿官方例程

- 打开 https://www.waveshare.net/wiki/1.54inch_e-Paper_Module
- 下载 **ESP32 例程**（或 Arduino 例程，看你顺手哪个）
- 例程里找到引脚定义（通常叫 `EPD_CS_PIN`、`EPD_DC_PIN`…），改成上表的 GPIO

### 3.2 编译烧录

```powershell
idf.py set-target esp32s3
idf.py build
idf.py -p COM3 flash monitor
```

### 3.3 验收标准

- 屏上出现例程自带的图（天气卡片 / 测试图案）；
- 全刷过程约 1–2 秒，能看到黑白翻转；
- 断电后画面保持（这是墨水屏的特性，不是 bug）。

**出图 = M0 完成。** 这时不要急着改波形，先拍张照记录。

### 3.4 记录三件事（下一步要用）

1. 模块背面丝印的控制器型号（`SSD1681` / `SSD1608`）；
2. 全刷一次大概多少秒（拿手机秒表）；
3. 串口日志里 SPI 时钟是多少（例程里通常写死 4 MHz 或 10 MHz）。

---

## 4. M0 验收清单

- [ ] `idf.py --version` 正常
- [ ] 设备管理器出现 COM 口（插 `UART` 口）
- [ ] `esptool.py --chip esp32s3 chip_id` → `ESP32-S3 (QFN56)`
- [ ] `esptool.py --chip esp32s3 flash_id` → Flash 16384 KB
- [ ] 启动日志显示 PSRAM 8 MB
- [ ] `hello_world` 能打印
- [ ] 屏能全刷出图
- [ ] 记下控制器丝印型号

---

## 5. 排错表

| 现象 | 最可能的原因 | 处理 |
|---|---|---|
| 插上没 COM 口 | 插错口 / 充电线 / 缺驱动 | 换 `UART` 口 → 换数据线 → 装 CH340 或 CP210x 驱动 |
| `Failed to connect` | 没进下载模式 | 按住 **BOOT** → 点 **RST** → 松开 BOOT，再烧 |
| 烧录一半失败 | 波特率太高 | `idf.py -p COM3 -b 115200 flash` |
| 屏全白 / 全黑 | BS 跳线错 / CS、DC 接反 | 检查 BS=0，用万用表对一遍 8 根线 |
| 屏只亮一半 / 发灰 | 供电不足或接触不良 | 换短一点的线；VCC 直接接板子 3V3 |
| 花屏、乱码 | SPI 太快或线太长 | 把 SPI 降到 4 MHz 再试 |
| 一直卡在 BUSY | RST 没接 / BUSY 极性搞反 | 确认 BUSY 是"高=忙"，RST 低有效 |
| 编译报找不到 idf.py | 没在 ESP-IDF 终端里 | 用开始菜单的 "ESP-IDF PowerShell" |

---

## 6. 回家后第一句话（把这个发我）

```
1. idf.py --version 的输出：____
2. 设备管理器的 COM 口：____
3. chip_id / flash_id 的输出：____
4. 屏背面丝印型号：____（最好拍张照）
```

拿到这四条，我就能按你的真实型号写 M0 的驱动骨架（初始化序列 + LUT 装载 + 全刷），再往上做单帧高刷。

---

## 7. 仓库地图

| 想知道什么 | 看哪里 |
|---|---|
| 为什么能高刷 | [01 原理](01-principles.md) |
| 屏/主控/电源怎么选 | [02 硬件选型](02-hardware.md) |
| 固件怎么组织 | [03 软件架构](03-software.md) |
| 还要买什么 | [10 采购清单](10-shopping-list.md) |
| 已定的决策 | [00 决策记录](00-decisions.md) |
| 游戏怎么移植 | [07 Godot 移植](07-godot-port.md) · [08 引擎](08-engine.md) |

## 8. 一句话原则

> **先把"能出图"做到，再谈"刷得快"。** 中间任何一步不对，都不要往下走——墨水屏的问题会互相掩盖。
