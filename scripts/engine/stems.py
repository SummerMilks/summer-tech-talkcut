"""剪映分轨音频：python3 stems.py <项目> <输出目录>
人声.wav / 配乐.wav（已按人声压低）/ 音效_合并.wav + sfx_clips.json（每个音效片段的文件、起点、截取、音量）。
三条分轨乘同一个增益，叠加后整体 -16 LUFS，与成片一致。"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proj import Project, duration
from audio_graph import build

P = Project(sys.argv[1])
out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else P.jianying_media   # 不传就用项目的剪映素材目录
os.makedirs(out, exist_ok=True)
dur = duration(P.rough); flt = P.path("work", "stems_filter.txt")


def run(gain, outs, capture=False):
    inputs, fc, clips = build(P, dur, gain_db=gain)
    open(flt, "w").write(";\n".join(fc))
    r = subprocess.run(["ffmpeg", "-v", "info", "-y", *inputs, "-filter_complex_script", flt, *outs], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr[-1500:])
    return r, clips


null = sum([["-map", f"[{n}]", "-f", "null", "-"] for n in ("sum", "voice", "music", "sfx")], [])
r, _ = run(0.0, null)
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1]); gain = -16.0 - I
print(f"未调增益 {I} LUFS → 统一增益 {gain:+.2f} dB")
outs = []
for n, f in (("voice", "人声.wav"), ("music", "配乐.wav"), ("sfx", "音效_合并.wav")):
    outs += ["-map", f"[{n}]", "-c:a", "pcm_s16le", f"{out}/{f}"]
outs += ["-map", "[sum]", "-f", "null", "-"]
_, clips = run(gain, outs)
json.dump(clips, open(f"{out}/sfx_clips.json", "w"), ensure_ascii=False, indent=0)
print("stems ok", len(clips), "sfx →", out)
