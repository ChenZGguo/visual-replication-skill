# Visual Replication Skill

一个跨平台、与具体 Agent 无关的视觉复刻 skill，用于复刻 UI、动效设计、动画、截图、Figma 设计稿、参考视频和视觉交互。

核心循环：

1. 分析参考素材。
2. 实现初版。
3. 运行真实应用。
4. 捕获实际输出。
5. 对比参考与实际输出。
6. 修复影响最大的差异。
7. 重新渲染并再次对比。
8. 只有存在验证证据后才完成。

## 支持平台

| 平台 | 安装方式 | 自动触发 | Hook |
|---|---|---|---|
| **Codex** | `git clone` 到 `~/.codex/skills/` | 通过 `SKILL.md` 描述触发 | `.codex/hooks.json` Stop Hook |
| **Claude Code** | 通过 `.claude-plugin/plugin.json` | Plugin/skill 系统 | 手动或由 skill 调用 |
| **Cursor** | 复制 `.cursorrules` 和脚本到项目 | 每个项目加载 `.cursorrules` | 无 |
| **Codewiz** | `git clone` 到 `~/.config/codewiz/skills/` | 通过 `SKILL.md` 描述触发 | 手动检查脚本 |

## 项目级文件

如果想让某个项目使用此 skill，把这些文件复制到项目根目录：

```text
AGENTS.md
config.json
scripts/
hooks/
.cursorrules
.codex/hooks.json
```

然后创建 `references/` 目录，把参考截图或视频放进去。

## 全局安装

### Codex

```bash
git clone https://github.com/ChenZGguo/visual-replication-skill.git ~/.codex/skills/visual-replication
```

还需要在项目根目录运行：

```bash
~/.codex/skills/visual-replication/install.sh init --platform codex
```

也可以手动复制 `AGENTS.md`、`config.json`、`scripts/`、`hooks/` 和 `.codex/hooks.json` 到项目根目录。

### Claude Code

从本地目录安装插件：

```bash
/plugin install /path/to/visual-replication-skill
```

也可以发布到 Claude Code 插件市场。

### Cursor

Cursor 没有全局 skill 系统。需要复制这些内容到每个项目：

```text
.cursorrules
scripts/
hooks/
references/
subagents/
config.json
```

### Codewiz

```bash
git clone https://github.com/ChenZGguo/visual-replication-skill.git ~/.config/codewiz/skills/visual-replication
```

还需要在项目根目录运行：

```bash
~/.config/codewiz/skills/visual-replication/install.sh init --platform codewiz
```

也可以手动复制 `AGENTS.md`、`config.json`、`scripts/` 和 `hooks/` 到项目根目录。

## 使用方式

### 静态 UI 参考

捕获已实现页面：

```bash
npx tsx scripts/capture-page.ts --url http://localhost:3000 --output artifacts/actual.png --viewport 1440x900
```

与参考图对比：

```bash
python3 scripts/compare-images.py \
  --reference references/reference.png \
  --actual artifacts/actual.png \
  --output-dir artifacts/diff \
  --report artifacts/visual-report.json
```

静态界面需要检查：布局、尺寸、间距、对齐、字体、字号、字重、行高、颜色、圆角、阴影、模糊，以及桌面和移动端响应式表现。

### 动效 / 视频参考

实现前必须先把参考归类为一个主策略：

| 策略 | 适用场景 | 典型输出 |
|---|---|---|
| 生成式视频 | 写实人物、自然场景、复杂相机/光照/材质、模型生成风格 | MP4、MOV、WebM、GIF、图像序列 |
| Lottie / 矢量关键帧动画 | Logo、图标、加载动画、UI 微交互、路径 reveal、mask、形态 morph、短循环 | Lottie JSON、dotLottie |
| 程序化动画 | 确定性数学、粒子、物理、数据、Canvas、SVG、WebGL、Three.js、p5.js、GSAP、shader、交互 | Web app、Canvas、SVG、WebGL、录制视频 |

