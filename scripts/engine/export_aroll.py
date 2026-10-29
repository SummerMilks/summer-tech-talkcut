"""导出剪映用口播：python3 export_aroll.py <项目> <输出目录>
  口播_无美颜.mp4：只调色（在剪映里自己加美颜）     口播_已美颜.mp4：与成片同款美颜
两条都带处理后的人声（需先跑 stems.py 生成 <输出目录>/人声.wav）。"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proj import Project
from prep import beauty_filter

P = Project(sys.argv[1])
out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else P.jianying_media   # 不传就用项目的剪映素材目录
voice = f"{out}/人声.wav"
if not os.path.exists(voice): sys.exit("先运行 stems.py 生成 人声.wav")
for fn, cfg in (("口播_无美颜.mp4", dict(P.cfg, beauty=0)), ("口播_已美颜.mp4", P.cfg)):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", P.rough, "-i", voice,
                    "-filter_complex", f"[0:v]{P.cfg.get('aroll_vf', '')}{beauty_filter(cfg)}[v]", "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "14",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", f"{out}/{fn}"], check=True)
    print("ok", fn)
