"""免版权 B-roll：Mixkit（Mixkit 各素材许可不同，使用前须核验单条许可）。

  python3 stock.py search <关键词> [关键词...]        每个关键词抓前 24 条，生成带编号的联系表 <词>.jpg + <词>.json
  python3 stock.py get <id> [id...]                   下载（优先 1080p，失败用 720p）到 <id>.mp4，登记 index.jsonl
  python3 stock.py pick <词>:<格号>[,<格号>] ...       按联系表格号换算 id 并下载
素材统一放共享库 $TTHE_HOME/stock（默认 ~/.tech-talking-head-edit/stock），下载过的 id 不会重复下载，所有项目共用；
项目的 clips_map.json 直接写 id 即可。
关键词用英文，空格换成 -（如 data-center）。先看联系表挑画面，再下载。网络慢时 720p 足够（全屏场景会压暗，卡片头图更小）。
"""
import json, os, re, shutil, subprocess, sys, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/141.0 Safari/537.36"}


def get(url, tries=3):
    for k in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception:
            if k == tries - 1: raise


def search(out, q):
    html = get(f"https://mixkit.co/free-stock-video/discover/{q}/").decode("utf8", "ignore")
    seen = []
    for slug in dict.fromkeys(re.findall(r"/free-stock-video/([a-z0-9-]+-\d+)/", html)):
        vid = slug.rsplit("-", 1)[1]
        seen.append({"id": vid, "title": slug.rsplit("-", 1)[0].replace("-", " "),
                     "page": f"https://mixkit.co/free-stock-video/{slug}/"})
    tdir = f"{out}/_thumbs"; os.makedirs(tdir, exist_ok=True)
    for it in seen:
        p = f"{tdir}/{it['id']}.jpg"
        for size in ("360", "720"):
            if os.path.exists(p) and os.path.getsize(p) > 0: break
            try: open(p, "wb").write(get(f"https://assets.mixkit.co/videos/{it['id']}/{it['id']}-thumb-{size}-0.jpg"))
            except Exception: pass
    seen = [it for it in seen if os.path.exists(f"{tdir}/{it['id']}.jpg") and os.path.getsize(f"{tdir}/{it['id']}.jpg") > 0]
    json.dump(seen, open(f"{out}/{q}.json", "w"), ensure_ascii=False, indent=1)
    if not seen: print(q, "无结果"); return
    sheet(out, q, seen)
    for i, it in enumerate(seen): print(q, i, it["id"], it["title"])


def sheet(out, q, seen):
    """联系表：每格左上角写序号。缩略图逐张统一成 320x180 再拼，避免尺寸/编码不一致导致拼接中断。"""
    tmp = f"{out}/_sheet_tmp"; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    k = 0
    for it in seen:
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{out}/_thumbs/{it['id']}.jpg", "-vf",
                            "scale=320:180:force_original_aspect_ratio=increase,crop=320:180", "-frames:v", "1",
                            f"{tmp}/{k:03d}.png"])
        if r.returncode == 0: it["cell"] = k; k += 1
    rows = (k + 5) // 6
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/%03d.png", "-vf",
                    "drawtext=text='%{eif\\:n\\:d}':x=6:y=4:fontsize=26:fontcolor=yellow:box=1:boxcolor=black@0.6,"
                    f"tile=6x{rows}:padding=4", "-frames:v", "1", f"{out}/{q}.jpg"], check=True)
    shutil.rmtree(tmp)


def fetch(out, vid):
    f = f"{out}/{vid}.mp4"
    if os.path.exists(f): return
    data = None
    for q in ("1080", "720"):
        try:
            data = get(f"https://assets.mixkit.co/videos/{vid}/{vid}-{q}.mp4"); break
        except Exception: data = None
    if not data: print("失败", vid); return
    open(f, "wb").write(data)
    meta = {}
    for j in os.listdir(out):
        if j.endswith(".json"):
            for it in json.load(open(f"{out}/{j}")):
                if it["id"] == vid: meta = it
    open(f"{out}/index.jsonl", "a").write(json.dumps({"file": f"{vid}.mp4", **meta, "source": "Mixkit",
                                                    "license": "Mixkit License（免费商用、无需署名）"}, ensure_ascii=False) + "\n")
    print("ok", vid, meta.get("title", ""))


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
    from proj import HOME
    cmd, *args = sys.argv[1:]; out = os.path.join(HOME, "stock")
    os.makedirs(out, exist_ok=True)
    if cmd == "search":
        for q in args: search(out, q)
    elif cmd == "sheet":
        for q in args: sheet(out, q, json.load(open(f"{out}/{q}.json")))
    elif cmd == "get":
        for v in args: fetch(out, v)
    elif cmd == "pick":
        for a in args:
            q, cells = a.split(":")
            L = [it for it in json.load(open(f"{out}/{q}.json")) if os.path.exists(f"{out}/_thumbs/{it['id']}.jpg")]
            for c in cells.split(","): fetch(out, L[int(c)]["id"])
    else: sys.exit(__doc__)
