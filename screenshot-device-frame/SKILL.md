---
name: screenshot-device-frame
description: 把手机/平板截图套进 iPhone、iPad、MacBook 机壳，生成 App Store 预览图或社媒配图。当用户要给截图加苹果手机外壳、做带设备的展示图、或需要透明/渐变背景的成品图时使用。
---

# 截图套设备外壳

纯 Python（Pillow + numpy）实现，无需 Ruby / ImageMagick / 无头浏览器。

## 适用场景

- 给截图加 iPhone 外框 → App Store / 小红书 / 公众号配图
- 批量处理一堆截图，统一尺寸和背景
- 需要透明底 PNG、渐变底、或投影效果
- iPad / MacBook 同样支持

## 开工前先问清尺寸和背景（不要直接套默认值）

尺寸和背景定错，整套图都要重做，所以**收到「给截图套壳」这类请求时，先问再跑**，
不要拿 `--out-height 1800` / `--bg #0f172a` 的默认值直接出图。

必问两项：

| 项目 | 问什么 | 常见答案 → 参数 |
|---|---|---|
| 画布尺寸 | 竖版、方形，还是 App Store 上架尺寸？ | 9:16 竖版 → `--canvas 1080x1920`；App Store 6.9" → `--canvas 1290x2796`；方形 → `--aspect 1.0 --out-height 2000` |
| 背景 | 透明底，还是指定背景色 / 渐变？ | 透明 → `--bg transparent`；纯色 → `--bg "#f5f5f7"`；渐变 → `--bg 起始色 --bg2 第二色` |

顺带确认（用户没提就用默认，但要在交付说明里写明）：机型（`-d`）、画布占比（`--device-ratio`）、是否加投影（`--shadow`）。

做法：用 `ask_user_options` 一次性问完，两个 tab 单选、开 `allow_custom_input` 接任意尺寸或色值。

- tab「尺寸」：`1080x1920 竖版(9:16)` / `1290x2796 App Store 6.9"` / `1200x1200 方形` / `先出多尺寸各一版`
- tab「背景」：`透明底 PNG` / `浅色 #f5f5f7` / `深色 #0f172a` / `深蓝渐变 #0b1220→#1d4ed8` / `白色 #ffffff`

例外，不用再问，直接做：

- 用户已经把尺寸和背景说全了（如「1290×2796 透明底」）——照做即可。
- 用户说「随便/你看着办」——用竖版 `1080x1920` + 浅色 `#f5f5f7` + 投影出一张，并在回复里说明用了什么、可随时换。

出图后一句说明实际参数：`尺寸 / 机型 / 背景 / 投影`，方便用户判断是否要改。

## 文件结构

```
scripts/
  frame.py          # 主入口：排版、背景、投影、CLI
  bezel.py          # 机壳素材下载 + 颜色/渐变背景
  holefit.py        # 屏幕挖孔检测 + 圆角蒙版（被 bezel.py import）
  verify.py         # 圆角漏色回归检查（改完代码跑一次）
  fetch_frames.py   # 查远端 / 预下载机壳
  frames/           # 机壳 PNG 缓存，缺失时自动下载
```

`frame.py`、`bezel.py`、`holefit.py` **必须在同一目录**（互相 import 依赖脚本自身所在目录进 `sys.path`）。
调用统一走 `python3 scripts/frame.py`，不要单独移动其中任何一个。

## 快速开始

```bash
# 1. 建环境（一次性）
python3 -m venv ~/.venv-frame
~/.venv-frame/bin/pip install pillow numpy

# 2. 套壳（机壳缺失会自动下载）
~/.venv-frame/bin/python scripts/frame.py shot.png -d 17promax -o out/framed.png
```

## 参数速查

| 参数 | 说明 | 默认 |
|---|---|---|
| `-d, --device` | 机型别名或机壳文件名片段 | `17promax` |
| `-o, --out` | 输出路径，`{name}` 替换为原文件名；以 `/` 结尾则自动命名 | `framed-{name}.png` |
| `--canvas` | 画布尺寸 `WxH`，如 `1290x2796` | 无 |
| `--out-height` | 输出高度（未给 `--canvas` 时） | 1800 |
| `--aspect` | 画布宽高比，`1.0` 正方形，`0.5625` 即 9:16 | 1.0 |
| `--device-ratio` | 机壳占画布高比例 | 0.9 |
| `--device-width` | 直接指定机壳像素宽度（优先于 `--device-ratio`） | 无 |
| `--bg` | 背景色/渐变起始色，`transparent` 为透明 | `#0f172a` |
| `--bg2` | 渐变第二色，给了即为线性渐变 | 无 |
| `--angle` | 渐变角度 | 135 |
| `--bg-image` | 用图片当背景 | 无 |
| `--shadow` | 加投影 | 关 |
| `--shadow-opacity` | 投影不透明度 | 0.45 |
| `--shadow-offset` | 投影偏移像素 | 18 |
| `--offset-x/--offset-y` | 机壳偏移 | 0 |
| `--list` | 列出可用机型别名 | — |

## 常见配方