动效复刻必须先完成分析门槛：

1. 按参考素材原始帧率抽取全部帧。
2. 基于完整帧序列分析动效，不得只看采样帧、稀疏截图或关键帧。
3. 向用户描述 agent 理解的动效：语义复述、视觉状态、关键对象、时间线、运动节奏、形态过渡和衔接连续性。
4. 得到用户明确认可后，才能开始代码复刻。
5. 复杂动效先拆阶段，建立 reference phase map，再逐阶段复刻并整合。

抽取参考视频全部帧：

```bash
ffmpeg -i "<reference-video>" -vsync 0 artifacts/reference-frames/frame_%06d.png
```

如果有 `watch` skill，可作为补充概览和字幕提取工具：

```bash
python3 ~/.codex/skills/watch/scripts/watch.py "<reference-video>" --out-dir artifacts/reference-frames
```

注意：`watch` 输出的自动缩放帧只能作为概览；动效语义、阶段拆分和过渡分析必须以全部帧为准。

Lottie 任务可优先使用 Text-to-Lottie：

```bash
npx skills add diffusionstudio/lottie
```

然后让编码 agent 使用 `text-to-lottie` 生成 Lottie 动画。

捕获实现动画的帧：

```bash
npx tsx scripts/capture-animation.ts --url http://localhost:3000 --output-dir artifacts/frames --duration-ms 3000 --fps 10
```

对比两个视频：

```bash
python3 scripts/compare-video.py \
  --reference references/reference.mp4 \
  --actual artifacts/actual.mp4 \
  --output-dir artifacts/diff \
  --report artifacts/visual-report.json \
  --threshold 0.965 \
  --motion-threshold 0.93
```

视频对比会同时检查帧相似度和逐帧运动相似度。因此不能只靠静帧判断，还要检查时序、速度、缓动、加速、减速、阶段 handoff、形态连续性和循环接缝。

### Lottie / 矢量动效质量门

复刻 Lottie、SVG 或矢量关键帧动画时，需要额外检查：

- 运动语义：元素身份、动作顺序、移动方向、视觉因果必须与参考一致。
- 阶段拆分：每个 phase 的起止时间、可见元素、活跃变换和 handoff 点要清晰。
- handoff invariant：A -> B 变换中，中心、边界框、scale、rotation、opacity、轮廓、层级和速度应连续，除非参考中存在明确切断、遮挡或闪白。
- stutter check：检查 transition 附近是否有重复位置、重复 hold、关键帧簇、微停顿、回退或速度重置。
- 形态过渡：形态到形态、阶段到阶段的衔接是否自然，是主要验收标准。
- 字体和渲染：尽早确定字体/轮廓/降级方案，检查字重、间距、边缘质量和抗锯齿。
- 回归检查：每次修复后检查旧问题是否回归，是否新增卡顿、瞬移、artifact、字体漂移或 frame-patching 快捷修补。

### 完成前检查

没有原生 Stop Hook 的平台，需要手动运行检查脚本：

```bash
python3 hooks/visual_stop_check.py
```

最终回复必须包含：执行过的验证命令、迭代次数、剩余已知差异，以及对比输出路径。

## 依赖

- Node.js + `npx`，用于 TypeScript 脚本。
- Playwright 和浏览器二进制文件：`npm install -D playwright` 和 `npx playwright install chromium`，或项目本地等价安装。
- `tsx`，用于运行 TypeScript 脚本：`npm install -D tsx`，或使用 `npx tsx`。
- Python 3。
- Pillow：`python3 -m pip install pillow`。
- OpenCV + NumPy，用于视频对比：`python3 -m pip install opencv-python numpy`。
- `ffmpeg`，用于视频全量抽帧。
- `watch` skill，用于视频参考分析，非必需但推荐。

## 许可证

MIT
