"""成片混音：python3 mix.py <项目> → work/mix.wav（-16 LUFS / TP -1.5）
先跑 render.py cues 导出音效点；缺音频文件先跑 scripts/fetch_audio.py。"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proj import Project, duration
from audio_graph import build

P = Project(sys.argv[1]); dur = duration(P.rough)
inputs, fc, clips = build(P, dur)
open(P.path("work", "mix_filter.txt"), "w").write(";\n".join(fc))
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", P.path("work", "mix_filter.txt"),
                "-map", "[out]", "-c:a", "pcm_s16le", P.path("work", "mix.wav")], check=True)
print("mix ok", len(clips), "sfx →", P.path("work", "mix.wav"))