```bash
# App Store 6.9" 竖版（1290x2796）
python3 scripts/frame.py shot.png -d 17promax --canvas 1290x2796 \
    --bg "#0b1220" --bg2 "#1d4ed8" --shadow -o out/appstore.png

# 方形社媒图，浅色
python3 scripts/frame.py shot.png -d 17 --canvas 1600x1600 --bg "#f5f5f7" --shadow

# 透明底 PNG（自己再叠到海报上）
python3 scripts/frame.py shot.png -d 16pro --bg transparent -o out/trans.png

# 批量：多张同样式
python3 scripts/frame.py shots/*.png -d 17pro --canvas 1290x2796 \
    -o "out/appstore-{name}.png"

# iPad / MacBook
python3 scripts/frame.py shot.png -d ipad --canvas 2064x2752 --bg white
```

## 机壳管理

```bash
python3 scripts/fetch_frames.py --search "iPhone 17"   # 看远端有哪些
python3 scripts/fetch_frames.py --list                 # 列出远端全部
python3 scripts/fetch_frames.py 17promax se            # 按别名下载
python3 scripts/frame.py --list                        # 看本地别名表
```

机壳来自 `fastlane/frameit-frames` 的 gh-pages（版本 pin 在 `scripts/bezel.py` 的 `VER`，避免上游变动）。
远端共 280 个机壳，其中 iPhone 17 系列 11 个。想加新机型：下载 PNG 丢进 `scripts/frames/`，
再在 `bezel.py` 的 `ALIAS` 里加一行；不写别名也能用 `-d "文件名片段"` 模糊匹配。

## 原理

1. **找屏幕挖空区（关键）**：机壳 PNG 里有两块 alpha≈0 区域——机身包围的屏幕挖孔，和机身外轮廓的
   透明边距。如果按「bbox 内所有透明像素」当屏幕，机身外那四个圆角会被一并算进去，
   **方角截图就会从这四个角漏到机身外面**（iPhone 17 Pro Max 实测误判 3090 px）。
   所以 `holefit.py` 对 alpha<16 的像素做 4-连通标记（游程编码 + 并查集），剔除与画布边缘相连的
   外部连通域，只保留被机身包围的那个作为屏幕。结果按 mtime+size 缓存到 `.holes.json`，蒙版存 `.masks/`。
   **`bezel.holes()` 只做转发，不要自己拼 `bbox ∩ 透明` 的矩形蒙版**——旧版本就是退回矩形逻辑，
   导致输出四角漏图。
2. **贴图**：截图按 `cover` 方式等比缩放后居中裁切（不拉伸），填进 bbox。
3. **圆角**：取该连通域自身的 alpha 形状放大 2 倍成软边蒙版，屏幕四角天然跟真机一致的圆角，
   无需手填 radius；蒙版再向外扩 1px（`MaxFilter(3x3)`），同时截图向内溢 2px 垫到边框下面，
   避免边框抗锯齿处漏出背景色细缝。
4. **叠层顺序**：背景（纯色/渐变/图片）→ 投影 → 屏幕 → 机壳。

## 性能

- 基础流程约 1.2 秒/张（1290×2796 输出，掩码已缓存）。
- 某机型首次运行 7~9 秒，时间花在连通域标记和下载机壳上，之后走缓存。
- 投影的高斯模糊在全分辨率跑要 6 秒多，改成 1/4 分辨率模糊再放大后降到 2.1 秒/张，
  质量差异 0.99/255，肉眼不可见。
- 渐变背景在 64×64 上计算再双三次放大，避免逐像素算全图。

## 校验方法

**改完 `bezel.py` / `holefit.py` 必须跑一次回归检查**（红图 + 黑图，统计红色像素落在机身轮廓外的数量）：

```bash
~/.venv-frame/bin/python scripts/verify.py -d 17promax --canvas 1290x2796
# PASS leak=1 px (tol 20) device=17promax
```

PASS 且 leak ≤ 20（抗锯齿残量）才算正常；FAIL 会打印漏色 bbox 和排查提示。
换机型或画布后同样跑一遍，`--shot-size` 可指定假截图尺寸。

## 排错

- **`ModuleNotFoundError: No module named 'holefit'`**：`holefit.py` 没跟 `bezel.py` 放同一目录。
- **`ModuleNotFoundError: No module named 'numpy'`**：`pip install numpy`（旧版只需 Pillow，现已需要 numpy）。
- **截图四角漏到机身外**：`bezel.holes()` 用回了「bbox ∩ 透明」的矩形蒙版。改成
  `c = holefit.cached(fp)` 并返回 `c['b'], c['mask'], Image.open(fp).convert('RGBA')`，
  删掉该目录的 `.holes.json`、`.masks/` 和 `__pycache__`，再跑 `scripts/verify.py` 确认。
- **找不到机壳**：`-d` 写太宽会匹配到多个，会提示候选；加限定词或写全名。
- **下载超时**：`github.com` 在部分网络下会超时，但 `raw.githubusercontent.com` 和 `api.github.com` 可用。
  脚本只走这两个域名，所以不用改；也可手工把 PNG 放进 `scripts/frames/`。
- **屏幕图被裁掉边**：截图比例和屏幕不一致时会 cover 裁切。想完整显示就先把截图按目标比例加边。
- **颜色格式报错**：支持 `#rgb`、`#rrggbb`、`white`/`black`/`transparent`。

## 许可提示

fastlane 本体为 MIT。`frameit-frames` 仓库未声明 SPDX 许可，机壳外观源自 Apple 官方设备图，
用于自用/商店截图一般无碍，商用素材分发前请自行确认授权。

更多背景与备选方案见 `references/sources.md`。
