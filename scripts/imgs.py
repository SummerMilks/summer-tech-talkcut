"""列出/下载官方页面里的产品图和演示视频（比截图信息量大得多，优先用）。环境变量 OFFICIAL_DIR 指定输出目录（默认 ./assets/official）。
  python3 imgs.py <名前缀> <网址>               列出页面里的大图（宽≥500）、<video> 源和封面，带序号和 alt 文字
  python3 imgs.py <名前缀> <网址> <序号...>      下载指定序号到 <前缀>_<序号>.<ext>，登记 sources.jsonl
懒加载严重的页面会慢慢滚动到底再收集。alt 文字常有现成的中文说明，可直接做中文注释。"""
import json, os, sys, time, urllib.request
from playwright.sync_api import sync_playwright
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
OUT = os.path.abspath(os.environ.get("OFFICIAL_DIR", "assets/official")); os.makedirs(OUT, exist_ok=True)
pre, url, *want = sys.argv[1:]
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900}, user_agent=UA)
    pg.goto(url, timeout=90000, wait_until="domcontentloaded"); pg.wait_for_timeout(6000)
    for _ in range(25): pg.mouse.wheel(0, 600); pg.wait_for_timeout(700)
    imgs = pg.evaluate("""() => { const out = [];
      for (const i of document.images) { const s = i.currentSrc || i.src; if (s && (i.naturalWidth >= 500 || /carousel|hero|screenshot/i.test(s))) out.push([s, i.naturalWidth, i.naturalHeight, i.alt || '']); }
      for (const v of document.querySelectorAll('video')) { if (v.poster) out.push([v.poster, 0, 0, 'video poster']); for (const s of v.querySelectorAll('source')) out.push([s.src, 0, 0, 'video']); if (v.src) out.push([v.src, 0, 0, 'video']); }
      return [...new Map(out.map(x => [x[0], x])).values()]; }""")
    b.close()
for k, (s, w, h, alt) in enumerate(imgs):
    if not want: print(k, w, h, alt[:70], s[:110])
    elif str(k) in want:
        ext = ".mp4" if "video" == alt else (".png" if ".png" in s.lower() else ".webp" if "webp" in s.lower() else ".jpg")
        f = f"{pre}_{k}{ext}"
        data = urllib.request.urlopen(urllib.request.Request(s, headers={"User-Agent": UA, "Referer": url}), timeout=120).read()
        open(f"{OUT}/{f}", "wb").write(data)
        open(f"{OUT}/sources.jsonl", "a").write(json.dumps({"file": f, "src": s, "page": url, "alt": alt, "captured": time.strftime("%Y-%m-%d %H:%M")}, ensure_ascii=False) + "\n")
        print("ok", f, len(data))
