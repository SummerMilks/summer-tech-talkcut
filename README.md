# Summer Tech TalkCut｜科技科普口播剪辑

面向科技、AI 科普、AI 教程和科技资讯口播视频的剪辑 Skill。可对口播原片进行本地语音转写、粗剪、字幕校对、画面包装与素材编排，输出 1080p 成片；需要时可另外生成剪映可编辑的多轨草稿。

## 依赖

| 依赖 | 用途 | 安装 |
|---|---|---|
| FFmpeg（需支持 `prores_ks`、`bilateral`、`loudnorm`） | 剪辑、滤镜、编码与混音 | `brew install ffmpeg` |
| whisper.cpp 与 `ggml-large-v3-turbo-q5_0.bin` 模型 | 本地语音转写 | `brew install whisper-cpp`；模型放入 `~/.cache/whisper/`，或设置 `WHISPER_MODEL` 指向模型文件 |
| Python 3.10+、Playwright、Chromium | 逐帧渲染包装与网页截图 | `pip install playwright && playwright install chromium` |

## 限制

剪映草稿导出目前仅在 macOS 版剪映专业版验证过；其他系统暂未验证。成片流程也尚未在其他操作系统上验证。

## License

MIT
