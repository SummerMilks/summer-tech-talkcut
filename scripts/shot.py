"""官网/来源页截图（真 Chrome 无头，1440x900 视口，2 倍像素）。环境变量 SHOT_DIR 指定输出目录（默认 ./assets/screenshots）。
  python3 shot.py text <名> <网址>                 导出页面正文到 <名>.txt，先读正文找要展示的原句
  python3 shot.py shot <名> <网址> [要定位的原文]   截图 → <名>.png；给了原文就把它滚到画面中部，
                                                    并记录它在截图里的位置框（1440x900 坐标），视频里用来做高亮
登记 sources.jsonl：网址、标题、截图时间、高亮框。自动去掉 cookie 横幅、弹窗、遮罩。
注意：截图只用于"证明存在"（中文报道标题、价格表、产品界面）；英文长段落观众看不懂，不要拿来解释概念。"""
import json, os, sys, time
from playwright.sync_api import sync_playwright

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
OUT = os.path.abspath(os.environ.get("SHOT_DIR", "assets/screenshots")); os.makedirs(OUT, exist_ok=True)
CLEAN = """() => { for (const e of document.querySelectorAll('body *')) { const s = getComputedStyle(e);
  if ((s.position === 'fixed' || s.position === 'sticky') && e.getBoundingClientRect().top > 300) e.remove();
  if ((s.position === 'fixed' || s.position === 'sticky') && (/cookie|consent|modal|mask|overlay|popup|dialog/i.test(e.id + ' ' + e.className) || e.getAttribute('role') === 'dialog')) e.remove(); }
  for (const e of document.querySelectorAll('body *')) if (getComputedStyle(e).filter.includes('blur')) e.style.filter = 'none'; }"""
FIND = """(txt) => { const norm = x => x.replace(/[\u2010-\u2015\u00a0]/g, m => m === '\u00a0' ? ' ' : '-');
  const c = [...document.querySelectorAll('p,li,h1,h2,h3,h4,blockquote,span,div')]
    .filter(e => e.getClientRects().length && norm(e.innerText || '').includes(norm(txt)))
    .sort((x, y) => x.innerText.length - y.innerText.length);
  if (!c.length) return null; c[0].scrollIntoView({block: 'center'});
  const b = c[0].getBoundingClientRect(); return [b.left, b.top, b.width, b.height]; }"""


def open_page(p, url):
    b = p.chromium.launch(channel="chrome", headless=True, args=["--disable-blink-features=AutomationControlled"])
    pg = b.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2, user_agent=UA, locale="en-US")
    r = pg.goto(url, timeout=90000, wait_until="domcontentloaded")
    pg.wait_for_timeout(6000)
    pg.keyboard.press("Escape")                       # 关弹窗
    pg.evaluate("""() => document.querySelectorAll('[class*=close i],[aria-label*=close i],[aria-label*=关闭]').forEach(e => { try { e.click() } catch (_) {} })""")
    pg.wait_for_timeout(800)
    for _ in range(8): pg.mouse.wheel(0, 900); pg.wait_for_timeout(400)   # 触发懒加载
    pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(1200)
    pg.evaluate(CLEAN)
    return b, pg, r


if __name__ == "__main__":
    cmd, name, url, *rest = sys.argv[1:]
    with sync_playwright() as p:
        b, pg, r = open_page(p, url)
        if cmd == "text":
            open(f"{OUT}/{name}.txt", "w").write(pg.url + "\n" + pg.title() + "\n\n" + pg.inner_text("body"))
            print(name, r.status if r else None, pg.url, len(pg.inner_text("body")))
        else:
            box = None
            if rest:
                pg.evaluate(FIND, rest[0]); pg.wait_for_timeout(1500); pg.evaluate(CLEAN)
                box = pg.evaluate(FIND, rest[0]); pg.wait_for_timeout(800)
            pg.screenshot(path=f"{OUT}/{name}.png")
            open(f"{OUT}/sources.jsonl", "a").write(json.dumps({"file": f"{name}.png", "url": pg.url, "title": pg.title(),
                "status": r.status if r else None, "find": rest[0] if rest else None, "box": box,
                "captured": time.strftime("%Y-%m-%d %H:%M")}, ensure_ascii=False) + "\n")
            print(name, r.status if r else None, pg.url, "|", pg.title(), "| box", box)
        b.close()
