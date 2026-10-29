"""新建剪辑项目：python3 scripts/init_project.py <项目目录> <口播原片路径>
只建这条视频自己的文件：project.json（写原片路径）、comp.js、clips_map.json、keep.json 由后续步骤写。
字体、配乐音效、B-roll、剪映设置都在共享库（scripts/setup.py 装一次），不复制进项目。"""
import json, os, shutil, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from proj import HOME, SKILL

root, src = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
for d in ("assets/screenshots", "assets/official", "work", "output"):
    os.makedirs(os.path.join(root, d), exist_ok=True)
T = os.path.join(SKILL, "templates")
if not os.path.exists(f"{root}/project.json"):
    cfg = json.load(open(f"{T}/project.example.json")); cfg["source"] = src; cfg.pop("_说明", None)
    json.dump(cfg, open(f"{root}/project.json", "w"), ensure_ascii=False, indent=2)
for a, b in (("clips_map.example.json", "clips_map.json"), ("comp.example.js", "comp.js")):
    if not os.path.exists(f"{root}/{b}"): shutil.copy(f"{T}/{a}", f"{root}/{b}")
print("项目已建：", root)
if not os.path.exists(os.path.join(HOME, "config.json")):
    print("⚠️ 还没装共享库：先运行一次 python3 scripts/setup.py（字体、配乐音效、剪映设置，只需一次）")
