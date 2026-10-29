"""项目配置、共享库与目录约定（所有脚本共用）。

共享库（装一次，所有项目共用，不随项目复制）：
  $TTHE_HOME（默认 ~/.tech-talking-head-edit）
    config.json   全局默认配置：字体、剪映外壳草稿、包装层导出目录等（scripts/setup.py 生成）
    fonts/        字幕字体（得意黑）
    audio/        配乐、音效（fetch_audio.py 下载，按 Mixkit id 去重）
    stock/        B-roll（stock.py 下载，按 Mixkit id 去重）
项目目录（每条视频一个，只放这条视频自己的东西）：
  project.json  只写和全局不同的项（至少 source）；会覆盖 config.json 的同名项
  keep.json  comp.js  clips_map.json  audio.json（可选，没有就用共享库默认）
  assets/screenshots|official   本期截图、官方素材（每期不同）
  work/    中间文件（交付后可整个删除）
  output/  成片、字幕与画面文字、交付说明
"""
import json, os, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENGINE = os.path.join(SKILL, "scripts", "engine")
HOME = os.path.abspath(os.path.expanduser(os.environ.get("TTHE_HOME", "~/.tech-talking-head-edit")))


def merge(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def global_cfg():
    p = os.path.join(HOME, "config.json")
    return json.load(open(p)) if os.path.exists(p) else {}


class Project:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        p = os.path.join(self.root, "project.json")
        if not os.path.exists(p):
            sys.exit(f"找不到 {p}，先运行 scripts/init_project.py")
        self.local = json.load(open(p))
        self.cfg = merge(global_cfg(), self.local)
        self.work = self.path("work"); self.output = self.path("output")
        for d in (self.work, self.output):
            os.makedirs(d, exist_ok=True)
        self.fps = self.cfg.get("fps", 30)

    def path(self, *a):
        return os.path.join(self.root, *a)

    def find(self, rel, shared_sub=None):
        """先找项目里的文件，再找共享库（shared_sub 下同名文件）"""
        if os.path.isabs(rel): return rel
        p = self.path(rel)
        if os.path.exists(p) or not shared_sub: return p
        q = os.path.join(HOME, shared_sub, os.path.basename(rel))
        return q if os.path.exists(q) else p

    def config_file(self, name):
        """audio.json 等：项目里有就用项目的，否则用 skill 自带模板"""
        p = self.path(name)
        return p if os.path.exists(p) else os.path.join(SKILL, "templates", name)

    @property
    def source(self):
        s = os.path.expanduser(self.cfg["source"])
        return s if os.path.isabs(s) else self.path(s)

    @property
    def font(self):
        f = os.path.expanduser(self.cfg.get("font", "SmileySans-Oblique.ttf"))
        return f if os.path.isabs(f) else self.find(f, "fonts")

    @property
    def rough(self):
        return self.path("work", "rough.mov")

    @property
    def jianying_media(self):
        """剪映草稿素材目录（包装层、口播、人声等）。每个项目必须独立，否则同名文件互相覆盖、旧草稿失效：
        project.json 写了 jianying.media_dir → 原样使用；只有全局 config.json 写了 → <全局目录>/<项目文件夹名>；
        都没写 → <项目>/output/jianying_media。"""
        local = self.local.get("jianying", {}).get("media_dir")
        if local: return os.path.abspath(os.path.expanduser(local))
        g = global_cfg().get("jianying", {}).get("media_dir")
        if g: return os.path.join(os.path.abspath(os.path.expanduser(g)), os.path.basename(self.root))
        return self.path("output", "jianying_media")


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


if __name__ == "__main__":   # python3 proj.py <项目>：打印这个项目的剪映素材目录
    print(Project(sys.argv[1]).jianying_media)
