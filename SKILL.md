---
name: summer-tech-talkcut
description: 科技风口播视频的粗剪 + 包装 + 剪映分轨草稿导出。用户给一条 AI 科普 / AI 教程 / 科技资讯类的口播原片，要求剪辑、粗剪、包装、加字幕、配画面、出成片或出剪映工程时使用。产出：粗剪、校对字幕、按语义配画面（官方素材 / 真实 B-roll / 流程图）的 1080p 成片，以及可在剪映里继续改美颜、字幕、音效的分轨草稿（口播、人声、包装、字幕、音效、音乐）。
---

# Summer Tech TalkCut｜科技科普口播剪辑

一条口播原片 → 粗剪 → 校字幕 → 分镜 → 找素材 → 逐帧渲染包装 → 混音 → 风险扫描 → 成片 →（可选）剪映分轨草稿。

整个包装由一个 HTML/CSS 页面逐帧渲染（Playwright 截图 → ffmpeg），每条视频只需要写一个 `comp.js`（字幕 + 分镜）。引擎、组件、渲染、混音、剪映导出都在 `scripts/` 里，不要重写。

## 开始前必读

| 文件 | 什么时候读 |
|---|---|
| [references/rules.md](references/rules.md) | **每次都读**。剪辑规则：粗剪、字幕、美颜、选画面三原则、动效、版式、音频 |
| [references/boundaries.md](references/boundaries.md) | **每次都读**。边界与拒绝项：哪些画面手法禁止、哪些请求要拒绝、事实与授权的底线 |
| [references/storyboard-api.md](references/storyboard-api.md) | 写 `comp.js` 前读：场景、分屏、浮层、截图卡、官方素材卡、注释、流程图、音效点 |
| [references/visual-system.md](references/visual-system.md) | 改样式时读 |
| [references/jianying-export.md](references/jianying-export.md) | 用户要剪映工程时读：**需要哪些功能和资源**、怎么导出、已知差异 |
| [references/qa-checklist.md](references/qa-checklist.md) | 交付前逐条过 |
| [references/pitfalls.md](references/pitfalls.md) | 出问题时查：踩过的坑和原因 |

## 流程

脚本路径相对本 skill 目录，`<P>` 为项目目录。

0. **环境**：`python3 scripts/check_env.py <P>`。如果共享库没装，先运行一次 `python3 scripts/setup.py`（字体、默认配乐音效、剪映设置，**整台机器只需一次**）。缺什么按提示补；剪映相关是可选项。
1. **建项目**：`python3 scripts/init_project.py <P> <原片>`。项目里只放这条视频自己的东西；字体、配乐音效、B-roll 都从共享库 `~/.tech-talking-head-edit/` 读，**不要复制进项目**。
2. **转写**：`python3 scripts/roughcut.py transcribe <P>`，打印带编号的句子。自检失败（逐字时间错位）就停下排查，不要往下做。
3. **粗剪**：通读转写稿，把要保留的区间写进 `<P>/keep.json`。同一句录了多遍时，只留最后完整的一遍；去掉口误、"重来"、和现场人员的沟通。然后执行 `roughcut.py render <P>` 和 `roughcut.py verify <P>`，**复核转写里不能再有重复和半截话**。
4. **校字幕**：对照复核转写，把 `SUBS` 写进 `comp.js`。产品名、人名、英文术语最常错，**联网查证**再改。拿不准的按原音保留，并列给用户确认。
5. **分镜**：按语义段落分场景（不要逐句切）。每段先判断属于新闻信息、抽象概念还是流程规则，再选画面（rules.md §4）。
6. **找素材**：
   - 官方素材：`imgs.py` 下载官方演示视频和产品图，优先使用；多款产品并列时用 `app_icon.py` 下载官方 App 图标。
   - 截图：`shot.py text` 先读正文，再用 `shot.py shot` 截原句。只用来证明"确实存在"。
   - B-roll：`stock.py search`，看联系表，再 `pick` 下载（存进共享库，按 id 去重，下次直接复用）。
   - 音频：默认配乐音效 setup 时已下载；项目自定义了 audio.json 才需要 `fetch_audio.py <P>` 补缺。
