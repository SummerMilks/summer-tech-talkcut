// 科技口播包装引擎：逐帧确定性渲染（window.seek(帧号) → 截图）。
// 所有动效都由时间 t 计算，不用 CSS transition/animation，保证每帧可复现。
const FPS = 30, W = 1920, H = 1080;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
const ease = {
  linear: t => t,
  outCubic: t => 1 - Math.pow(1 - t, 3),
  inCubic: t => t * t * t,
  inOutCubic: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  outExpo: t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t),
  inExpo: t => t <= 0 ? 0 : Math.pow(2, 10 * t - 10),
  outQuint: t => 1 - Math.pow(1 - t, 5),
  outBack: t => { const c1 = 1.4, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
};
const prog = (t, t0, d, e = ease.outExpo) => e(clamp((t - t0) / d));
// 可复现的伪随机
const rnd = (i, s = 1) => { const x = Math.sin(i * 12.9898 + s * 78.233) * 43758.5453; return x - Math.floor(x); };

function h(html) { const d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstElementChild; }

// ---------- 图标（线性描边，24 视图） ----------
const ICON_PATHS = {
  memory: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  tool: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/>',
  zap: '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
  target: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
  plane: '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>',
  lock: '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  cloud: '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
  cpu: '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  msg: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
  thumb: '<path d="M7 10v12M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/>',
  star: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  pause: '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
  gift: '<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M12 8v13M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7M7.5 8a2.5 2.5 0 0 1 0-5C11 3 12 8 12 8s1-5 4.5-5a2.5 2.5 0 0 1 0 5"/>',
  chart: '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>',
  file: '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
  ticket: '<path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M13 5v2M13 17v2M13 11v2"/>',
  book: '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>',
  folder: '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
  server: '<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><path d="M6 6h.01M6 18h.01"/>',
  spark: '<path d="M12 3l1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2z"/>',
  bot: '<rect x="3" y="8" width="18" height="12" rx="3"/><path d="M12 8V4M8 14h.01M16 14h.01"/><circle cx="12" cy="3" r="1"/>',
  loop: '<path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>',
  box: '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5M12 22V12"/>',
  sliders: '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
  layers: '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5M2 12l10 5 10-5"/>',
  key: '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6M15.5 7.5l3 3L22 7l-3-3"/>',
};
const icon = (name, cls = '') => `<svg class="ico ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICON_PATHS[name] || ''}</svg>`;

// ---------- 时间线 ----------
const ITEMS = [];   // {t0, t1, node, update}
const CUES = [];    // 音效 {t, sfx, gain}
const IMGS = [];    // 需要按帧换图的 <img>：{img, src(t) → url|null}
function cue(t, sfx, gain = 0) { CUES.push({ t: +t.toFixed(3), sfx, gain }); }

function item(t0, t1, node, update, parent) {
  (parent || document.getElementById('stage')).appendChild(node);
  const it = { t0, t1, node, update: update || (() => { }) };
  ITEMS.push(it); return it;
}

// 通用入场/出场：kind = rise | pop | left | right | blur | fade | drop | scale
function anim(node, t, tin, kind = 'rise', tout = null, din = .55, dout = .3) {
  let k = prog(t, tin, din, kind === 'pop' ? ease.outBack : ease.outExpo);
  let o = clamp((t - tin) / Math.min(din, .25));
  let x = 0, y = 0, s = 1, b = 0;
  const r = 1 - k;
  if (kind === 'rise') { y = 46 * r; b = 10 * r; }
  else if (kind === 'drop') { y = -46 * r; b = 10 * r; }
  else if (kind === 'pop') { s = .6 + .4 * k; }
  else if (kind === 'left') { x = -90 * r; b = 12 * r; }
  else if (kind === 'right') { x = 90 * r; b = 12 * r; }
  else if (kind === 'blur') { b = 24 * r; s = 1.06 - .06 * k; }
  else if (kind === 'scale') { s = 1.25 - .25 * k; b = 14 * r; }
  if (tout !== null && t > tout) {
    const q = prog(t, tout, dout, ease.inCubic); o *= 1 - q; b += 12 * q; y -= 20 * q;
  }
  node.style.opacity = o;
  node.style.transform = `translate(${x}px,${y}px) scale(${s})`;
  node.style.filter = b > .05 ? `blur(${b}px)` : '';
  node.style.visibility = o <= 0.001 ? 'hidden' : '';
}

