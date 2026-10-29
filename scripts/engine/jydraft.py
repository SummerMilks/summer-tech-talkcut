"""剪映专业版（Mac）草稿写入：只含本 skill 需要的视频 / 文字 / 音频 / 关键帧。

基于剪映 Mac 版明文 draft_info.json（11.x 实测可直接打开）。剪映版本升级可能改格式，出问题先看 references/jianying-export.md。
时间单位：接口用秒，内部微秒。坐标：剪映归一化坐标，x = 像素偏移 / (画布宽/2)，y = -像素偏移 / (画布高/2)（向上为正）。
"""
import copy, glob, json, os, shutil, subprocess, time, uuid

US = 1_000_000
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jy_templates")
SKEL, TEXT_TPL, MEDIA_TPL = (os.path.join(HERE, f) for f in ("skeleton.json", "text_template.json", "media_template.json"))
_KEEP_EXTRAS = ("speeds", "placeholder_infos", "canvases", "sound_channel_mappings", "material_colors", "vocal_separations")
JY_CACHE = os.path.expanduser("~/Movies/JianyingPro/User Data/Cache/effect")


def uid():
    return str(uuid.uuid4()).upper()


def _remap_ids(obj, mapping):
    """把对象里出现的旧 id 全部换成新 id（深度遍历字符串值）"""
    if isinstance(obj, dict):
        return {k: _remap_ids(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_remap_ids(v, mapping) for v in obj]
    if isinstance(obj, str) and obj in mapping:
        return mapping[obj]
    return obj


def fresh_ids(obj):
    """收集对象里所有 UUID 形式的 id，返回 旧id -> 新id 映射"""
    mapping = {}

    def _c(o):
        if isinstance(o, dict):
            v = o.get('id')
            if isinstance(v, str) and len(v) >= 32 and v.count('-') == 4:
                mapping.setdefault(v, uid())
            for x in o.values():
                _c(x)
        elif isinstance(o, list):
            for x in o:
                _c(x)
    _c(obj)
    return mapping


class Draft:
    def __init__(self, w=1920, h=1080, fps=30.0, name=''):
        self.d = json.load(open(SKEL))
        self.d['canvas_config'] = {'background': None, 'height': h, 'ratio': 'original', 'width': w}
        self.d['fps'] = fps
        self.d['id'] = uid()
        self.d['name'] = name
        self.d['materials'] = {}
        self.d['tracks'] = []
        self.tracks = {}      # key -> track dict
        self.order = []
        self.render_index = 0

    # ---------- 基础 ----------
    def mats(self, kind):
        return self.d['materials'].setdefault(kind, [])

    def track(self, key, ttype):
        if key not in self.tracks:
            t = {'attribute': 0, 'flag': 0, 'id': uid(), 'is_default_name': True, 'name': '',
                 'segments': [], 'type': ttype}
            self.tracks[key] = t
            self.d['tracks'].append(t)
        return self.tracks[key]

    def _bump(self, end_us):
        self.d['duration'] = max(self.d.get('duration', 0), end_us)

        # ---------- 文字 ----------
    def add_text(self, text, start, dur, track='text', size=8.0, color=(1, 1, 1), pos=(0.0, -0.8),
                 font=None, anim_in=None, anim_out=None, runs=None, bold=False, italic=0, shadow=None,
                 stroke=None, letter_spacing=0.0, scale=1.0, rotation=0.0, alpha=1.0, bg=None, align=1):
        """bg: dict(color=(r,g,b), alpha=0.9, radius=0.1, w=0.14, h=0.14) 剪映原生文字底框（对话气泡用）
        align: 0 左 1 中 2 右"""
        """runs: [(文字, (r,g,b)), ...] 多色（如强调词标红），给出时忽略 text/color
        shadow: dict(color=(r,g,b), alpha=0.9, distance=5, angle=-45, smooth=0.45)
        stroke: dict(color=(r,g,b), width=0.08, alpha=1)   italic: 倾斜角度（0 不斜）"""
        tpl = json.load(open(TEXT_TPL))
        tpl = _remap_ids(tpl, fresh_ids(tpl))
        m, s = tpl['material'], tpl['segment']
        mid, sid = uid(), uid()
        m['id'] = mid
        runs = runs or [(text, color)]
        text = ''.join(r[0] for r in runs)
        if font:
            fnt = {'id': font['obj'].get('resource_id', font['obj'].get('id', '')), 'path': font['obj'].get('path', '')}
            m['fonts'] = [font['obj']]
            m['font_resource_id'] = fnt['id']
            m['font_path'] = fnt['path']
        else:   # 剪映默认字体
            fnt = {'id': '', 'path': ''}
            m['fonts'] = []
            m['font_resource_id'] = ''
            m['font_path'] = ''
        styles, i = [], 0
        for t, c in runs:
            st = {'fill': {'content': {'render_type': 'solid', 'solid': {'color': list(c)}}}, 'font': fnt,
                  'size': size, 'useLetterColor': True, 'range': [i, i + len(t)]}
            if bold:
                st['bold'] = True
            if italic:
                st['italic'] = True
            if shadow:
                st['shadows'] = [{'diffuse': shadow.get('smooth', 0.45) / 70, 'alpha': shadow.get('alpha', 0.9),
                                  'distance': shadow.get('distance', 5.0),
                                  'content': {'render_type': 'solid',
                                              'solid': {'color': list(shadow.get('color', (0, 0, 0)))}},
                                  'angle': shadow.get('angle', -45)}]
            if stroke:
                st['strokes'] = [{'alpha': stroke.get('alpha', 1.0), 'content': {'render_type': 'solid', 'solid': {
                    'color': list(stroke.get('color', (0, 0, 0)))}}, 'width': stroke.get('width', 0.08) / 46,
                                  'mode': 0}]
            styles.append(st)
            i += len(t)
        m['content'] = json.dumps({'text': text, 'styles': styles}, ensure_ascii=False)
        m['font_size'] = size
        m['fixed_width'] = -1.0
        m['text_color'] = '#%02X%02X%02X' % tuple(int(c * 255) for c in runs[0][1])
        m['letter_spacing'] = letter_spacing
        m['bold_width'] = 0.008 if bold else 0.0
        m['italic_degree'] = italic or 0
        if shadow:
            m.update(has_shadow=True, shadow_alpha=shadow.get('alpha', 0.9), shadow_angle=shadow.get('angle', -45),
                     shadow_distance=shadow.get('distance', 5.0), shadow_smoothing=shadow.get('smooth', 0.45),
                     shadow_color='#%02X%02X%02X' % tuple(int(c * 255) for c in shadow.get('color', (0, 0, 0))))
        else:
            m['has_shadow'] = False
        m['alignment'] = align
        if bg:
            m.update(background_style=1, background_alpha=bg.get('alpha', 0.9),
                     background_color='#%02X%02X%02X' % tuple(int(c * 255) for c in bg.get('color', (0.22, 0.22, 0.22))),
                     background_round_radius=bg.get('radius', 0.1), background_height=bg.get('h', 0.14),
                     background_width=bg.get('w', 0.14))
        # check_flag 是剪映的样式开关位：7=基础，8=描边，16=背景，32=阴影；只写字段不打开对应位，剪映不显示
        m['check_flag'] = 7 | (8 if stroke else 0) | (16 if bg else 0) | (32 if shadow else 0)
        if stroke:
            m['border_width'] = stroke.get('width', 0.08)
            m['border_color'] = '#%02X%02X%02X' % tuple(int(c * 255) for c in stroke.get('color', (0, 0, 0)))
        self.mats('texts').append(m)
        refs = []
        anims = [a['obj'] for a in (anim_in, anim_out) if a]  # 动画对象需自备（本 skill 不内置剪映动画词表）
        if anims:
            aid = uid()
            self.mats('material_animations').append(
                {'animations': [copy.deepcopy(a) for a in anims], 'id': aid, 'multi_language_current': 'none',
                 'type': 'sticker_animation'})
            refs.append(aid)
        s['id'] = sid
        s['material_id'] = mid
        s['extra_material_refs'] = refs
        s['target_timerange'] = {'start': int(start * US), 'duration': int(dur * US)}
        s['clip']['transform'] = {'x': pos[0], 'y': pos[1]}
        sx, sy = (scale, scale) if not isinstance(scale, (tuple, list)) else scale
        s['clip']['scale'] = {'x': sx, 'y': sy}
        s['uniform_scale'] = {'on': sx == sy, 'value': 1.0}      # 样片「新模型」类大字：横 1.29 纵 3.53 拉长
        s['clip']['alpha'] = alpha
        s['clip']['rotation'] = rotation
        s['common_keyframes'] = []
        self.render_index += 1
        s['render_index'] = 20000 + self.render_index
        self.track(('text', track), 'text')['segments'].append(s)
        self._bump(int(start * US) + int(dur * US))
        return s

    def _split_overlaps(self):
        """同一轨道内有重叠的片段，拆到紧挨着的新轨道（剪映不允许同轨重叠）"""
        out = []
        for t in self.d['tracks']:
            segs = sorted(t['segments'], key=lambda s: s['target_timerange']['start'])
            lanes = []
            for sg in segs:
                st = sg['target_timerange']['start']
                for ln in lanes:
                    last = ln[-1]['target_timerange']
                    if last['start'] + last['duration'] <= st:
                        ln.append(sg)
                        break
                else:
                    lanes.append([sg])
            for i, ln in enumerate(lanes or [[]]):
                nt = dict(t) if i == 0 else dict(t, id=uid())
                nt['segments'] = ln
                out.append(nt)
        self.d['tracks'] = out

    # ---------- 保存 ----------
    def save(self, folder):
        """folder 必须是从一个可打开的剪映草稿克隆出来的文件夹（保留其 draft_meta_info.json 等）"""
        self._split_overlaps()
        txt = json.dumps(self.d, ensure_ascii=False)
        targets = [os.path.join(folder, 'draft_info.json'), os.path.join(folder, 'draft_info.json.bak')]
        tl = os.path.join(folder, 'Timelines')
        if os.path.isdir(tl):
            proj = json.load(open(os.path.join(tl, 'project.json')))
            tid = proj['main_timeline_id']
            self.d['id'] = tid
            txt = json.dumps(self.d, ensure_ascii=False)
            targets += [os.path.join(tl, tid, 'draft_info.json'), os.path.join(tl, tid, 'draft_info.json.bak')]
        for p in targets:
            if os.path.exists(os.path.dirname(p)):
                open(p, 'w').write(txt)
        return self.d['duration'] / US


def probe(path):
    import subprocess
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height:format=duration', '-of', 'json', path], capture_output=True, text=True)
    j = json.loads(r.stdout or '{}')
    st = (j.get('streams') or [{}])[0]
    return st.get('width', 1920), st.get('height', 1080), float(j.get('format', {}).get('duration', 0) or 0)


def _add_media(self, path, start, dur, src_start=0.0, track='main', pos=(0.0, 0.0), scale=1.0, alpha=1.0,
               volume=1.0, anim_in=None, anim_out=None, rotation=0.0):
    """path: 本地视频或图片；图片时长由 dur 决定。track='main' 为主轨（剪映会吸附，需连续摆放）"""
    ext = os.path.splitext(path)[1].lower()
    kind = 'photo' if ext in ('.png', '.jpg', '.jpeg', '.webp', '.bmp') else 'video'
    tpl = json.load(open(MEDIA_TPL))[kind]
    tpl = _remap_ids(tpl, fresh_ids(tpl))
    m, s = tpl['material'], tpl['segment']
    w, h, d = probe(path)
    m.update(path=path, width=w, height=h, material_name=os.path.basename(path),
             duration=int((d if kind == 'video' else 10800) * US), has_audio=(kind == 'video'))
    self.mats('videos').append(m)
    refs = []
    for e in tpl['extras']:
        if e['kind'] in _KEEP_EXTRAS:
            self.mats(e['kind']).append(e['obj'])
            refs.append(e['obj']['id'])
    anims = [a['obj'] for a in (anim_in, anim_out) if a]  # 动画对象需自备（本 skill 不内置剪映动画词表）
    if anims:
        aid = uid()
        self.mats('material_animations').append(
            {'animations': [copy.deepcopy(a) for a in anims], 'id': aid, 'multi_language_current': 'none',
             'type': 'sticker_animation'})
        refs.append(aid)
    s['material_id'] = m['id']
    s['extra_material_refs'] = refs
    s['target_timerange'] = {'start': int(start * US), 'duration': int(dur * US)}
    s['source_timerange'] = {'start': int(src_start * US), 'duration': int(dur * US)}
    s['clip'] = {'alpha': alpha, 'flip': {'horizontal': False, 'vertical': False}, 'rotation': rotation,
                 'scale': {'x': scale, 'y': scale}, 'transform': {'x': pos[0], 'y': pos[1]}}
    s['common_keyframes'] = []
    s['keyframe_refs'] = []
    s['volume'] = volume
    s['speed'] = 1.0
    self.render_index += 1
    s['render_index'] = self.render_index
    self.track(('video', track), 'video')['segments'].append(s)
    self._bump(int(start * US) + int(dur * US))
    return s


# ---------- 关键帧 ----------
_KF_PROP = {'scale': 'KFTypeScaleX', 'x': 'KFTypePositionX', 'y': 'KFTypePositionY', 'rotation': 'KFTypeRotation',
            'alpha': 'KFTypeAlpha'}


def add_keyframes(seg, prop, points, ease='inout', sub=4):
    """points: [(相对片段起点的秒, 值), ...]
    写成样片同款格式：curveType Line、控制柄全 0（剪映实测只认这种；样片 52 组关键帧全是这样）。
    ease='inout' 时在相邻两点之间插 sub 个 smoothstep 中间点，模拟两端缓动。"""
    pts = sorted(points)
    if ease == 'inout' and len(pts) > 1:
        out = [pts[0]]
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            if v1 != v0 and t1 - t0 > 0.12:
                for k in range(1, sub + 1):
                    u = k / (sub + 1)
                    e = u * u * (3 - 2 * u)
                    out.append((t0 + (t1 - t0) * u, v0 + (v1 - v0) * e))
            out.append((t1, v1))
        pts = out
    kfs = [{'curveType': 'Line', 'graphID': '', 'id': uid(), 'left_control': {'x': 0.0, 'y': 0.0},
            'right_control': {'x': 0.0, 'y': 0.0}, 'string_value': '', 'time_offset': int(t * US), 'values': [float(v)]}
           for t, v in pts]
    ck = seg.setdefault('common_keyframes', [])
    ck[:] = [k for k in ck if k['property_type'] != _KF_PROP[prop]]
    ck.append({'id': uid(), 'keyframe_list': kfs, 'material_id': '', 'property_type': _KF_PROP[prop]})
    return seg


def add_motion(seg, points, ease='inout'):
    """一次写齐 位置X/位置Y/缩放/旋转 四组关键帧（样片的关键帧总是四组一起出现）。
    points: [(秒, x, y, scale, rot)]，x/y 为剪映归一化坐标"""
    for k, prop in enumerate(('x', 'y', 'scale', 'rotation'), 1):
        add_keyframes(seg, prop, [(p[0], p[k]) for p in points], ease)
    return seg


# ---------- 音频轨 ----------
def _add_audio(self, path, start, dur=None, src_start=0.0, track='音频', volume=1.0, name=None, fade_in=0, fade_out=0):
    import subprocess
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                       capture_output=True, text=True)
    full = float(r.stdout.strip() or 0)
    dur = dur or (full - src_start)
    aid = uid()
    self.mats('audios').append({
        'app_id': 0, 'category_id': '', 'category_name': 'local', 'check_flag': 1, 'copyright_limit_type': 'none',
        'duration': int(full * US), 'effect_id': '', 'formula_id': '', 'id': aid, 'intensifies_path': '',
        'is_ai_clone_tone': False, 'is_text_edit_overdub': False, 'is_ugc': False, 'local_material_id': uid().lower(),
        'music_id': uid().lower(), 'name': name or os.path.basename(path), 'path': path, 'query': '', 'request_id': '',
        'resource_id': '', 'search_id': '', 'source_from': '', 'source_platform': 0, 'team_id': '', 'text_id': '',
        'tone_category_id': '', 'tone_category_name': '', 'tone_effect_id': '', 'tone_effect_name': '',
        'tone_platform': '', 'tone_second_category_id': '', 'tone_second_category_name': '', 'tone_speaker': '',
        'tone_type': '', 'type': 'extract_music', 'video_id': '', 'wave_points': []})
    refs = []
    for kind, obj in [('speeds', {'curve_speed': None, 'id': uid(), 'mode': 0, 'speed': 1.0, 'type': 'speed'}),
                      ('placeholder_infos', {'error_path': '', 'error_text': '', 'id': uid(), 'meta_type': 'none',
                                             'res_path': '', 'res_text': '', 'type': 'placeholder_info'}),
                      ('beats', {'ai_beats': {'beat_speed_infos': [], 'beats_path': '', 'beats_url': '',
                                              'melody_path': '', 'melody_percents': [0.0], 'melody_url': ''},
                                 'enable_ai_beats': False, 'gear': 404, 'gear_count': 0, 'id': uid(), 'mode': 404,
                                 'type': 'beats', 'user_beats': [], 'user_delete_ai_beats': None}),
                      ('sound_channel_mappings', {'audio_channel_mapping': 0, 'id': uid(), 'is_config_open': False,
                                                  'type': ''}),
                      ('vocal_separations', {'choice': 0, 'id': uid(), 'production_path': '', 'removed_sounds': [],
                                             'time_range': None, 'type': 'vocal_separation'})]:
        self.mats(kind).append(obj)
        refs.append(obj['id'])
    if fade_in or fade_out:
        fid = uid()
        self.mats('audio_fades').append({'fade_in_duration': int(fade_in * US), 'fade_out_duration': int(fade_out * US),
                                         'fade_type': 0, 'id': fid, 'type': 'audio_fade'})
        refs.append(fid)
    s = {'caption_info': None, 'cartoon': False, 'clip': None, 'common_keyframes': [], 'enable_adjust': False,
         'enable_color_correct_adjust': False, 'enable_color_curves': True, 'enable_color_match_adjust': False,
         'enable_color_wheels': True, 'enable_lut': False, 'enable_smart_color_adjust': False,
         'extra_material_refs': refs, 'group_id': '', 'hdr_settings': None, 'id': uid(), 'intensifies_audio': False,
         'is_placeholder': False, 'is_tone_modify': False, 'keyframe_refs': [], 'last_nonzero_volume': 1.0,
         'material_id': aid, 'render_index': 0, 'responsive_layout': {'enable': False, 'horizontal_pos_layout': 0,
                                                                      'size_layout': 0, 'target_follow': '',
                                                                      'vertical_pos_layout': 0},
         'reverse': False, 'source_timerange': {'start': int(src_start * US), 'duration': int(dur * US)},
         'speed': 1.0, 'target_timerange': {'start': int(start * US), 'duration': int(dur * US)},
         'template_id': '', 'template_scene': 'default', 'track_attribute': 0, 'track_render_index': 0,
         'uniform_scale': None, 'visible': True, 'volume': volume}
    self.track(('audio', track), 'audio')['segments'].append(s)
    self._bump(int(start * US) + int(dur * US))
    return s


