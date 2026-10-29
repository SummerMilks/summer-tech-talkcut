"""素材预处理：python3 prep.py <项目>
1. 口播：work/rough.mov → 美颜 + 调色 → work/frames/aroll/*.jpg（project.json → beauty / grade）
2. 视频素材：clips_map.json 每项 → 30fps 帧序列 work/frames/<名>/（默认 1280x720 铺满裁切；可给 vf 自定义，如裁手机竖屏）
3. 写 work/clips.js（帧目录与帧数）、work/shots.js（assets/screenshots/sources.jsonl 里的截图与高亮框）
clips_map.json 值：Mixkit id 字符串（先找项目 assets/stock/<id>.mp4，再找共享库 stock/<id>.mp4），
或 {"file": 相对项目的路径或绝对路径, "vf": "ffmpeg 滤镜"}。
"""
import json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proj import Project

url = lambda p: "file://" + os.path.abspath(p)


def beauty_filter(cfg):
    """轻度美颜：只对亮度通道做双边滤波，按强度混合回原图（有效果但不假），再轻提亮、轻锐化。"""
    b = cfg.get("beauty", 0.55)
    g = cfg.get("grade", {"brightness": 0.015, "contrast": 1.05, "saturation": 1.04, "shadows_blue": 0.035})
    grade = (f"eq=brightness={g['brightness']}:contrast={g['contrast']}:saturation={g['saturation']},"
             f"colorbalance=rs=-0.02:bs={g['shadows_blue']}:rh=0.015")
    if b <= 0:
        return grade
    return (f"split[o][b];[b]bilateral=sigmaS=14:sigmaR=0.07:planes=1[s];[o][s]blend=all_mode=normal:all_opacity={b},"
            f"{grade},unsharp=5:5:0.35:5:5:0")


def frames(src, out, vf):
    if os.path.isdir(out) and os.listdir(out): return
    os.makedirs(out, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-vf", vf, "-q:v", "3", f"{out}/%05d.jpg"], check=True)


def main():
    P = Project(sys.argv[1]); W = P.work; FPS = P.fps
    ar = f"{W}/frames/aroll"
    if P.cfg.get("rebuild_aroll") and os.path.isdir(ar): shutil.rmtree(ar)
    frames(P.rough, ar, f"fps={FPS}," + P.cfg.get("aroll_vf", "") + beauty_filter(P.cfg))   # aroll_vf：原片有黑边/非16:9时先裁切，如 "crop=3024:1696:0:134,scale=1920:1080,"
    clips = {"aroll": {"dir": url(ar), "n": len(os.listdir(ar))}}
    missing = []
    cmap = json.load(open(P.path("clips_map.json"))) if os.path.exists(P.path("clips_map.json")) else {}
    for name, spec in cmap.items():
        if name.startswith("_"): continue
        spec = spec if isinstance(spec, dict) else {"file": f"assets/stock/{spec}.mp4"}
        src = P.find(os.path.expanduser(spec["file"]), "stock"); out = f"{W}/frames/{name}"
        if not os.path.exists(src): missing.append(f"{name}({spec['file']})"); continue
        frames(src, out, f"fps={FPS}," + spec.get("vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720"))
        clips[name] = {"dir": url(out), "n": len(os.listdir(out))}
    open(f"{W}/clips.js", "w").write("const CLIPS = " + json.dumps(clips, ensure_ascii=False, indent=1) + ";\n")
    shots, src = {}, P.path("assets", "screenshots", "sources.jsonl")
    if os.path.exists(src):
        for l in open(src):
            d = json.loads(l)
            shots[d["file"][:-4]] = {"src": url(P.path("assets", "screenshots", d["file"])), "url": d["url"], "box": d.get("box")}
    open(f"{W}/shots.js", "w").write("const SHOTS = " + json.dumps(shots, ensure_ascii=False, indent=1) + ";\n")
    for k, v in clips.items(): print(f"{k:14s} {v['n']:5d} 帧 {v['n'] / FPS:6.1f}s")
    print("截图", len(shots))
    if missing: sys.exit("缺素材：" + " ".join(missing))


if __name__ == "__main__":
    main()