7. **预处理**：`python3 scripts/engine/prep.py <P>`，做口播美颜调色和素材抽帧。
8. **预览**：`render.py <P> still <秒...>`，读 `work/stills/sheet_*.jpg` 联系表，逐场景检查（qa-checklist.md）。改 `comp.js`，再出图，直到干净。
9. **成片**：
   ```
   python3 scripts/engine/render.py <P> cues
   python3 scripts/engine/mix.py <P>
   python3 scripts/engine/render.py <P> video 0 <时长> <P>/work/v.mp4 5
   ffmpeg -i <P>/work/v.mp4 -i <P>/work/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart <P>/output/<名>.mp4
   ```
   成片完成后，每 3 秒抽一帧拼成联系表，通看一遍再交付。
10. **风险扫描**：`render.py <P> text` 导出字幕和画面文字，再跑 `scan.py <P>`。BLOCK 必须清零；REVIEW 逐条写出判断。截图和官方素材里的文字要人工看。
11. **交付说明**：写 `<P>/output/交付说明.md`，内容包括：粗剪去掉了什么、字幕改了什么、待确认项、口播事实核实表、素材与截图来源、授权情况、扫描结果。
12. **剪映草稿**（用户要剪映工程时）：先按 [jianying-export.md](references/jianying-export.md) 确认资源齐全，再依次执行：
    1. `render.py overlay`
    2. `render.py akeys`
    3. `stems.py`
    4. `export_aroll.py`
    5. `jianying.py`

## 硬规则摘要（细节见 references）

- **先粗剪再包装**。原片只读，不修改、不删除。
- **字幕**：得意黑 + 黑色半透明底条，一屏一句，按实际口播。
- **美颜**：轻度，有效果但不假。
- **选画面三原则**：
  - 新闻、产品信息：用官方演示视频、产品图，配中文注释。截图只用来证明"存在"。
  - 抽象概念：用真实 B-roll。
  - 流程、规则、结构：用流程图。
- **禁止**：
  - 对错框 + 打勾打叉 + 删除线。
  - 把口播原话装进框里。
  - 用英文长段落截图来解释概念。
  - 截图带网址。
  - 用空白页截图。
  - 截图里出现最高级或"首个"表述。
- **事实**：产品、功能、价格、日期都要联网核实，并写出处。核实不了的不上画面，在交付说明里标出。
- **每个场景过一遍**：去掉这个画面，观众会少看到什么？答不上来就换。

## 什么时候停下来问用户

- 转写自检失败，或者粗剪后发现整段内容缺失。
- 口播里的事实核实不了，或者和官方信息冲突（例如产品名、价格）。
- 需要用到的素材授权不明。
- 扫描结果有 BLOCK，而且命中的是口播原话（只能改口播，或者由用户判断）。
- 用户要剪映工程，但缺外壳草稿、字体或磁盘空间。

## 剪映草稿硬规则

- **人声必须是独立的「人声」音频轨**，口播视频静音。不要让剪映从视频素材里取原声：避免剪映对脚本生成的视频素材读取音轨不稳定（见 jianying-export.md 踩坑 1）。
- 交付前逐条过 qa-checklist.md 的「剪映草稿」：人声轨、1920×1080 画布、字幕底条（check_flag 16）。
- **默认在现有草稿上返修**，避免产生多个版本；若用户要求保留版本或另建版本，按其要求执行。只改素材内容时，原地替换同名素材文件，剪映开着也行；草稿结构变了（字幕、轨道、画布、关键帧）时，用 `jianying.py <P> <第一版名>` 原地重写（自动备份，不用退剪映，只要那个草稿没打开着）。用户在剪映里手动改过草稿时，先问再重写。

## 共享库（装一次，所有项目共用）

`$TTHE_HOME`（默认 `~/.tech-talking-head-edit`）下有四样：
- `config.json`：全局默认配置，项目 `project.json` 里只写和它不同的项
- `fonts/`：字幕字体
- `audio/`：配乐、音效
- `stock/`：B-roll

想放外接盘就设环境变量 `TTHE_HOME`。项目的 `work/` 是中间文件（帧序列等，较大），交付后可以整个删除。