Draft.add_media = _add_media
Draft.add_audio = _add_audio


def font(resource_id, title=""):
    """剪映字库字体：资源 ID → 本机剪映缓存里的字体文件（需先在剪映里用过一次该字体，让它下载到缓存）"""
    files = [f for f in glob.glob(f"{JY_CACHE}/{resource_id}/*/*") if f.lower().endswith((".ttf", ".otf", ".ttc"))]
    path = files[0] if files else ""
    return {"obj": {"category_id": "", "category_name": "", "effect_id": resource_id, "file_uri": "", "id": uid(),
                    "path": path, "request_id": "", "resource_id": resource_id, "source_platform": 0, "team_id": "",
                    "third_resource_id": "", "title": title}, "path": path}


def new_draft_folder(shell, drafts_dir, name):
    """从用户自己的空草稿（外壳）克隆一个草稿文件夹。外壳必须是剪映新建后正常退出的空草稿。"""
    dst = os.path.join(os.path.expanduser(drafts_dir), name)
    if os.path.exists(dst):
        raise FileExistsError(f"草稿已存在：{dst}（换个名字，或确认后手动删除）")
    shutil.copytree(os.path.expanduser(shell), dst, symlinks=True)
    return dst


def prepare_update(folder):
    """原地更新已有草稿：剪映打开过的草稿会把 draft_info.json 加密并生成 crypto_key_store.dat。
    先把当前文件备份到 <草稿>/.tthe_backup/<时间>/，再移走密钥，之后 save() 写回明文。返回备份目录。"""
    bk = os.path.join(folder, ".tthe_backup", time.strftime("%Y%m%d_%H%M%S"))
    os.makedirs(bk)
    rel = ["draft_info.json", "draft_info.json.bak", "draft_meta_info.json", "crypto_key_store.dat", "crypto_key_store.dat.bak"]
    tl = os.path.join(folder, "Timelines", "project.json")
    if os.path.exists(tl):
        tid = json.load(open(tl))["main_timeline_id"]
        rel += [f"Timelines/{tid}/draft_info.json", f"Timelines/{tid}/draft_info.json.bak"]
    for r in rel:
        src = os.path.join(folder, r)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(os.path.join(bk, r)), exist_ok=True)
            shutil.copy2(src, os.path.join(bk, r))
    for r in ("crypto_key_store.dat", "crypto_key_store.dat.bak"):
        if os.path.exists(os.path.join(folder, r)): os.remove(os.path.join(folder, r))
    return bk


