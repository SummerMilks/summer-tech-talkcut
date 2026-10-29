"""混音滤镜图（mix.py 与 stems.py 共用，保证成片与剪映分轨听感一致）。
人声：高通 75Hz + 轻降噪 + 压缩；配乐：分段交叉、被人声侧链压低；音效：按 work/cues.json 摆放。"""
import json, os
from proj import HOME


def audio_file(P, item, kind):
    """项目 assets/audio 优先，其次共享库 audio/（fetch_audio.py 下载一次，所有项目共用）"""
    name = item.get("file") or f"{kind}_{item['mixkit']}.mp3"
    if os.path.isabs(os.path.expanduser(name)): return os.path.expanduser(name)
    return P.find(os.path.join("assets", "audio", name), "audio")


def build(P, dur, gain_db=None, split_stems=False):
    """返回 (inputs, filter_lines, sfx_clips)。gain_db=None → 末端 loudnorm 到 -16 LUFS（成片）；
    给定 gain_db → 不做 loudnorm，三条分轨各乘同一增益（剪映分轨）。"""
    cfg = json.load(open(P.config_file("audio.json")))
    cues = json.load(open(P.path("work", "cues.json")))
    inputs, fc = ["-i", P.rough], []
    fc.append("[0:a]aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=75,afftdn=nf=-28,"
              "acompressor=threshold=-21dB:ratio=3:attack=8:release=120:makeup=2,asplit=2[voice0][sc]")
    mus = []
    for k, m in enumerate(cfg["music"]):
        a, b = m["from"], min(m["to"], dur)
        if b - a < 1: continue                      # 片子比配乐表短：跳过开始得太晚的段
        i = len(inputs) // 2; inputs += ["-i", audio_file(P, m, "music")]
        fi, fo, off = m.get("fade_in", .8), min(m.get("fade_out", 1.2), (b - a) / 2), m.get("offset", 0)
        fc.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim={off}:{off + b - a},asetpts=PTS-STARTPTS,"
                  f"volume={m['gain']}dB,afade=t=in:d={fi},afade=t=out:st={b - a - fo:.3f}:d={fo},adelay={int(a * 1000)}|{int(a * 1000)}[m{k}]")
        mus.append(f"[m{k}]")
    if not mus: fc.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{dur}[m_empty]"); mus = ["[m_empty]"]
    fc.append(f"{''.join(mus)}amix=inputs={len(mus)}:normalize=0:duration=longest[mraw]")
    fc.append("[mraw][sc]sidechaincompress=threshold=0.04:ratio=5:attack=40:release=450:makeup=1[music0]")
    tags, clips = [], []
    for k, c in enumerate(cues):
        s = cfg["sfx"].get(c["sfx"])
        if not s: continue
        f = audio_file(P, s, "sfx"); i = len(inputs) // 2; inputs += ["-i", f]
        ss, ln = s.get("ss", 0), s.get("len", 3)
        t = max(0, c["t"] + s.get("shift", 0)); g = cfg["sfx_base_db"] + s.get("gain", 0) + c["gain"]
        fc.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim={ss}:{ss + ln},asetpts=PTS-STARTPTS,"
                  f"afade=t=out:st={max(0, ln - 0.15):.3f}:d=0.15,volume={g}dB,adelay={int(t * 1000)}|{int(t * 1000)}[s{k}]")
        tags.append(f"[s{k}]")
        clips.append({"file": f, "name": c["sfx"], "start": round(t, 3), "ss": ss, "len": ln, "gain_db": g + (gain_db or 0)})
    if not tags: fc.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{dur}[s_empty]"); tags = ["[s_empty]"]
    fc.append(f"{''.join(tags)}amix=inputs={len(tags)}:normalize=0:duration=longest[sfx0]")
    if gain_db is None:
        fc.append(f"[voice0][music0][sfx0]amix=inputs=3:normalize=0:duration=first,atrim=0:{dur},"
                  "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[out]")
    else:
        G = f"volume={gain_db:.2f}dB,atrim=0:{dur},apad=whole_dur={dur}"
        for n in ("voice", "music", "sfx"):
            fc.append(f"[{n}0]{G},asplit=2[{n}][{n}_s]")
        fc.append("[voice_s][music_s][sfx_s]amix=inputs=3:normalize=0:duration=first,ebur128[sum]")
    return inputs, fc, clips
