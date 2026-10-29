# firmware · 固件

本目录存放 ESP-IDF 工程。**目前为空，M0 开始填充。**

## 计划结构

```
firmware/
├── CMakeLists.txt
├── sdkconfig.defaults
├── main/
│   ├── app_main.c
│   ├── display/
│   │   ├── epd_panel.c        # 面板命令、LUT、BUSY
│   │   ├── epd_waveform.c     # 掩码、剂量、应力记账
│   │   └── epd_service.c      # epd_present、三缓冲、调度
│   ├── books/                 # txt / epub / layout
│   ├── emu/gb/                # Peanut-GB 适配
│   ├── ui/
│   ├── drivers/               # sd / audio / power / input
│   └── tools/                 # 测试图、压力测试
├── components/
└── test/
```

## 开始之前

1. 安装 **ESP-IDF 5.x**（推荐用 Espressif IDE 或 `idf.py`）；
2. `idf.py set-target esp32s3`；
3. 先跑通 `hello_world` 与 SPI 回环，再动屏幕。

## 代码约定

- 显示相关代码**禁止**在中断里做长操作；
- 所有对面板的写操作集中到 `epd_panel.c`，便于审计命令集（**绝不下发 OTP 烧写命令**）；
- 波形参数放 `Kconfig`/NVS，可运行时调，不要硬编码；
- 每个 demo 都要能在串口打印"帧时间 / 全刷倒计时 / debt 统计"。

## 待办

- [ ] M0：最小全刷驱动
- [ ] M1：单帧 LUT + 双平面掩码 + 剂量
- [ ] M2：Peanut-GB 集成
- [ ] M3：并口时序 + TPS65185
- [ ] M4：TXT/EPUB 排版
