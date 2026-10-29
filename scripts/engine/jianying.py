"""生成剪映分轨草稿：口播 / 包装 / 字幕 / 音效 / 音乐。画面与成片一致，口播可在剪映里改美颜、字幕逐条可改。

  python3 jianying.py <项目> <草稿名> [--beauty] [--no-register] [--new]
  默认：同名草稿已存在就原地更新（先备份到 <草稿>/.tthe_backup/<时间>/，不用退出剪映，但剪映里不能正打开这个草稿）；
       不存在才新建并登记（登记要求剪映已退出）。--new：强制新建，同名已存在就报错。
  注意：原地更新会覆盖用户在剪映里对该草稿做的修改；用户改过草稿时先问清楚再更新。

前置（见 references/jianying-export.md）：
  <M> = 这个项目的剪映素材目录（python3 proj.py <项目> 打印；全局 media_dir 下按项目名自动建子文件夹）
  - <M>/包装层.mov        render.py overlay 0 <时长> <M>/包装层.mov
  - <M>/口播_无美颜.mp4 / 口播_已美颜.mp4 / 人声.wav / 配乐.wav / sfx_clips.json   export_aroll.py + stems.py
  - work/aroll_motion.json        render.py akeys
  - project.json → jianying.shell（剪映里新建的空草稿）、drafts_dir、projects_root、font_resource_id、media_dir
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jydraft as jy
from proj import Project, duration
from playwright.sync_api import sync_playwright

P = Project(sys.argv[1]); name = sys.argv[2]
beauty, do_register = "--beauty" in sys.argv, "--no-register" not in sys.argv
J = P.cfg.get("jianying", {}); FPS = P.fps
media = P.jianying_media          # 每个项目独立的素材目录，见 proj.py
ORIGIN_Y = 1080 * .42          # stage.html 里口播 transform-origin: 50% 42%；剪映按中心缩放，要补位移
dur = duration(f"{media}/包装层.mov")
d = jy.Draft(1920, 1080, FPS, name)

# 1) 口播：整段一个片段，位置/缩放关键帧（只在变化处取点，线性插值）
aroll = f"{media}/{'口播_已美颜' if beauty else '口播_无美颜'}.mp4"
# 人声不靠视频自带音轨：剪映 Mac 对脚本写入的视频素材经常不出原声（has_sound_separated 修过一次仍复发），
# 所以口播视频静音、has_audio=False，人声单独放「人声」音频轨（stems.py 导出的 人声.wav，增益与成片一致）
seg = d.add_media(aroll, 0, dur, track="main", volume=0.0)
vm = next(m for m in d.mats("videos") if m["id"] == seg["material_id"])
vm["has_audio"], vm["has_sound_separated"] = False, False
d.add_audio(f"{media}/人声.wav", 0, dur, track="人声", name="人声")
mot = json.load(open(P.path("work", "aroll_motion.json")))[:round(dur * FPS)]
pts = []
for i, (x, s) in enumerate(mot):
    prev, nxt = (mot[i - 1] if i else None), (mot[i + 1] if i + 1 < len(mot) else None)
    changing = (prev is not None and prev != [x, s]) or (nxt is not None and nxt != [x, s])
    if i in (0, len(mot) - 1) or (changing and (i % 2 == 0 or prev == [x, s] or nxt == [x, s])):
        dy = (540 - ORIGIN_Y) * (s - 1)
        pts.append((i / FPS, x / 960, -dy / 540, s, 0.0))
jy.add_motion(seg, pts, ease="none")

# 2) 包装层：透明底 ProRes 4444
ov = d.add_media(f"{media}/包装层.mov", 0, dur, track="包装", volume=0.0)
next(m for m in d.mats("videos") if m["id"] == ov["material_id"])["has_audio"] = False

# 3) 字幕：剪映原生文字
with sync_playwright() as p:
    b = p.chromium.launch(args=["--allow-file-access-from-files"]); pg = b.new_page()
    pg.goto(f"file://{P.work}/stage.html"); pg.wait_for_function("window.READY === true")
    subs = pg.evaluate("SUBS"); b.close()
st = J.get("subtitle", {})
f = jy.font(J.get("font_resource_id", "7399865900821647935"), J.get("font_title", "得意黑"))
if not f["path"]: print("⚠️ 剪映缓存里没找到字幕字体，草稿会回退成默认字体（先在剪映里用一次该字体）")
for a, e, txt in subs:
    e = min(e, dur)
    if e - a < .05: continue
    d.add_text(txt, a, e - a, track="字幕", size=st.get("size", 5.0), font=f if f["path"] else None, pos=(0.0, st.get("y", -0.81)),
               bg=dict(color=(0, 0, 0), alpha=st.get("bg_alpha", 0.58), radius=0.25, w=0.16, h=0.22))

# 4) 音效：每个一个片段；同时刻重叠的会被分到相邻音频轨（剪映不允许同轨重叠）
for c in json.load(open(f"{media}/sfx_clips.json")):
    if c["start"] >= dur: continue
    ln = min(c["len"], dur - c["start"])
    d.add_audio(c["file"], c["start"], ln, src_start=c["ss"], track="音效", volume=round(10 ** (c["gain_db"] / 20), 4),
                name=c["name"], fade_out=min(.15, ln / 2))

# 5) 音乐：已按人声压低的配乐分轨
d.add_audio(f"{media}/配乐.wav", 0, dur, track="音乐", name="配乐（已压低）")

drafts_dir = os.path.expanduser(J.get("drafts_dir", "~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"))
existing = os.path.join(drafts_dir, name)
updating = os.path.isdir(existing) and "--new" not in sys.argv
if updating:
    folder = existing
    print("原地更新已有草稿，旧版本备份在", jy.prepare_update(folder))
else:
    folder = jy.new_draft_folder(J["shell"], drafts_dir, name)
L = d.save(folder)
n = {}
for t in d.d["tracks"]: n[t["type"]] = n.get(t["type"], 0) + 1
print("草稿：", folder, f"{L:.1f}s", n, "口播关键帧点", len(pts))
if updating:
    print("已原地更新：剪映里重新打开这个草稿即可（不用重新登记）")
elif do_register:
    jy.register(J.get("projects_root", "~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"), folder, name, L)
    print("已登记到剪映草稿列表，打开剪映即可看到")
