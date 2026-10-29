"""下载产品官方 App 图标（App Store 公开搜索接口，1024px）。环境变量 OFFICIAL_DIR 指定输出目录（默认 ./assets/official）。
  python3 app_icon.py search "<关键词>"                   列出候选：App 名 | 开发商
  python3 app_icon.py get <文件名> "<关键词>" "<App 全名>"   下载该 App 的图标为 <文件名>.png，登记 sources.jsonl
核对开发商是不是官方（例如 Meta Platforms / OpenAI / X Corp.），不要用第三方同名应用的图标。
没有独立 App 的产品（例如嵌在别的应用里的功能），去官网找官方标识（imgs.py 列出页面里的 svg/png），放进同样的圆角底。"""
import json, os, sys, time, urllib.parse, urllib.request

OUT = os.path.abspath(os.environ.get("OFFICIAL_DIR", "assets/official")); os.makedirs(OUT, exist_ok=True)


def search(q, country="us"):
    u = f"https://itunes.apple.com/search?term={urllib.parse.quote(q)}&entity=software&country={country}&limit=8"
    return json.load(urllib.request.urlopen(u, timeout=30))["results"]


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "search":
        for r in search(sys.argv[2]): print(r["trackName"], "|", r["sellerName"])
    elif cmd == "get":
        name, q, app = sys.argv[2:5]
        hit = next((r for r in search(q) if r["trackName"] == app), None)
        if not hit: sys.exit(f"没找到「{app}」，先用 search 看准确名称")
        url = hit["artworkUrl512"].rsplit("/", 1)[0] + "/1024x1024bb.png"
        open(f"{OUT}/{name}.png", "wb").write(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read())
        open(f"{OUT}/sources.jsonl", "a").write(json.dumps({"file": f"{name}.png", "src": url, "page": hit["trackViewUrl"],
            "alt": f"{app} App Store 图标（{hit['sellerName']}）", "captured": time.strftime("%Y-%m-%d %H:%M")}, ensure_ascii=False) + "\n")
        print("ok", name, "|", hit["sellerName"])
    else:
        sys.exit(__doc__)
