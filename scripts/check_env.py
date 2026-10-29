"""环境自检：python3 scripts/check_env.py [项目目录]
逐项检查剪辑必需和剪映导出所需的工具、模型、字体、剪映外壳草稿，缺什么打印怎么补。"""
import glob, json, os, shutil, subprocess, sys

ok = True
def chk(name, cond, fix, required=True):
    global ok
    print(("✅" if cond else ("❌" if required else "⚠️ ")), name, "" if cond else f"→ {fix}")
    if required and not cond: ok = False

print("== 必需（剪辑与包装）")
chk("ffmpeg / ffprobe", shutil.which("ffmpeg") and shutil.which("ffprobe"), "brew install ffmpeg（需要 libass、prores_ks、bilateral 等常规滤镜）")
w = shutil.which("whisper-cli")
chk("whisper.cpp（whisper-cli）", w, "brew install whisper-cpp")
model = os.path.expanduser(os.environ.get("WHISPER_MODEL", "~/.cache/whisper/ggml-large-v3-turbo-q5_0.bin"))
chk(f"Whisper 模型 {model}", os.path.exists(model), "下载 ggml-large-v3-turbo-q5_0.bin（huggingface: ggerganov/whisper.cpp），或设环境变量 WHISPER_MODEL 指向已有模型")
try:
    import playwright  # noqa
    pw = True
except ImportError:
    pw = False
chk("Python playwright", pw, "pip install playwright && playwright install chromium")
chk("Chromium（playwright）", bool(glob.glob(os.path.expanduser("~/Library/Caches/ms-playwright/chromium*")) or glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium*"))), "playwright install chromium")
chk("Google Chrome（截图官网用，反爬更少）", os.path.exists("/Applications/Google Chrome.app") or shutil.which("google-chrome"), "安装 Chrome；没有也能用 Chromium，但部分官网会拦截", required=False)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from proj import HOME, Project, global_cfg, merge
print(f"== 共享库 {HOME}（装一次，所有项目共用）")
chk("全局配置 config.json", os.path.exists(os.path.join(HOME, "config.json")), "运行一次 python3 scripts/setup.py")
font = os.path.join(HOME, "fonts", "SmileySans-Oblique.ttf")
chk(f"字幕字体 {font}", os.path.exists(font), "python3 scripts/setup.py（自动下载得意黑），或 --font <本机已有的 ttf>")
na = len([f for f in glob.glob(os.path.join(HOME, "audio", "*.mp3")) if os.path.getsize(f)])
chk(f"配乐音效（已有 {na} 个）", na >= 20, "python3 scripts/fetch_audio.py", required=False)

cfg = global_cfg()
if len(sys.argv) > 1:
    P = Project(sys.argv[1]); cfg = P.cfg
    chk(f"口播原片 {P.source}", os.path.exists(P.source), "在项目 project.json 的 source 里写对路径")
    chk(f"本项目用的字幕字体 {P.font}", os.path.exists(P.font), "python3 scripts/setup.py")

print("== 可选（导出剪映分轨草稿）")
jy = cfg.get("jianying", {})
app = any(os.path.exists(p) for p in ("/Applications/VideoFusion-macOS.app", "/Applications/剪映专业版.app"))
chk("剪映专业版（Mac）", app, "安装剪映专业版 Mac；本 skill 只验证过 Mac 版明文草稿", required=False)
shell = os.path.expanduser(jy.get("shell", ""))
chk(f"外壳草稿 {shell or '(未配置)'}", bool(shell) and os.path.exists(os.path.join(shell, "draft_meta_info.json")),
    "在剪映里新建一个空草稿并退出剪映，然后 python3 scripts/setup.py --jianying-shell <该草稿文件夹>", required=False)
root_dir = os.path.expanduser(jy.get("projects_root", "~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"))
chk("剪映草稿根目录", os.path.isdir(root_dir), "剪映 → 设置 → 草稿位置，写进 config.json → jianying.projects_root", required=False)
rid = jy.get("font_resource_id", "")
cache = glob.glob(os.path.expanduser(f"~/Movies/JianyingPro/User Data/Cache/effect/{rid}/*/*.ttf")) if rid else []
chk("剪映字库里的字幕字体", bool(cache), "在剪映里给任意文字选一次「得意黑」让它下载到缓存", required=False)
out = os.path.expanduser(jy.get("media_dir", "")) or os.path.expanduser("~")
try:
    st = os.statvfs(out); free = st.f_bavail * st.f_frsize / 1e9
    chk(f"包装层导出盘 {out} 剩余 {free:.0f} GB（ProRes 4444 约 2.5 GB/分钟）", free > 20,
        "python3 scripts/setup.py --media-dir <空间大的盘上的文件夹>", required=False)
except OSError:
    chk(f"包装层导出目录 {out}", False, "目录不存在：python3 scripts/setup.py --media-dir <文件夹>", required=False)
print("\n结论：", "可以开始" if ok else "先补齐 ❌ 项")
sys.exit(0 if ok else 1)
