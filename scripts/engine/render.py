"""逐帧渲染：Playwright 打开 work/stage.html，window.seek(帧) 后截图，管道送进 ffmpeg。
用法：
  python3 render.py <项目> still <秒> [秒...]          导出单帧 PNG 到 work/stills/，并拼 2x2 联系表 work/stills/sheet_*.jpg
  python3 render.py <项目> video <起秒> <止秒> <输出.mp4> [并行数]
  python3 render.py <项目> cues                        导出音效提示点 work/cues.json
  python3 render.py <项目> text                        导出全部字幕和画面文字 output/字幕与画面文字.txt（合规扫描用）
  python3 render.py <项目> overlay <起秒> <止秒> <输出.mov> [并行数]   只渲染包装层：透明底 ProRes 4444（剪映分轨用）
  python3 render.py <项目> akeys                        导出每帧口播位移/缩放 work/aroll_motion.json（剪映关键帧用）
"""
import glob, json, os, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proj import Project, ENGINE, duration

FPS = 30


def build_stage(P):
    """按项目生成 work/stage.html（模板里的路径换成绝对 file:// 路径）"""
    u = lambda p: "file://" + os.path.abspath(p) + ("/" if os.path.isdir(p) else "")
    t = open(os.path.join(ENGINE, "stage.template.html")).read()
    if not os.path.exists(P.font): sys.exit(f"找不到字幕字体 {P.font}：运行 scripts/setup.py 装一次即可")
    t = (t.replace("{{FONT_URL}}", u(P.font))
          .replace("{{PROJ_URL}}", u(P.root)).replace("{{WORK_URL}}", u(P.work)).replace("{{ENGINE_URL}}", u(ENGINE)))
    open(os.path.join(P.work, "stage.html"), "w").write(t)


def open_page(p, root, overlay=False):
    b = p.chromium.launch(args=["--allow-file-access-from-files", "--disable-web-security", "--force-color-profile=srgb",
                                "--hide-scrollbars", "--font-render-hinting=none"])
    pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"file://{root}/work/stage.html" + ("?overlay" if overlay else ""))
    pg.wait_for_function("window.READY === true", timeout=30000)
    pg.evaluate("document.fonts.ready")
    if errs: raise SystemExit("页面脚本出错：" + errs[0])
    return b, pg


def chunk(args):
    root, f0, f1, out, overlay = args
    if overlay:   # 透明底 PNG → ProRes 4444（带 alpha）
        # Chrome 截图在渐变淡出到全透明处有抖动，留下"几乎透明但颜色极亮"的像素；剪映合成时会显成一条竖向虚线。
        # 把 alpha < 24 的像素颜色按 alpha 比例压暗（可见内容不变，PSNR 45dB）。
        clean = ("[0:v]format=gbrap,split=3[c][a][a2];[a]alphaextract,lut=y='if(lt(val\\,24)\\,val*255/24\\,255)',format=gbrp[m];"
                 "[c]format=gbrp[c2];[c2][m]blend=all_mode=multiply[cm];[a2]alphaextract[al];[cm][al]alphamerge,format=yuva444p10le")
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
                                "-filter_complex", clean, "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-vendor", "apl0", "-r", str(FPS), out],
                               stdin=subprocess.PIPE)
    else:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                                "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", "-r", str(FPS), out],
                               stdin=subprocess.PIPE)
    with sync_playwright() as p:
        b, pg = open_page(p, root, overlay)
        for f in range(f0, f1):
            for k in range(3):  # 偶发截图超时（机器负载高时），重试
                try:
                    pg.evaluate(f"window.seek({f})")
                    buf = (pg.screenshot(type="png", omit_background=True, timeout=120000) if overlay
                           else pg.screenshot(type="jpeg", quality=94, timeout=120000)); break
                except Exception:
                    if k == 2: raise
            enc.stdin.write(buf)
        b.close()
    enc.stdin.close(); enc.wait()
    return out


if __name__ == "__main__":
    P = Project(sys.argv[1]); root = P.root; cmd = sys.argv[2]
    build_stage(P)
    if cmd == "still":
        os.makedirs(f"{root}/work/stills", exist_ok=True)
        with sync_playwright() as p:
            b, pg = open_page(p, root)
            for s in sys.argv[3:]:
                pg.evaluate(f"window.seek({round(float(s) * FPS)})")
                pg.screenshot(path=f"{root}/work/stills/{float(s):07.2f}.png")
            b.close()
        fs = [f"{root}/work/stills/{float(s):07.2f}.png" for s in sys.argv[3:]]
        for k in range(0, len(fs), 4):   # 2x2 联系表，方便一次看 4 个场景
            g = fs[k:k + 4] + [fs[k + len(fs[k:k + 4]) - 1]] * (4 - len(fs[k:k + 4]))
            inp = sum([["-i", f] for f in g], [])
            subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex",
                            "".join(f"[{i}]scale=960:540[s{i}];" for i in range(4)) + "[s0][s1][s2][s3]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0",
                            f"{root}/work/stills/sheet_{k // 4}.jpg"], check=True)
        print("联系表：", " ".join(sorted(glob.glob(f"{root}/work/stills/sheet_*.jpg"))))
    elif cmd == "cues":
        with sync_playwright() as p:
            b, pg = open_page(p, root)
            json.dump(pg.evaluate("CUES"), open(f"{root}/work/cues.json", "w"), ensure_ascii=False)
            b.close()
    elif cmd == "text":
        with sync_playwright() as p:
            b, pg = open_page(p, root)
            subs = pg.evaluate("SUBS.map(s => s[2]).join('\\n')")
            ov = pg.evaluate("[...document.querySelectorAll('#stage *')].map(e => [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')).filter(Boolean).join('\\n')")
            b.close()
        open(f"{root}/output/字幕与画面文字.txt", "w").write("【字幕】\n" + subs + "\n\n【画面文字】\n" + ov + "\n")
        print("→", f"{root}/output/字幕与画面文字.txt")
    elif cmd == "akeys":
        with sync_playwright() as p:
            b, pg = open_page(p, root)
            n = round(duration(P.rough) * FPS)
            st = pg.evaluate(f"(() => {{ AKEYS.sort((p, q) => p.t - q.t); const o = []; for (let f = 0; f < {n}; f++) {{ const a = arollState(f / FPS); o.push([+a.x.toFixed(2), +a.s.toFixed(5)]); }} return o; }})()")
            json.dump(st, open(f"{root}/work/aroll_motion.json", "w"))
            b.close()
    elif cmd in ("video", "overlay"):
        t0, t1, out = float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
        n = int(sys.argv[6]) if len(sys.argv) > 6 else 4
        F0, F1 = round(t0 * FPS), round(t1 * FPS)
        step = -(-(F1 - F0) // n)
        ext = ".mov" if cmd == "overlay" else ".mp4"
        parts = [(root, a, min(a + step, F1), f"{out}.part{i}{ext}", cmd == "overlay") for i, a in enumerate(range(F0, F1, step))]
        with ProcessPoolExecutor(n) as ex: done = list(ex.map(chunk, parts))
        lst = f"{out}.txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(d)}'\n" for d in done))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
        for d in done: os.remove(d)
        os.remove(lst)
