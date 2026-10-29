"""一次性安装共享库：字体、全局配置、默认配乐音效。之后每个新项目都不用再复制或下载。

  python3 scripts/setup.py                          全部用默认（字体从 GitHub 下载得意黑）
  python3 scripts/setup.py --font <已有的 SmileySans-Oblique.ttf>     用本机已有字体（不下载）
  python3 scripts/setup.py --jianying-shell <剪映空草稿文件夹> --media-dir <剪映素材根目录>   顺便配好剪映导出（每个项目在根目录下自动建子文件夹）
  python3 scripts/setup.py --no-audio               先不下载配乐音效
共享库位置：$TTHE_HOME（默认 ~/.tech-talking-head-edit）。想放外接盘，先 export TTHE_HOME=/Volumes/xxx/tthe 再运行。
重复运行是安全的：已有的文件和配置项不会被覆盖（除非这次显式传了参数）。"""
import argparse, io, json, os, shutil, subprocess, sys, urllib.request, zipfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from proj import HOME, SKILL

FONT = "SmileySans-Oblique.ttf"
FONT_URL = "https://github.com/atelier-anchor/smiley-sans/releases/download/v2.0.1/smiley-sans-v2.0.1.zip"
ap = argparse.ArgumentParser()
ap.add_argument("--font"); ap.add_argument("--jianying-shell"); ap.add_argument("--media-dir"); ap.add_argument("--no-audio", action="store_true")
a = ap.parse_args()
for d in ("fonts", "audio", "stock"): os.makedirs(os.path.join(HOME, d), exist_ok=True)

# 1) 字体
dst = os.path.join(HOME, "fonts", FONT)
if a.font:
    shutil.copy(os.path.expanduser(a.font), dst); print("字体：已放入", dst)
elif not os.path.exists(dst):
    try:
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(FONT_URL, timeout=120).read()))
        n = next(x for x in z.namelist() if x.endswith(FONT))
        open(dst, "wb").write(z.read(n)); print("字体：已下载得意黑（OFL）→", dst)
    except Exception as e:
        print("⚠️ 字体下载失败：", e, "\n   手动下载 https://github.com/atelier-anchor/smiley-sans 后运行：python3 scripts/setup.py --font <路径>")
else:
    print("字体：已存在", dst)

# 2) 全局配置
cp = os.path.join(HOME, "config.json")
cfg = json.load(open(cp)) if os.path.exists(cp) else json.load(open(os.path.join(SKILL, "templates", "config.default.json")))
if a.jianying_shell: cfg["jianying"]["shell"] = os.path.abspath(os.path.expanduser(a.jianying_shell))
if a.media_dir: cfg["jianying"]["media_dir"] = os.path.abspath(os.path.expanduser(a.media_dir))
json.dump(cfg, open(cp, "w"), ensure_ascii=False, indent=2); print("配置：", cp)

# 3) 默认配乐音效
if not a.no_audio:
    subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "fetch_audio.py")])
print("\n共享库就绪：", HOME, "\n新项目：python3 scripts/init_project.py <项目目录> <口播原片>")