// 逐字打出
function typeText(node, full, t, t0, cps = 14) {
  const n = clamp(Math.floor((t - t0) * cps), 0, full.length);
  node.textContent = full.slice(0, n);
  node.classList.toggle('typing', n < full.length && t >= t0);
}

// ---------- 视频素材（帧序列） ----------
// CLIPS 由 clips.json 提供：name → {dir, n}；rate < 1 为慢放
function seqImg(cls, clip, tStart, rate = 1) {
  const img = document.createElement('img'); img.className = cls;
  IMGS.push({ img, src: t => {
    const c = CLIPS[clip]; if (!c) return null;
    const i = clamp(Math.floor((t - tStart) * FPS * rate), 0, c.n - 1);
    return `${c.dir}/${String(i + 1).padStart(5, '0')}.jpg`;
  } });
  return img;
}

// ---------- 口播主画面 ----------
// AKEYS：[{t, x, s, d}]，d 为过渡时长（0 = 硬切推镜）
let AKEYS = [];
function arollState(t) {
  // 每个关键帧从"当时的实际位置"过渡到目标，连续分屏左右换边也不会跳
  let cur = { x: 0, s: 1 };
  for (let i = 0; i < AKEYS.length; i++) {
    const k = AKEYS[i]; if (k.t > t) break;
    const from = { ...cur }, to = { x: k.x ?? cur.x, s: k.s ?? cur.s };
    const end = i + 1 < AKEYS.length ? Math.min(t, AKEYS[i + 1].t) : t;
    const q = k.d ? prog(end, k.t, k.d, ease.inOutCubic) : 1;
    cur = { x: lerp(from.x, to.x, q), s: lerp(from.s, to.s, q) };
  }
  return cur;
}

// ---------- 场景 ----------
// 全屏场景：盖住口播。enter/exit: zoom | glitch | wipe | fade | flash
function scene(t0, t1, opts, build) {
  const node = h(`<div class="scene"></div>`);
  // 背景：opts.bg 单段；opts.bgs = [[clip, 起始秒, 片内偏移秒]] 多段依次硬切
  const bgs = opts.bgs || (opts.bg ? [[opts.bg, t0, opts.bgOffset || 0]] : []);
  const bgEls = bgs.map(([clip, from, off], i) => {
    const bg = seqImg('bg', clip, from - (off || 0), opts.rate || 1);
    bg.style.filter = `brightness(${opts.dim ?? .42}) saturate(${opts.sat ?? .9})${opts.blur ? ` blur(${opts.blur}px)` : ''}`;
    node.appendChild(bg); return [bg, from, bgs[i + 1] ? bgs[i + 1][1] : 1e9];
  });
  node.appendChild(h(`<div class="scene-tint ${opts.tint || ''}"></div>`));
  if (opts.grid !== false) node.appendChild(h(`<div class="grid"></div>`));
  const inner = h(`<div class="scene-inner"></div>`); node.appendChild(inner);
  const kids = [];
  const S = {
    node: inner, t0, t1,
    add(el, at, kind = 'rise', out = null, din, dout) { inner.appendChild(el); kids.push({ el, at, kind, out, din, dout }); return el; },
    on(fn) { kids.push({ fn }); },
  };
  build && build(S);
  const enter = opts.enter || 'zoom', exit = opts.exit || 'zoom';

  item(t0 - .02, t1 + .4, node, t => {
    let o = 1, s = 1, b = 0, x = 0, clip = '';
    const ki = clamp((t - t0) / .42), ko = clamp((t - t1) / .36);
    if (t < t0 + .45) {
      const e = ease.outExpo(ki);
      if (enter === 'zoom') { o = clamp(ki * 2.5); s = 1.14 - .14 * e; b = 18 * (1 - e); }
      else if (enter === 'fade') { o = ease.outCubic(ki); }
      else if (enter === 'wipe') { clip = `inset(0 0 0 ${(1 - ease.outQuint(ki)) * 100}%)`; }
      else if (enter === 'glitch') { const g = t - t0 < .2; o = clamp(ki * 4); if (g) { x = (rnd(Math.floor(t * FPS)) - .5) * 80; s = 1.04; } }
      else if (enter === 'flash') { o = clamp(ki * 3); s = 1.06 - .06 * e; }
    }
    if (t > t1) {
      const e = ease.inCubic(ko);
      if (exit === 'zoom') { o = 1 - clamp(ko * 1.2); s = 1 + .1 * e; b = 16 * e; }
      else if (exit === 'fade' || exit === 'flash') { o = 1 - ko; }
      else if (exit === 'wipe') { clip = `inset(0 ${ease.inOutCubic(ko) * 100}% 0 0)`; o = ko >= 1 ? 0 : 1; }
      else if (exit === 'glitch') { o = ko > .5 ? 0 : 1; x = (rnd(Math.floor(t * FPS), 3) - .5) * 90; }
      else if (exit === 'cut') { o = 0; }
    }
    node.style.opacity = o; node.style.clipPath = clip;
    node.style.transform = `translateX(${x}px) scale(${s})`;
    node.style.filter = b > .05 ? `blur(${b}px)` : '';
    node.style.visibility = o <= .001 ? 'hidden' : '';
    for (const [bg, a, b] of bgEls) {  // 背景缓推
      bg.style.display = t >= a - .05 && t < b ? '' : 'none';
      bg.style.transform = `scale(${1.04 + .05 * clamp((t - t0) / (t1 - t0 + .4))})`;
    }
    for (const k of kids) {
      if (k.fn) { k.fn(t); continue; }
      anim(k.el, t, k.at, k.kind, k.out, k.din, k.dout);
    }
  });
  // 转场音效 + 闪白
  const sfxIn = { zoom: 'whoosh', glitch: 'glitch', wipe: 'swipe', fade: null, flash: 'hit' }[enter];
  if (sfxIn && !opts.silentIn) cue(t0 - .12, sfxIn, enter === 'glitch' ? -4 : -2);
  if (enter === 'flash' || enter === 'glitch' || opts.flash) flash(t0);
  if (exit === 'zoom' && opts.exitSfx !== false) cue(t1 - .05, 'whoosh_soft', -6);
  return S;
}

