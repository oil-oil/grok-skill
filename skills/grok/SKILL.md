---
name: grok
description: 将前端实现、UI 优化、编码、评审以及图片生成/编辑任务委托给本机 Grok CLI。仅当用户明确要求使用 Grok、说“用 Grok 做/改/画”“让 Grok 执行”“ask Grok”，或选择 $grok 时调用。优先用于前端和用户可见 UI、HTML/CSS/React、视觉实现以及 Imagine/Imagen 图片任务；不要因为普通编码、前端、设计或图片任务可能适合 Grok 就自动调用。
---

# Grok

把边界明确的执行任务委托给本机 Grok CLI。Grok 4.5 尤其适合前端/UI，也提供 `image_gen` 和 `image_edit` 工具。

## 工作方式

- 委托前先明确目标和硬约束。提供期望结果、必要的产品背景和验收条件，让 Grok 自行检查并编辑工作区。
- 优先把前端实现和可见体验优化交给 Grok，包括 HTML/CSS、React 组件、响应式布局、层级、间距、排版、交互状态和动效。
- 按风险检查 Grok 的改动并运行测试。Grok 负责执行，调用方负责范围、正确性和最终交付。
- 提示词保持聚焦，通常不超过 500 个英文单词或等量中文。不要粘贴文件内容；用 `--file` 传入 1–4 个有效入口文件，wrapper 会把路径作为起始上下文。
- 使用随 skill 提供的 wrapper，不要直接调用 `grok`。wrapper 会保存输出、会话 ID 和转录记录。

## 运行 Grok

macOS/Linux：

```bash
~/.codex/skills/grok/scripts/ask_grok.sh "优化设置页前端并保持现有行为" \
  --workspace /path/to/project \
  --file src/pages/Settings.tsx \
  --file src/styles/tokens.css
```

读取 `output_path` 指向的文件；后续任务保存并复用 `session_id`：

```bash
~/.codex/skills/grok/scripts/ask_grok.sh "继续收紧移动端布局" \
  --workspace /path/to/project \
  --session <session_id>
```

纯分析任务添加 `--read-only`。重要改动需要自检时，可给 wrapper 添加 `--check`：wrapper 只会把检查要求写入提示词，绝不把 `--check` 传给本机 Grok CLI，因为 Grok 1.0.0 不支持该参数。

wrapper 输出：

```text
session_id=<id>
output_path=<markdown report>
elapsed=<seconds>s
```

## 前端流程

1. 检查足够的项目上下文，明确可见目标和不能改变的行为。
2. 用 `--file` 传入目标组件/页面，以及相关样式 token 或相邻 UI 基础组件。
3. 要求 Grok 直接编辑项目。只在必要时说明需保留的行为、断点、无障碍要求和资源/依赖限制。
4. 对重要改动给 wrapper 添加 `--check`，要求 Grok 在结束前运行相关项目检查。
5. 阅读报告、检查 diff，并由调用方运行必要的测试或渲染检查。

用户希望 Grok 自主判断设计时，不要过度规定样式；用户给出的品牌规则和参考文件必须明确传达。

## 生成或编辑图片

用自然语言要求 Grok 调用图片工具：

- 新建图片：调用 `image_gen`，传入 `prompt` 和 `16:9`、`9:16` 或 `1:1` 等 `aspect_ratio`。
- 编辑图片：调用 `image_edit`，传入提示词、源图片路径和可选宽高比。
- Grok 把这组能力称为 Imagine，用户也可能称为 Imagen；提示词中使用真实工具名。

始终提供绝对输出路径，并要求 Grok 把最终文件保存或复制到该路径。Grok 0.2.93 的实测行为是：`image_gen` 先把 JPG 原图放到 `~/.grok/sessions/.../images/`，再转换为指定 PNG；不要假设原始文件已经是 PNG 或位于工作区。

示例：

```bash
~/.codex/skills/grok/scripts/ask_grok.sh \
  "调用 image_gen 生成一张无文字的 16:9 编辑插画，把最终图片保存或转换到 /absolute/path/hero.png，并报告该路径。" \
  --workspace /path/to/project
```

需要透明背景时，先要求纯 `#808080` 背景并保存原图，再执行：

```bash
python3 ~/.codex/skills/grok/scripts/cutout.py raw.png final.png
```

确认最终文件是 RGBA。外观驱动的图像使用图片生成；精确文字、图表、表格和技术图使用 HTML/CSS 或 SVG 构建并进行视觉检查。

## 参数

- `--workspace <path>`：目标工作目录，默认当前目录。
- `--file <path>`：添加起始文件路径，可重复使用。
- `--session <id>`：恢复已有 Grok 会话。
- `--model <id>`：覆盖模型；本机默认当前报告为 `grok-4.5`。
- `--reasoning <effort>`：向 Grok 传入推理强度。
- `--read-only`：使用 plan 权限模式并明确禁止写入。
- `--check`：只在提示词中要求 Grok 运行相关检查，绝不把该参数传给 Grok CLI。
- `--no-subagents`：禁用 Grok 子代理，可与 wrapper 的 `--check` 同时使用。

## 失败处理

- 找不到 `grok` 时，报告本机 CLI 不可用；不要擅自安装或登录。
- 即使任务执行正常，`grok models` 也可能显示“未认证”；以 wrapper 的实际任务执行结果判断可用性。
- 使用 `--check` 时，根据 Grok 报告和真实命令输出判断验证结果；本机 CLI 没有原生 `--check` 模式。
- Grok 可以在 Git 仓库外工作，但仓库内的代码上传和会话恢复质量更好；非 Git 运行可能出现无害的仓库发现警告。
- 失败时读取生成的报告和 stderr 路径；先处理已报告的原因，不要盲目重复运行。