def register(projects_root, folder, name, duration_s=0):
    """把草稿登记进剪映草稿列表（root_meta_info.json）。剪映必须已退出；改之前自动备份。
    folder 不在 projects_root 里时，在 projects_root 下建软链接指过去（方便草稿实体放外接盘）。"""
    if subprocess.run(["pgrep", "-x", "VideoFusion-macOS"], capture_output=True).stdout:
        raise RuntimeError("剪映正在运行，请先完全退出剪映再登记")
    projects_root = os.path.expanduser(projects_root)
    link = os.path.join(projects_root, name)
    if os.path.abspath(folder) != os.path.abspath(link) and not os.path.lexists(link):
        os.symlink(folder, link)
    rp = os.path.join(projects_root, "root_meta_info.json")
    shutil.copy(rp, rp + f".bak.{int(time.time())}")
    rm = json.load(open(rp))
    now = int(time.time() * 1e6)
    old = [e for e in rm["all_draft_store"] if e["draft_name"] == name]
    if old:
        e = old[0]
    else:
        if not rm["all_draft_store"]:
            raise RuntimeError("剪映草稿列表为空：先在剪映里新建任意一个草稿（外壳草稿即可）再登记")
        e = copy.deepcopy(rm["all_draft_store"][0])
        e["draft_id"] = uid(); e["tm_draft_create"] = now
        rm["all_draft_store"].insert(0, e)
    e.update(draft_name=name, draft_fold_path=link, draft_json_file=f"{link}/draft_info.json", draft_cover=f"{link}/draft_cover.jpg",
             tm_draft_modified=now, tm_duration=int(duration_s * US), draft_timeline_materials_size=0,
             draft_is_invisible=False, tm_draft_removed=0)
    rm["draft_ids"] = len(rm["all_draft_store"])
    json.dump(rm, open(rp, "w"), ensure_ascii=False)
