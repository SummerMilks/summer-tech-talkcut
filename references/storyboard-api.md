# 分镜 API（comp.js）

`comp.js` 在 `work/stage.html` 里加载，可以直接用 `scripts/engine/lib.js` 里的全部函数。时间单位都是**粗剪时间轴上的秒**。完整示例见 `templates/comp.example.js`。

## 基础

| 名称 | 说明 |
|---|---|
| `SUBS = [[起, 止, '字幕'], ...]` | 字幕数组，最后调用 `subtitles(SUBS)` |
| `END` | 片长，片尾淡出和进度条会用到 |
| `h(html)` | 用 HTML 字符串创建元素 |
| `C.at(el, x, y, style?)` | 绝对定位，坐标是 1920×1080 的像素 |
| `C.kicker(txt)` / `kick(P, txt, at, x, y, out?)` | 小标题，带发光圆点、全大写宽字距（栏目名、来源） |
| `C.title(html, cls?)` | 得意黑大标题，`<span class="hl">` 给渐变强调 |
| `C.chip(txt, icon?, cls?)` / `C.row(icon, txt, sub?)` | 胶囊 / 要点行。**只放口播之外的信息**（产品名、日期、数值、流程节点） |
| `icon(name)` | 线性图标：memory tool zap calendar bell target plane lock users cloud cpu check x msg thumb star plus pause gift chart file ticket book folder server spark bot loop box sliders layers key |
| `A('assets/...')` | 项目素材的 file:// 路径 |
| `prog(t, t0, dur, ease)` / `ease.*` / `clamp` / `lerp` | 动画工具 |

## 口播镜头

```js
AKEYS.push({ t: 0, x: 0, s: 1.0, d: 0 });      // 起始
AKEYS.push({ t: 0.2, s: 1.06, d: 2.6 });       // 极慢推近
AKEYS.push({ t: 32.18, s: 1.14, d: 0 });       // 关键句硬切推镜（d=0）
```

`split()` 会自动加让位关键帧，不用手写。

## 场景类型

```js
// 全屏场景：盖住口播。bg 用 clips_map 里的素材名；bgs 可以多段硬切；enter/exit: zoom | glitch | wipe | fade | flash
scene(t0, t1, { bg: 'net', dim: .4, blur: 0, tint: 'cool'|'light', grid: true, enter: 'zoom', exit: 'zoom', bgOffset: 0 }, S => {
  S.add(el, at, 'rise'|'drop'|'left'|'right'|'pop'|'blur'|'scale'|'fade', outAt?, din?, dout?);
  S.on(t => { /* 每帧自定义 */ });
});
scene(t0, t1, { bgs: [['airport', 52.84, 0], ['gym', 55.3, 0]] }, S => {...});   // 多段背景

// 分屏：人让到另一侧（±330px），panel 宽 820，内容宽度控制在 740 以内
split(t0, t1, 'left'|'right', P => { kick(P, '来源 · 产品', at); P.add(...); });

// 口播浮层：不切画面
overlay(t0, t1, '', O => { O.add(...); });
```

## 素材组件

```js
// 官方演示视频 / B-roll 卡（clip 为 clips_map 里的名字；第二个参数让 clip 的第 0 秒对准时间轴上的这一刻；rate 是速率）
vidCard('muse_japan', 65.10 - 11 / 1.5, 1.5, 420, 878, { r: 36, fit: 'cover', pos: '50% 0%' });
// 静态官方产品图
picCard(A('assets/official/dots_feedback.png'), 740, 416, { at, fit: 'cover', pos: '50% 50%', bg: '#fff' });
// 中文注释气泡：翻译 / 解释画面里正在发生的事（who 写说话方或来源；cls:'me' 是用户一侧的蓝色气泡）
note('“酒店附近有条 5 公里跑步路线，<b>把晨跑加进训练计划</b>？”', { who: 'MUSE', w: 820 });
// 网页截图卡（只用来证明存在；不显示网址）
addShot(P, 'openai_pro', x, y, { at, w: 1000, crop: [x, y, w, h], focus: true, hl: 高亮时刻, zoom: 1.08, box: [x, y, w, h], out });
```

- 卡片元素在 `S.add` 之外还要 `S.on(t => card.tick(t))`，才有缓推效果（`addShot` 已经自动处理）。
- 截图的 `box` 用 1440×900 视口坐标，`shot.py` 截图时会自动记录。也可以手动传 `box` 来覆盖。
- `focus: true` 表示以高亮框为中心裁出一块 16:10 的区域，字会更大。

## 音效与转场

```js
cue(t, 'whoosh'|'whoosh_soft'|'glitch'|'swipe'|'hit'|'pop'|'tick'|'impact'|'riser'|'bass'|'click'|'send'|'receive'|'typing'|'close'|'notify'|'counter'|'lock', gainDb);
flash(t, strength);   // 闪白
```

`scene()` 和 `split()` 会自动给转场配音效。名字和音频文件的对应关系写在 `audio.json`。

## 常用画面模式（来自真实项目）

| 口播内容 | 画面 |
|---|---|
| "X、Y、Z 接连发布" | 全屏，三张真实产品画面（官方宣传片截帧 / 产品图）依次弹入，下方标产品名和发布日期 |
| "它不是 A，而是 B"（概念定位） | 分层结构图：模型层 → 应用层 → 工作方式，当前层发光、其他层压暗 |
| "它由 A、B、C 构成" | 中心辐射图：核心节点 + 三个卫星卡，描线依次连到核心 |
| 讲一个使用例子 | 官方演示视频（手机竖屏卡）+ 右侧中文注释逐条出现，时间对齐口播 |
| "先自己做，需要你决定时再问你" | 官方演示里的"允许 / 拒绝"弹窗 + 注释 |
| 价格 | 官方价格表截图 + 高亮那一行 + 中文标注 |
| 章节页「这几款怎么选」 | 大标题 + 一排产品官方 App 图标（`app_icon.py`），依次弹入 |
| 总结怎么选 | 决策树：需求 → 两个分支，「托管成品」后面挂产品官方图标 |
| 金句 / 号召 | 真实 B-roll 蒙太奇，不加字 |
| 结尾提问 | 分屏放三格真实 B-roll（对应三个选项）+ 评论气泡图标 |

## 时间对齐技巧

- 演示视频先逐秒拼成联系表：`ffmpeg -i x.mp4 -vf "fps=1,scale=240:-2,tile=10x4"`。找到和口播语义对应的那几秒，播放速率 = 片段长 ÷ 场景长，一般 1.5–2.5。
- 注释气泡的出现时间对齐**口播说到那个意思的时刻**（从 SUBS 里查），而不是演示视频里出现那句话的时刻。
