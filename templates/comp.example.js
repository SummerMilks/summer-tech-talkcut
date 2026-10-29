// 分镜示例：一条科技口播的字幕 + 画面（每条视频只改这个文件）。时间单位：粗剪时间轴秒。
// 先读 references/rules.md 和 references/storyboard-api.md。
// 选画面三原则：新闻/产品信息 → 官方演示视频、产品图、截图（证明存在）；抽象概念 → 真实 B-roll；流程/结构 → 流程图。
// 禁止：对错框 + 打勾打叉 + 删除线；把口播原话装进框里；英文长段落截图当解释；截图带网址。

// ============ 字幕：按实际口播，校对过同音错字；一屏一句，≤16 字 ============
const SUBS = [
  [0.00, 2.80, '最近有个新概念特别火'],
  [2.80, 5.60, '三家公司接连发布了新产品'],
  [5.60, 9.00, '它们到底是怎么干活的？'],
  [9.00, 12.50, '第一步，它先记住你的目标'],
  [12.50, 15.50, '然后结合你的日程安排'],
  [15.50, 18.50, '在合适的时候主动提醒你'],
  [18.50, 22.00, '欢迎在评论区告诉我'],
];
const END = 22.0;

// ============ 口播基础镜头：整体极慢推近；关键句硬切推镜 ============
AKEYS.push({ t: 0, x: 0, s: 1.0, d: 0 });
AKEYS.push({ t: 0.2, s: 1.06, d: 2.6 });

// 开场主题词（口播上叠字，左侧压暗，不挡脸）
overlay(0.5, 2.7, '', O => {
  O.add(C.at(h(`<div class="shade shade-left" style="width:1920px;height:1080px"></div>`), 0, 0), 0.5, 'fade', 2.4);
  O.add(C.at(C.kicker('AI 新热词'), 120, 400), 0.6, 'left', 2.4);
  O.add(C.at(h('<div class="en glow" style="font-weight:800;font-size:150px;line-height:.98;background:linear-gradient(90deg,#8fe6ff,#b3a6ff);-webkit-background-clip:text;color:transparent">Topic<br>Name</div>'), 110, 450), 0.9, 'blur', 2.4);
  cue(0.85, 'riser', -12);
});

// 新闻信息：三家产品的真实画面 + 发布日期（全屏）。真实项目里换成 assets/official 下的官方产品图 / 截图
scene(2.80, 5.55, { bg: 'net', dim: .35, enter: 'glitch', exit: 'zoom', tint: 'cool' }, S => {
  [['产品 A', '2026.08', 2.9, -4], ['产品 B', '2026.09', 3.6, 0], ['产品 C', '2026.09', 4.3, 4]].forEach(([n, date, at, rot], i) => {
    const w = C.at(h(`<div style="width:540px"></div>`), 110 + i * 590, 300);
    const card = h(`<div class="card" style="position:relative;width:540px;height:330px;display:grid;place-items:center;font-size:40px;color:var(--mute)">产品画面</div>`);
    w.appendChild(card);
    w.appendChild(h(`<div style="display:flex;justify-content:space-between;margin-top:22px"><span class="en" style="font-size:40px;font-weight:800">${n}</span><span style="font-size:26px;color:var(--mute)">${date}</span></div>`));
    w.style.rotate = rot + 'deg';
    S.add(w, at, 'pop'); cue(at, 'impact', -6);
  });
});

// 抽象概念：真实 B-roll（分屏，人让到右边，左侧放素材卡 + 中文注释讲清"画面里在发生什么"）
split(5.60, 8.95, 'left', P => {
  kick(P, '真实场景', 5.7, 70, 170);
  P.add(C.at(vidCard('laptop', 5.6, .9, 740, 416, { bg: '#000' }), 50, 220), 5.7, 'rise');
  P.add(C.at(note('后台一直开着，<b>不用你每次重新交代</b>', { w: 740, who: '注释' }), 50, 670), 6.4, 'rise');
});

// 流程：时间线（节点依次点亮，进度线描过去）
scene(9.00, 18.40, { bg: 'cubes', dim: .35, enter: 'wipe', exit: 'zoom' }, S => {
  S.add(C.at(C.kicker('它会怎么做'), 150, 200), 9.1, 'left');
  const nodes = [['target', '记住目标', 9.2], ['calendar', '结合日程', 12.5], ['bell', '适时提醒', 15.5]];
  const X0 = 360, GAP = 560, Y = 480;
  const line = C.at(h(`<div style="height:4px;border-radius:2px;background:rgba(255,255,255,.14);width:${GAP * 2}px"><i style="display:block;height:100%;border-radius:2px;background:linear-gradient(90deg,var(--cyan),var(--violet));width:0"></i></div>`), X0 + 50, Y + 48);
  S.add(line, 9.2, 'fade');
  const fill = line.querySelector('i');
  S.on(t => { fill.style.width = (clamp((t - 9.2) / (15.5 - 9.2)) * GAP * 2) + 'px'; });
  nodes.forEach(([ic, txt, at], i) => {
    S.add(C.at(h(`<div style="width:100px;text-align:center"><div style="width:100px;height:100px;border-radius:30px;display:grid;place-items:center;font-size:46px;background:linear-gradient(135deg,rgba(76,201,255,.35),rgba(155,140,255,.35));border:1px solid rgba(160,210,255,.5)">${icon(ic)}</div>
        <div style="margin-top:26px;font-size:40px;font-weight:700;white-space:nowrap;transform:translateX(-50%);margin-left:50px;width:max-content">${txt}</div></div>`), X0 + i * GAP, Y), at, 'pop');
    cue(at, 'tick', -6);
  });
});

// 关键句推镜
AKEYS.push({ t: 18.5, s: 1.1, d: 0 });

// 片尾淡出
(() => { const n = h(`<div style="position:absolute;inset:0;background:#000;z-index:95"></div>`); item(END - .6, 1e9, n, t => { n.style.opacity = prog(t, END - .6, .6, ease.inOutCubic); }); })();

// ============ 全局层：章节进度条、字幕、颗粒暗角 ============
(() => {
  const chapters = [['开场', 0, 5.6], ['是什么', 5.6, 18.5], ['互动', 18.5, END]];
  const bar = h(`<div class="prog">${chapters.map(c => `<div class="seg"><div class="bar"><i></i></div><b>${c[0]}</b></div>`).join('')}</div>`);
  const segs = [...bar.querySelectorAll('.seg')];
  item(0, 1e9, bar, t => {
    chapters.forEach(([, a, b], i) => { segs[i].querySelector('i').style.width = (clamp((t - a) / (b - a)) * 100) + '%'; segs[i].classList.toggle('on', t >= a && t < b); });
    bar.style.opacity = clamp(t / .6) * (1 - prog(t, END - .8, .4));
  });
})();
subtitles(SUBS);
finish();