// 闪光转场层
function flash(t, strength = .55) {
  const n = h(`<div class="flash"></div>`);
  item(t - .1, t + .35, n, tt => {
    const k = tt < t ? clamp((tt - t + .1) / .1) : 1 - prog(tt, t, .3, ease.outCubic);
    n.style.opacity = k * strength;
  });
}

// 分屏侧栏：口播让到一边，另一侧放玻璃面板。side = 'left'（面板在左，人往右）| 'right'
const SPLIT_X = 330;
function split(t0, t1, side, build) {
  const dir = side === 'left' ? 1 : -1;
  AKEYS.push({ t: t0, x: dir * SPLIT_X, s: 1.0, d: .55 });
  AKEYS.push({ t: t1, x: 0, s: 1.0, d: .45 });
  const shade = h(`<div class="shade shade-${side}"></div>`);
  const panel = h(`<div class="panel panel-${side}"></div>`);
  const kids = [];
  const P = {
    node: panel, t0, t1,
    add(el, at, kind = 'rise', out = null, din, dout) { panel.appendChild(el); kids.push({ el, at, kind, out, din, dout }); return el; },
    on(fn) { kids.push({ fn }); },
  };
  build(P);
  item(t0, t1 + .5, shade, t => {
    const k = prog(t, t0, .55, ease.inOutCubic) * (1 - prog(t, t1, .45, ease.inOutCubic));
    shade.style.opacity = k;
  });
  item(t0, t1 + .5, panel, t => {
    const ki = prog(t, t0 + .1, .6), ko = prog(t, t1 - .05, .35, ease.inCubic);
    panel.style.opacity = clamp(ki * 1.8) * (1 - ko);
    panel.style.transform = `translateX(${-dir * (1 - ki) * 120 + -dir * ko * 60}px)`;
    panel.style.filter = (1 - ki) * 14 + ko * 10 > .05 ? `blur(${(1 - ki) * 14 + ko * 10}px)` : '';
    for (const k of kids) { if (k.fn) { k.fn(t); continue; } anim(k.el, t, k.at, k.kind, k.out, k.din, k.dout); }
  });
  cue(t0, 'swipe', -8);
  return P;
}

// 口播上的浮层（不切画面）
function overlay(t0, t1, cls, build) {
  const node = h(`<div class="ov ${cls}"></div>`);
  const kids = [];
  const O = {
    node, add(el, at, kind = 'rise', out = null, din, dout) { node.appendChild(el); kids.push({ el, at, kind, out, din, dout }); return el; },
    on(fn) { kids.push({ fn }); },
  };
  build(O);
  item(t0, t1 + .4, node, t => {
    node.style.opacity = 1 - prog(t, t1, .3, ease.inCubic);
    for (const k of kids) { if (k.fn) { k.fn(t); continue; } anim(k.el, t, k.at, k.kind, k.out, k.din, k.dout); }
  });
  return O;
}

