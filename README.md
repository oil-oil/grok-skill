<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="grok：把 Codex 任务交给本机 Grok CLI">
</p>

<h1 align="center">grok</h1>

把前端实现、UI 优化、代码评审和图片生成任务委托给本机 Grok CLI 的 Codex Skill。

它提供一个轻量 wrapper，负责传递工作区和入口文件、恢复会话、保存流式日志，并把 Grok 的结果整理成 Markdown 报告。

## 能做什么

- 委托 HTML、CSS、React 和用户可见 UI 的实现与优化。
- 让 Grok 直接检查和修改指定工作区。
- 用 `--file` 提供少量入口文件，不必把源码粘贴进提示词。
- 保存会话 ID、运行日志、stderr 和最终报告，支持后续继续执行。
- 支持 `image_gen`、`image_edit` 和透明背景后处理。
- 兼容 Grok 1.0.0：wrapper 的 `--check` 只写入提示词，不会把不存在的原生参数传给 Grok CLI。

## 前置条件

- macOS 或 Linux。
- 已安装并可正常执行的 `grok` 命令。
- Python 3。
- 只有使用 `cutout.py` 时才需要 Pillow。

先确认本机 Grok 可用：

```bash
grok --version
```

## 安装

使用 Skills CLI：

```bash
npx skills add oil-oil/grok
```

也可以让 Agent 安装：

```text
安装这个 Skill：https://github.com/oil-oil/grok
```

## 使用

在 Codex 中明确调用：

```text
使用 $grok 优化这个项目的设置页前端，保持现有行为，并检查移动端布局。
```

直接运行 wrapper：

```bash
~/.codex/skills/grok/scripts/ask_grok.sh "优化设置页前端并保持现有行为" \
  --workspace /path/to/project \
  --file src/pages/Settings.tsx \
  --file src/styles/tokens.css
```

wrapper 输出：

```text
session_id=<id>
output_path=<markdown report>
elapsed=<seconds>s
```

继续已有会话：

```bash
~/.codex/skills/grok/scripts/ask_grok.sh "继续收紧移动端布局" \
  --workspace /path/to/project \
  --session <session_id>
```

## 常用参数

| 参数 | 作用 |
| --- | --- |
| `--workspace <path>` | 指定目标工作目录 |
| `--file <path>` | 添加入口文件，可重复使用 |
| `--session <id>` | 恢复已有 Grok 会话 |
| `--model <id>` | 覆盖模型 |
| `--reasoning <effort>` | 设置推理强度 |
| `--read-only` | 使用 plan 权限模式并禁止写入 |
| `--check` | 在提示词中要求运行相关检查，不传给 Grok CLI |
| `--no-subagents` | 禁止 Grok 创建子代理 |

## 图片任务

生成图片时，在提示词里要求 Grok 调用 `image_gen`；编辑已有图片时使用 `image_edit`。始终提供绝对输出路径。

需要移除纯色背景时：

```bash
python3 -m pip install Pillow
python3 ~/.codex/skills/grok/scripts/cutout.py raw.png final.png
```

## 安全说明

- 默认写入模式会向 Grok 使用 `bypassPermissions`，只在可信工作区和明确任务中使用。
- 纯分析任务使用 `--read-only`。
- wrapper 不会自动安装 Grok，也不会自动登录。
- 提交或发布 Grok 修改前，应由调用方检查 diff 并运行必要测试。

## 仓库结构

```text
skills/grok/
├── SKILL.md
├── agents/openai.yaml
├── assets/grok-icon.svg
└── scripts/
    ├── ask_grok.sh
    ├── run_grok.py
    └── cutout.py
```

## 说明

这是社区维护的非官方 Skill，与 xAI 没有隶属或背书关系。Grok 名称及相关商标归其权利人所有。

SVG 图标来自 [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Grok-icon.svg)，采用 CC0 公共领域贡献许可。

## License

MIT
