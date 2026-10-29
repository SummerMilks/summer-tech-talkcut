"""把 audio.json 用到的配乐和音效下载到共享库（Mixkit（素材许可因条目而异，使用前须核验））。下载过的不会重复下载，所有项目共用。
用法：python3 fetch_audio.py [项目]      不给项目就按 skill 自带的默认 audio.json 下载
共享库位置：$TTHE_HOME/audio（默认 ~/.tech-talking-head-edit/audio）。
audio.json 里 mixkit 是 Mixkit 条目 id；用自己的文件时写 file（项目 assets/audio/ 下的文件名，或绝对路径），不会下载。"""
import json, os, sys, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from proj import HOME, SKILL

UA = {"User-Agent": "Mozilla/5.0"}
src = os.path.join(os.path.abspath(sys.argv[1]), "audio.json") if len(sys.argv) > 1 else ""
cfg = json.load(open(src if src and os.path.exists(src) else os.path.join(SKILL, "templates", "audio.json")))
out = os.path.join(HOME, "audio"); os.makedirs(out, exist_ok=True)
jobs = [("music", m["mixkit"]) for m in cfg["music"] if m.get("mixkit")] + \
       [("sfx", s["mixkit"]) for s in cfg["sfx"].values() if s.get("mixkit")]
n = 0
for kind, i in jobs:
    f = os.path.join(out, f"{kind}_{i}.mp3")
    if os.path.exists(f) and os.path.getsize(f) > 0: continue
    url = f"https://assets.mixkit.co/active_storage/sfx/{i}/{i}-preview.mp3" if kind == "sfx" else f"https://assets.mixkit.co/music/{i}/{i}.mp3"
    try:
        open(f, "wb").write(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read())
        open(os.path.join(out, "LICENSES.md"), "a").write(f"- {os.path.basename(f)}：Mixkit {kind} #{i}，Mixkit（使用前核验该条目的许可）\n")
        n += 1; print("ok", f)
    except Exception as e:
        print("失败", kind, i, e)
print(f"新下载 {n} 个，共享库已有 {len(jobs)} 个中的 {sum(os.path.exists(os.path.join(out, f'{k}_{i}.mp3')) for k, i in jobs)} 个：{out}")
