# Summer Tech TalkCut · 科技科普口播剪辑 Skill

给 AI Agent（Claude Code / Codex 等支持 Skills 的 Agent）用的剪辑 skill：一条科技口播原片，交给它完成以下步骤，每条视频只需要写一个分镜文件。

1. **粗剪**：本地 Whisper 转写，按静音边界切掉重录、口误和现场沟通，再重新转写复核。
2. **字幕**：按实际口播出字幕，联网核对产品名和术语，用得意黑配黑色半透明底条。
3. **包装**：轻度美颜和调色；按语义给画面：
   - 新闻、产品信息：用官方演示视频、产品图，配中文注释。
   - 抽象概念：用真实 B-roll。
   - 流程、规则：用流程图。
   卡片、截图、转场、进度条、音效、配乐都会配上。
4. **风险扫描**：扫描字幕和画面文字里的绝对化用语、承诺性表述和需要标注来源的数据。
5. **剪映分轨草稿**：口播视频、人声、包装、字幕、音效、音乐六轨，画面和成片一致，可以在剪映里继续改美颜、字幕和音效。

> 本工作流将常见剪辑问题整理为可复用的规则。具体项目可按内容和发布要求调整，见 [references/rules.md](references/rules.md) 和 [references/boundaries.md](references/boundaries.md)。

## 怎么用

把本仓库放进 Agent 的 skills 目录，例如 Claude Code 的 `~/.claude/skills/summer-tech-talkcut/`，然后对 Agent 说：

> 这个文件夹里有一条口播，帮我粗剪 + 科技风包装，最后出剪映工程

Agent 会按 [SKILL.md](SKILL.md) 的流程推进。

## 依赖

| 依赖 | 用途 | 安装 |
|---|---|---|
| macOS | 剪映草稿只在 Mac 版验证过。成片流程跨平台，但没有在其他系统上测试过 | — |
| ffmpeg（含 prores_ks、bilateral、loudnorm） | 剪辑、滤镜、编码 | `brew install ffmpeg` |
| whisper.cpp + `ggml-large-v3-turbo-q5_0.bin` | 本地转写 | `brew install whisper-cpp`；模型放到 `~/.cache/whisper/`，或者设置环境变量 `WHISPER_MODEL` |
| Python 3.10+ / playwright / Chromium | 逐帧渲染包装、网页截图 | `pip install playwright && playwright install chromium` |
| Google Chrome（推荐） | 截官网，被反爬拦截的情况更少 | — |
| 得意黑 SmileySans-Oblique.ttf | 字幕字体（OFL） | `scripts/setup.py` 自动下载；也可 `--font` 指向本机已有文件 |
| 剪映专业版 Mac（可选） | 导出剪映工程 | 需要外壳草稿、字库里有得意黑、磁盘空间，详见 [jianying-export.md](references/jianying-export.md) |

运行 `python3 scripts/check_env.py <项目>` 会逐项检查，并告诉你缺什么。

**只装一次**：字体、配乐音效、B-roll、剪映设置都放在共享库 `~/.tech-talking-head-edit/`（可用环境变量 `TTHE_HOME` 改到外接盘），所有项目共用，新项目里不复制、不重复下载。

## 快速开始

```bash
# 整台机器只需一次：字体（自动下载得意黑）、默认配乐音效、可选的剪映设置
python3 scripts/setup.py --jianying-shell <剪映里新建的空草稿文件夹> --media-dir <空间大的盘>

# 每条视频
python3 scripts/init_project.py ~/videos/ep01 ~/videos/raw/ep01.mov
python3 scripts/check_env.py ~/videos/ep01
python3 scripts/roughcut.py transcribe ~/videos/ep01        # 然后写 keep.json
python3 scripts/roughcut.py render ~/videos/ep01 && python3 scripts/roughcut.py verify ~/videos/ep01
# 写 comp.js（字幕 + 分镜），找素材，然后：
python3 scripts/engine/prep.py ~/videos/ep01
python3 scripts/engine/render.py ~/videos/ep01 still 3 10 20 30   # 看联系表
```

后续步骤（成片、扫描、剪映导出）见 [SKILL.md](SKILL.md)。

## 目录

```
SKILL.md                 Agent 入口：流程、硬规则、什么时候问用户
references/              规则、边界与拒绝项、分镜 API、视觉系统、剪映导出、检查清单、踩坑记录
scripts/
  setup.py check_env.py init_project.py roughcut.py
  stock.py fetch_audio.py shot.py imgs.py app_icon.py   素材：Mixkit B-roll / 音频、官网截图、官方产品图与演示视频、官方 App 图标
  engine/  lib.js stage.template.html          逐帧渲染的组件库与页面
           prep.py render.py mix.py stems.py scan.py export_aroll.py jianying.py jydraft.py jy_templates/
templates/               project.json / audio.json / clips_map.json / comp.js 模板
```

## 素材与版权

- 默认 B-roll、配乐和音效从 [Mixkit](https://mixkit.co/license/) 获取。Mixkit 对不同素材类型及单条素材适用不同许可；下载和发布前请逐条确认素材标注为适用于目标用途的许可（视频尤其要区分 Free License 与 Restricted License）。符合相应许可的免费素材通常无需署名，但应遵守各许可条款；脚本会登记素材来源，来源登记不代表已核验许可。
- 官方演示视频、产品图、网页截图属于新闻评论中的引用。使用时保持原貌，在交付说明里列出处，并建议在发布简介里注明来源。是否适用于你的场景，请自行判断。
- 本仓库**不附带**任何视频、音频、字体文件，也不附带剪映外壳草稿（其中含有账号和设备数据）。
- `scripts/engine/jy_templates/` 是剪映草稿 JSON 结构模板；设备标识字段已清空，生成草稿时由本机外壳草稿提供必要元数据。

## 免责

- 风险扫描只是辅助，**不保证能通过平台审核**。
- 剪映草稿格式不是公开接口，剪映升级后可能失效。
- 发布前请自行核实所有事实和授权。

## License

MIT
