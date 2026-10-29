# Summer Tech TalkCut｜科技科普口播剪辑

Summer Tech TalkCut 是一个面向科技、AI 科普、AI 教程和科技资讯口播视频的剪辑 Skill，可交给支持 Skills 的 AI Agent（如 Claude Code、Codex）使用。

## 这个 Skill 能做什么

把一条口播原片交给 Agent 后，它可以按照 Skill 的流程协助完成剪辑：

1. **粗剪**：用本地语音转写整理口播内容，按静音边界剪掉重录、口误和现场沟通，并复核剪辑结果。
2. **字幕**：根据实际口播生成字幕，校对产品名和术语，并统一字幕样式。
3. **画面包装**：轻度美颜与调色；根据内容选择官方产品画面、真实 B-roll 或流程图，配合卡片、截图、转场、音效和配乐。
4. **交付**：输出 1080p 成片；需要时可另外生成可在剪映中继续编辑的多轨草稿，包含口播、人声、包装、字幕、音效和音乐。

## 怎么用

1. 将 `summer-tech-talkcut` 文件夹放进 AI Agent 支持的 Skills 目录，并确保 Agent 可以读取该 Skill。
2. 将口播原片放在一个项目文件夹中，告诉 Agent 你希望如何剪辑和需要哪些输出。

例如：

> 请用 Summer Tech TalkCut 把这个口播剪成科技科普风格，输出 1080p 成片，并生成可继续编辑的剪映草稿。

Agent 会读取 Skill 的流程和规则，检查环境，处理视频并整理交付结果；如果缺少素材或剪辑决定需要你确认，Agent 会再向你询问。

## 依赖

| 依赖 | 用途 | 安装 |
|---|---|---|
| FFmpeg（需支持 `prores_ks`、`bilateral`、`loudnorm`） | 剪辑、滤镜、编码与混音 | macOS：`brew install ffmpeg` |
| whisper.cpp 与 `ggml-large-v3-turbo-q5_0.bin` 模型 | 本地语音转写 | macOS：`brew install whisper-cpp`；模型放入 `~/.cache/whisper/`，或设置 `WHISPER_MODEL` 指向模型文件 |
| Python 3.10+、Playwright、Chromium | 逐帧渲染包装与网页截图 | `python3 -m pip install playwright && python3 -m playwright install chromium` |

## 限制

- 剪映草稿导出目前只在 macOS 版剪映专业版验证过，其他系统尚未验证。
- 成片流程也尚未在其他操作系统上完成验证。

## 联系方式

如有问题、建议或功能需求，欢迎通过邮箱联系：[whitemoww@gmail.com](mailto:whitemoww@gmail.com)。

## License

MIT