// ---------- 字幕 ----------
function subtitles(list) {
  const box = h(`<div class="subs"><div class="sub"><span></span></div></div>`);
  const span = box.querySelector('span'), bar = box.querySelector('.sub');
  item(0, 1e9, box, t => {
    const s = list.find(x => t >= x[0] && t < x[1]);
    if (!s) { bar.style.opacity = 0; return; }
    if (span.textContent !== s[2]) span.textContent = s[2];
    const k = prog(t, s[0], .16, ease.outCubic);
    bar.style.opacity = k;
    bar.style.transform = `translateY(${(1 - k) * 8}px)`;
  });
}

// ---------- 胶片颗粒 + 暗角 ----------
function finish() {
  const g = h(`<div class="grain"></div>`);
  item(0, 1e9, g, t => {
    const i = Math.floor(t * FPS) % 7;
    g.style.backgroundPosition = `${Math.floor(rnd(i) * 300)}px ${Math.floor(rnd(i, 2) * 300)}px`;
  });
  item(0, 1e9, h(`<div class="vignette"></div>`));
}

// ---------- 渲染入口 ----------
let AROLL = null;
window.seek = async function (frame) {
  const t = frame / FPS;
  for (const it of ITEMS) {
    const vis = t >= it.t0 && t < it.t1;
    it.node.style.display = vis ? '' : 'none';
    if (vis) it.update(t);
  }
  // 口播
  if (!AKEYS.sorted) { AKEYS.sort((p, q) => p.t - q.t); AKEYS.sorted = true; }
  const a = arollState(t);
  AROLL.style.transform = `translateX(${a.x}px) scale(${a.s})`;
  const loads = [];
  const want = `${CLIPS.aroll.dir}/${String(clamp(frame, 0, CLIPS.aroll.n - 1) + 1).padStart(5, '0')}.jpg`;
  if (!window.OVERLAY && !AROLL.src.endsWith(want)) { AROLL.src = want; loads.push(AROLL.decode().catch(() => { })); }
  for (const m of IMGS) {
    if (!m.img.isConnected || m.img.closest('[style*="display: none"]')) continue;
    const u = m.src(t);
    if (u && !m.img.src.endsWith(u)) { m.img.src = u; loads.push(m.img.decode().catch(() => { })); }
  }
  await Promise.all(loads);
  return true;
};

// ---------- 网页截图卡（新闻/产品信息用真截图） ----------
// SHOTS 由 prep.py 从 assets/screenshots/sources.jsonl 生成：name → {src, url, box}，box 为 1440x900 视口坐标
// opts: w 卡片宽；crop [x,y,w,h] 只显示页面某块；hl 高亮出现时刻；zoom 推近倍数；box 手动覆盖高亮框
function browser(name, o = {}) {
  const s = SHOTS[name]; const w = o.w || 1000;
  const box = o.box || s.box;
  // focus：以高亮框为中心裁一块 16:10 区域，字更大
  // 裁切宽度让高亮段落推近后仍完整在画内
  const fw = o.fw || clamp(box ? box[2] * (o.zoom || 1.08) + 80 : 860, 700, 1440);
  const [cx, cy, cw, ch] = o.crop || (o.focus && box ? [clamp(box[0] + box[2] / 2 - fw / 2, 0, 1440 - fw), clamp(box[1] + box[3] / 2 - fw * .3125, 0, 900 - fw * .625), fw, fw * .625] : [0, 0, 1440, 900]);
  const k = w / cw, H = Math.round(ch * k);
  const node = h(`<div class="browser" style="width:${w}px">
    <div class="bbar"><i></i><i></i><i></i></div>
    <div class="bview" style="height:${H}px"><div class="bpage"><img src="${s.src}" style="width:${1440 * k}px;left:${-cx * k}px;top:${-cy * k}px"></div></div></div>`);
  const page = node.querySelector('.bpage');
  let spot = null, ox = w / 2, oy = H / 2;
  if (box && o.hl != null) {
    const pad = 12, bx = (box[0] - cx) * k - pad, by = (box[1] - cy) * k - pad, bw = box[2] * k + 2 * pad, bh = box[3] * k + 2 * pad;
    spot = h(`<div class="bspot" style="left:${bx}px;top:${by}px;width:${bw}px;height:${bh}px"></div>`);
    spot.dim = h(`<div style="position:absolute;left:${bx}px;top:${by}px;width:${bw}px;height:${bh}px;border-radius:10px"></div>`);
    page.appendChild(spot.dim); page.appendChild(spot); ox = bx + bw / 2; oy = by + bh / 2;
  }
  page.style.transformOrigin = `${ox}px ${oy}px`;
  const t0 = o.at ?? 0;
  node.tick = t => {
    const q = o.hl != null ? prog(t, o.hl, 1.1, ease.inOutCubic) : 0;
    const z = 1 + .03 * clamp((t - t0) / 6) + ((o.zoom || 1.08) - 1) * q;
    page.style.transform = `scale(${z})`;
    if (spot) {
      const a = prog(t, o.hl + .25, .5, ease.outCubic);
      spot.style.opacity = a;
      spot.style.boxShadow = `0 0 30px rgba(76,201,255,${.6 * a})`;
      spot.dim.style.boxShadow = `0 0 0 3000px rgba(4,6,12,${.5 * a})`;
      spot.style.clipPath = `inset(0 ${(1 - a) * 100}% 0 0 round 10px)`;
    }
  };
  return node;
}
// 把截图卡加进场景/分屏：入场 + 每帧推近与高亮
function addShot(S, name, x, y, o) {
  const n = C_at(browser(name, o), x, y);
  S.add(n, o.at, o.kind || 'rise', o.out ?? null, o.din, o.dout);
  S.on(t => n.tick(t));
  if (o.hl != null) cue(o.hl + .25, 'tick', -8);
  return n;
}
const C_at = (el, x, y) => { el.style.left = x + 'px'; el.style.top = y + 'px'; return el; };

