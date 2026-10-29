"""口播粗剪：转写 → 写保留区间 → 吸附静音边界导出 → 复核。

  python3 roughcut.py transcribe <项目>          抽音频、静音检测、whisper.cpp 逐字转写，打印带编号的句子
  python3 roughcut.py words <项目> <句号...>      打印指定句子的逐字时间
  python3 roughcut.py render <项目>              按 keep.json 导出 work/rough.mov + work/cuts.json
  python3 roughcut.py verify <项目>              对粗剪重新转写并打印（查残留重复、半截话；结果供校字幕）
keep.json: {"keep": [[起秒, 止秒, "备注"], ...]}，起止只需大致落在保留段首尾的静音里，脚本吸附到真实开口/收声点。
转写模型：环境变量 WHISPER_MODEL（默认 ~/.cache/whisper/ggml-large-v3-turbo-q5_0.bin），语言见 project.json → lang。
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from proj import Project, duration

MODEL = os.path.expanduser(os.environ.get("WHISPER_MODEL", "~/.cache/whisper/ggml-large-v3-turbo-q5_0.bin"))
SIL_DB, SIL_DUR = -35, 0.25
PRE, POST = 0.12, 0.22                # 段首 / 段尾气口
LONG_PAUSE, KEEP_PAUSE = 0.65, 0.38   # 段内超过 LONG_PAUSE 秒的停顿压到 KEEP_PAUSE 秒


def transcribe(P, wav, base, prompt=None):
    lang = P.cfg.get("lang", "zh")
    prompt = prompt or P.cfg.get("asr_prompt", "以下是普通话的句子，包含标点符号。")
    # 不要加 --vad：开了以后整句时间换算回原片，逐字时间不会，越往后偏得越多
    subprocess.run(["whisper-cli", "-m", MODEL, "-f", wav, "-l", lang, "-fa", "-mc", "0", "-ojf", "-of", base,
                    "--prompt", prompt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    res = []
    for s in json.load(open(base + ".json"))["transcription"]:
        words = [{"s": t["offsets"]["from"] / 1000, "e": t["offsets"]["to"] / 1000, "w": t["text"]}
                 for t in s["tokens"] if not t["text"].startswith("[_") and t["text"].strip()]
        if words:
            res.append({"start": s["offsets"]["from"] / 1000, "end": s["offsets"]["to"] / 1000, "text": s["text"].strip(), "words": words})
    bad = [s for s in res if abs(s["words"][0]["s"] - s["start"]) > 1.5]
    if bad:
        sys.exit(f"逐字时间与整句时间错位 {len(bad)} 处（{bad[0]['start']:.1f}s {bad[0]['text']}），时间轴不可信，停止排查")
    json.dump(res, open(base + ".sent.json", "w"), ensure_ascii=False)
    return res


def silences(wav):
    r = subprocess.run(["ffmpeg", "-i", wav, "-af", f"silencedetect=noise={SIL_DB}dB:d={SIL_DUR}", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    out, st = [], None
    for line in r.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m: st = float(m.group(1)); continue
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and st is not None: out.append((st, float(m.group(1)))); st = None
    return out


def plan(keep, S, dur):
    """每个保留区间 → 若干子片段：吸附到静音检测出的说话岛，段内长停顿压缩。
    逐字时间首尾相连，不能用来判断停顿，边界一律按静音检测定。"""
    isl, t = [], 0.0
    for a, b in S:
        if a > t: isl.append((t, a))
        t = max(t, b)
    if t < dur: isl.append((t, dur))
    pieces = []
    for k in keep:
        a, b = k[0], k[1]
        I = [x for x in isl if x[1] > a and x[0] < b]
        if not I: continue
        I[0] = (max(I[0][0], a), I[0][1]); I[-1] = (I[-1][0], min(I[-1][1], b))
        groups = [[I[0][0], I[0][1]]]
        for s, e in I[1:]:
            if s - groups[-1][1] > LONG_PAUSE: groups.append([s, e])
            else: groups[-1][1] = e
        half = KEEP_PAUSE / 2
        for j, (s, e) in enumerate(groups):
            pre = PRE if j == 0 else half
            post = POST if j == len(groups) - 1 else half
            pieces.append([round(max(0, s - pre), 3), round(min(dur, e + post), 3), k[2] if len(k) > 2 else ""])
    return pieces


def wav_of(src, wav):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)


if __name__ == "__main__":
    cmd, P = sys.argv[1], Project(sys.argv[2])
    W = P.work
    if cmd == "transcribe":
        wav_of(P.source, f"{W}/src.wav")
        for i, s in enumerate(transcribe(P, f"{W}/src.wav", f"{W}/src")):
            print(i, f"{s['start']:.2f}-{s['end']:.2f}", s["text"])
    elif cmd == "words":
        d = json.load(open(f"{W}/src.sent.json"))
        for i in map(int, sys.argv[3:]):
            print(i, " ".join(f"{x['w'].strip()}@{x['s']:.2f}" for x in d[i]["words"]))
    elif cmd == "render":
        keep = json.load(open(P.path("keep.json")))["keep"]
        if not os.path.exists(f"{W}/src.wav"): wav_of(P.source, f"{W}/src.wav")
        pieces = plan(keep, silences(f"{W}/src.wav"), duration(P.source))
        fc, cat = [], ""
        for k, (i, o, _) in enumerate(pieces):
            L = o - i
            fc.append(f"[0:v]trim={i:.3f}:{o:.3f},setpts=PTS-STARTPTS[v{k}]")
            fc.append(f"[0:a]atrim={i:.3f}:{o:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={L - 0.015:.3f}:d=0.015[a{k}]")
            cat += f"[v{k}][a{k}]"
        fc.append(f"{cat}concat=n={len(pieces)}:v=1:a=1[v][a]")
        open(f"{W}/rough_filter.txt", "w").write(";\n".join(fc))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", P.source, "-filter_complex_script", f"{W}/rough_filter.txt",
                        "-map", "[v]", "-map", "[a]", "-r", str(P.fps), "-c:v", "libx264", "-preset", "medium", "-crf", "14",
                        "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", P.rough], check=True)
        json.dump(pieces, open(f"{W}/cuts.json", "w"), ensure_ascii=False)
        print(len(pieces), "pieces", round(sum(o - i for i, o, _ in pieces), 2), "s →", P.rough)
    elif cmd == "verify":
        wav_of(P.rough, f"{W}/rough.wav")
        for s in transcribe(P, f"{W}/rough.wav", f"{W}/rough", P.cfg.get("asr_prompt_terms")):
            print(f"{s['start']:.2f}-{s['end']:.2f}", s["text"])
    else:
        sys.exit(__doc__)
