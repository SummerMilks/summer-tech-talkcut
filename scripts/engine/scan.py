"""字幕与画面文字的风险词扫描：python3 scan.py <项目> [文本文件]
默认扫 output/字幕与画面文字.txt（render.py text 导出）。规则：
  BLOCK  绝对化/最高级/排名（参考《广告法》第九条与市场监管总局绝对化用语执法指南）、保证结果与收益承诺
  REVIEW 数据与引用来源、数字结论、商业推广、AI 生成合成、高风险行业、"第一"的语境
project.json → scan: {"block": [额外禁用词], "review": [额外复核词]} 可按账号加严。
注意：
  - 口播原话里的比较说法（如"门槛最低"）字幕要照录，但画面文字不要再写；BLOCK 命中口播时，要么改口播，要么由人判断后放行。
  - 截图和官方素材里的文字不在扫描范围，必须人工看一遍（常见："World's First""most capable""#1"）。
  - 自动扫描通过不等于平台一定过审。"""
import json, os, re, sys

BLOCK = [("ABSOLUTE", "绝对化、最高级或排名", r"全球第一|全世界第一|世界第一|全国第一|全网第一|行业第一|领域第一|第一名|国家级|最高级|最佳|最强|最好|最优|最先进|顶级|唯一|首个|首发|首家|天花板|史上最|遥遥领先|绝无仅有|独一无二|万能|永久"),
         ("GUARANTEE", "保证结果或收益承诺", r"100%|百分百|保证(?:你|能|可以|实现|达到|获得)?|一定能|肯定能|稳赚|保本|保底收益|包回报|固定回报|快速回报|无风险|零风险|永久有效|立竿见影")]
REVIEW = [("SOURCE", "数据/研究/引用：需写清出处、日期和范围", r"数据显示|数据表明|研究显示|研究表明|调查显示|报告指出|专家表示|专家说|据统计|据报道|据.{1,12}报道"),
          ("NUMBER", "数字结论：判断是否需要标来源", r"\d+(?:\.\d+)?\s*(?:%|％|万|亿|倍|元|美元|人|家|年|个月|天)"),
          ("COMMERCIAL", "可能构成商业推广：确认是否需要广告/合作标识", r"赞助|广告|商务合作|品牌合作|返佣|佣金|购买链接|下单|优惠券|课程|咨询服务|链接在"),
          ("AI_LABEL", "可能涉及 AI 生成合成：按平台规则标识", r"AI生成|人工智能生成|数字人|虚拟人|换脸|克隆声音|声音克隆|合成画面|生成图片|生成视频"),
          ("HIGH_RISK", "高风险领域：人工核验资质与专项规则", r"股票|个股|荐股|融资|募资|众筹|证券|基金|期货|保险|医疗|药品|保健品|治疗|疗效|教育培训|保过|招商加盟|房地产|法律建议|未成年人|时政|政策解读"),
          ("FIRST", "出现“第一”：确认只是顺序表达", r"第一(?!次|步|阶段|部分|章|节|期|集|天|周|月|年|人称|视角)")]

root = os.path.abspath(sys.argv[1])
f = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "output", "字幕与画面文字.txt")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proj import Project
cfg = Project(root).cfg.get("scan", {})
if cfg.get("block"): BLOCK.append(("CUSTOM_BLOCK", "账号自定义禁用词", "|".join(map(re.escape, cfg["block"]))))
if cfg.get("review"): REVIEW.append(("CUSTOM_REVIEW", "账号自定义复核词", "|".join(map(re.escape, cfg["review"]))))
text = open(f).read(); nb = nr = 0
for sev, rules in (("BLOCK", BLOCK), ("REVIEW", REVIEW)):
    for rid, label, rx in rules:
        hits = sorted(set(m.group(0) for m in re.finditer(rx, text, re.I)))
        if hits:
            print(f"[{sev}] {rid}: {label}；命中：{'、'.join(hits)}")
            nb += sev == "BLOCK"; nr += sev == "REVIEW"
print("自动扫描结果:", "BLOCK" if nb else "REVIEW" if nr else "PASS")
sys.exit(2 if nb else 0)