// ---------- 官方图片 / 官方演示视频卡 ----------
// 图片卡：src 为相对 stage.html 的路径；fit cover|contain；bg 底色（白底产品图用白）
function picCard(src, w, hh, o = {}) {
  const n = h(`<div class="card" style="width:${w}px;height:${hh}px;border-radius:${o.r ?? 22}px;background:${o.bg || '#0d1018'}">
    <img src="${src}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:${o.fit || 'cover'};object-position:${o.pos || '50% 50%'}"></div>`);
  const img = n.querySelector('img'); const t0 = o.at ?? 0;
  n.tick = t => { img.style.transform = `scale(${1.02 + .04 * clamp((t - t0) / 8)})`; };   // 缓推
  return n;
}
function vidCard(clip, tStart, rate, w, hh, o = {}) {
  const n = h(`<div class="card" style="width:${w}px;height:${hh}px;border-radius:${o.r ?? 22}px;background:${o.bg || '#f4f6fa'}"></div>`);
  const v = seqImg('', clip, tStart, rate); v.style.cssText = `position:absolute;inset:0;width:100%;height:100%;object-fit:${o.fit || 'cover'};object-position:${o.pos || '50% 50%'}`;
  n.appendChild(v); n.tick = () => { };
  return n;
}
// 中文注释气泡：翻译/解释画面里正在发生的事（不是重复口播）
function note(html, o = {}) {
  return h(`<div class="note ${o.cls || ''}" style="width:${o.w || 560}px">${o.who ? `<div class="who">${o.who}</div>` : ''}<div>${html}</div></div>`);
}

// ---------- 常用小部件 ----------
// 注意：chip / row 只用来放"口播之外的信息"（产品名、日期、数值、步骤节点），不要把口播原话装进框里。
const C = {
  chip: (txt, ic, cls = '') => h(`<div class="chip ${cls}">${ic ? icon(ic) : ''}<span>${txt}</span></div>`),
  row: (ic, txt, sub) => h(`<div class="row"><div class="ib">${icon(ic)}</div><div class="tx">${txt}${sub ? `<small>${sub}</small>` : ''}</div></div>`),
  kicker: (txt) => h(`<div class="kicker"><span class="dot"></span>${txt}</div>`),
  title: (html, cls = '') => h(`<div class="title ${cls}">${html}</div>`),
  at: (el, x, y, extra = {}) => { el.style.left = x + 'px'; el.style.top = y + 'px'; Object.assign(el.style, extra); return el; },
};
// 场景/面板的小标题（来源、栏目名）
const kick = (P, txt, at, x = 90, y = 150, out = null) => P.add(C.at(C.kicker(txt), x, y), at, 'left', out);
