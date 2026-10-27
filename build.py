# -*- coding: utf-8 -*-
"""
وجوه العيش — Faces of Livelihood
يبني الموقع الثابت في dist/ من:
  data/faces.json   (البيانات الوصفية والنص العربي — يولّدها tools/extract.py)
  data/en/p*.py     (الترجمة الإنجليزية وملاحظات المترجم)
  images/NN.jpg     (الصور الأصلية)
  site/             (css, js, fonts)
تشغيل:  python3 build.py
"""
import glob
import html
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
SITE = ROOT / "site"

# ———— مجموعات الأصل (للفلترة) ————
# origin_en → (مفتاح, عربي, إنجليزي)
GROUPS = [
    ("saudi", "السعودية", "Saudi Arabia", {"Saudi Arabia"}),
    ("pakistan", "باكستان", "Pakistan", {"Pakistan", "Punjab", "Punjab (Pakistan)"}),
    ("sudan", "السودان", "Sudan", {"Sudan", "Rashaida (Sudan)"}),
    ("bengal", "بنغلاديش والبنغال", "Bangladesh & Bengal", {"Bangladesh", "Bengal"}),
    ("burma", "بورما والروهنجيا", "Burma & Rohingya", {"Burma", "Burma (Rohingya)", "Rohingya"}),
    ("yemen", "اليمن", "Yemen", {"Yemen"}),
    ("pashtun", "البشتون", "Pashtun", {"Pashtun"}),
    ("egypt", "مصر", "Egypt", {"Egypt", "Egypt (Beheira)"}),
    ("afghanistan", "أفغانستان", "Afghanistan", {"Afghanistan"}),
    ("tuareg", "الطوارق", "Tuareg", {"Tuareg"}),
    ("turkestan", "تركستان", "Turkestan", {"Turkestan"}),
    ("westafrica", "غرب أفريقيا", "West Africa", {"West Africa"}),
    ("india", "الهند", "India", {"India (Bombay)"}),
]
GROUP_OF = {o: g for g in GROUPS for o in g[3]}

# نقطة التركيز عند قصّ المصغّرات 4:5 (x, y) من 0 إلى 1
DEFAULT_FOCUS = (0.5, 0.36)
FOCUS = {
    "46": (0.5, 0.5),
}

CREDITS = {}

AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
EN_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
HERO_IDS = ["02", "05", "07", "09", "12", "15", "28", "29"]


def esc(s):
    return html.escape(s or "", quote=True)


def ar_digits(s):
    return str(s).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))


def date_ar(d):
    y, m, dd = d.split("-")
    return f"{ar_digits(int(dd))} {AR_MONTHS[int(m)-1]} {ar_digits(y)}"


def date_en(d):
    y, m, dd = d.split("-")
    return f"{EN_MONTHS[int(m)-1]} {int(dd)}, {y}"


# ———— عرض النص: فقرات وأبيات وحواشٍ ————
def render_text(text):
    out = []
    for para in re.split(r"\n\s*\n", text.strip()):
        verse = []

        def flush():
            if verse:
                if len(verse) == 1:
                    cls = ' class="sig"' if re.match(r"^[—–-]\s", verse[0]) else ""
                    out.append(f"<p{cls}>{esc(verse[0])}</p>")
                else:
                    out.append('<p class="verse">' + "<br>".join(esc(v) for v in verse) + "</p>")
                verse.clear()

        for line in para.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("*("):
                flush()
                out.append(f'<p class="fn">{esc(line)}</p>')
            elif len(line) > 95:
                flush()
                out.append(f"<p>{esc(line)}</p>")
            else:
                verse.append(line)
        flush()
    return "\n".join(out)


def load_data():
    faces = json.load(open(ROOT / "data" / "faces.json", encoding="utf-8"))
    T = {}
    for f in sorted(glob.glob(str(ROOT / "data" / "en" / "p*.py"))):
        ns = {}
        exec(open(f, encoding="utf-8").read(), ns)
        T.update(ns["T"])
    ids = [x["id"] for x in faces]
    missing = [i for i in ids if i not in T]
    if missing:
        raise SystemExit(f"ترجمة ناقصة: {missing}")
    for x in faces:
        t = T[x["id"]]
        x["text_en"] = t["en"]
        x["notes_en"] = t.get("notes", [])
        o = x.get("origin_en")
        x["group"] = GROUP_OF[o][0] if o in GROUP_OF else None
        x["credit"] = CREDITS.get(x["id"])
        x["en_label"] = x["en_label"].replace("'", "’")
    return faces


# ———— الصور ————
def build_images(faces):
    (DIST / "img").mkdir(parents=True, exist_ok=True)
    for x in faces:
        src = ROOT / "images" / f"{x['id']}.jpg"
        shutil.copy(src, DIST / "img" / f"{x['id']}.jpg")
        im = Image.open(src).convert("RGB")
        fx, fy = FOCUS.get(x["id"], DEFAULT_FOCUS)
        th = ImageOps.fit(im, (640, 800), Image.LANCZOS, centering=(fx, fy))
        th.save(DIST / "img" / f"{x['id']}-t.jpg", quality=82, optimize=True, progressive=True)
    # صورة المشاركة (فسيفساء وجوه بلا نص)
    ids = ["02", "05", "12", "15", "28", "29"]
    W, H = 1200, 630
    w = W // len(ids)
    og = Image.new("RGB", (W, H), "#17120e")
    for i, k in enumerate(ids):
        im = Image.open(ROOT / "images" / f"{k}.jpg").convert("RGB")
        fx, fy = FOCUS.get(k, DEFAULT_FOCUS)
        og.paste(ImageOps.fit(im, (w, H), Image.LANCZOS, centering=(fx, 0.3)), (i * w, 0))
    og.save(DIST / "img" / "og.jpg", quality=84, optimize=True)


# ———— القوالب ————
def layout(*, title, desc, rel, body, og="img/og.jpg", body_class="", extra_head="", scripts=""):
    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ar_AR">
<meta property="og:locale:alternate" content="en_US">
<meta property="og:image" content="{rel}{og}">
<meta name="twitter:card" content="summary_large_image">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="{rel}favicon.svg" type="image/svg+xml">
<link rel="preload" href="{rel}fonts/thmanyahserifdisplay-Black.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{rel}css/style.css">
{extra_head}
</head>
<body class="{body_class}">
<a class="skip" href="#main">تخطَّ إلى المحتوى · Skip to content</a>
<header class="top">
  <a class="brand" href="{rel}"><span class="brand-ar">الوجوه</span><span class="brand-en" lang="en" dir="ltr">An Unread Language</span></a>
  <nav aria-label="Main">
    <a href="{rel}about/">عن المشروع<span lang="en" dir="ltr">About</span></a>
  </nav>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <div class="wrap foot-in">
    <p>الصور والنصوص: ماجد الأهدل · ٢٠١٦–٢٠١٨</p>
    <p lang="en" dir="ltr">Photographs and texts by Majed Al-Ahdal, 2016–2018</p>
  </div>
</footer>
{scripts}
</body>
</html>
"""


def tile(x, rel):
    label = f'<span class="t-ar">{esc(x["ar_label"])}</span><span class="t-en" lang="en" dir="ltr">{esc(x["en_label"])}</span>'
    origin = ""
    if x["origin_ar"]:
        origin = f'<span class="t-origin">{esc(x["origin_ar"])} <i lang="en" dir="ltr">{esc(x["origin_en"])}</i></span>'
    grp = f' data-group="{x["group"]}"' if x["group"] else ""
    return f"""<a class="tile" href="{rel}face/{x['id']}/"{grp}>
  <span class="t-img"><img src="{rel}img/{x['id']}-t.jpg" width="640" height="800" loading="lazy" decoding="async" alt="{esc(x['ar_label'])} — {esc(x['en_label'])}"></span>
  <span class="t-meta"><span class="t-num"><b>{ar_digits(int(x['id']))}</b><i lang="en" dir="ltr">{x['id']}</i></span>{origin}</span>
  {label}
</a>"""


def page_index(faces):
    rel = ""
    counts = {}
    for x in faces:
        if x["group"]:
            counts[x["group"]] = counts.get(x["group"], 0) + 1
    chips = ['<button class="chip is-on" data-g="">الكل <i lang="en" dir="ltr">All</i><em>{}</em></button>'.format(len(faces))]
    for key, ar, en, _ in sorted(GROUPS, key=lambda g: -counts.get(g[0], 0)):
        if counts.get(key):
            chips.append(f'<button class="chip" data-g="{key}">{ar} <i lang="en" dir="ltr">{en}</i><em>{counts[key]}</em></button>')
    strip = "".join(
        f'<a href="face/{k}/" tabindex="-1" aria-hidden="true"><img src="img/{k}-t.jpg" alt="" loading="eager" width="640" height="800"></a>'
        for k in HERO_IDS
    )
    n = len(faces)
    tiles = "\n".join(tile(x, rel) for x in faces)
    body = f"""
<section class="hero wrap">
  <p class="kicker"><span>مكة والمدينة وجدة · ٢٠١٦–٢٠١٨</span><span lang="en" dir="ltr">Makkah, Madinah &amp; Jeddah · 2016–2018</span></p>
  <h1><span class="h-ar">الوجوه<span class="sr">:</span></span><span class="h-sub">لغةٌ مات قارئوها</span><span class="h-en" lang="en" dir="ltr">Faces: <em>An Unread Language</em></span></h1>
  <div class="intro">
    <div class="intro-ar" lang="ar" dir="rtl"><p class="lead">«في وجوه الكادحين لغةٌ مات قارئوها في حادث اصطدامٍ شنيعٍ مع الرفاه». كتب ماجد الأهدل هذه العبارة عام ٢٠١٦ تحت أحد وجوه سلسلته «Proletarian»، ومنها يأخذ العمل اسمه.</p><p>يضمّ المشروع ستّةً وأربعين وجهًا التقطها بين ٢٠١٦ و٢٠١٨ في أسواق مكة وطرقاتها ومشاعرها، وأحيانًا في المدينة وجدّة. فيهم عمّالٌ وباعةٌ وخبّازون وجزّارون جاؤوا من باكستان وبنغلاديش والسودان وبورما وأفغانستان وغرب أفريقيا واليمن ومصر. وفيهم حجّاجٌ من بلادٍ شتّى، بينهم سعوديّون في مخيّمات الحجّ. ويرافق كلَّ وجهٍ نصّ: بعضه بصوت صاحبه، وبعضه عنه، وبعضه تأمّلٌ يبدأ من الوجه ويمضي إلى الأدب والتاريخ.</p><p>لا يقدّم العمل هذه الوجوه على أنّها غامضة أو غريبة، بل على أنّها نصوصٌ مكتوبةٌ بوضوح: بالتعب والغربة والانتظار والشيخوخة، وبالضحك أيضًا. الغائب هو القارئ. ومكة، المدينة التي يلتقي فيها هؤلاء جميعًا، تجعل السؤال أشدّ: كيف يمرّ المرء كلَّ يومٍ بكلّ هذه الوجوه ولا يقرأ منها شيئًا؟</p></div>
    <div class="intro-en" lang="en" dir="ltr"><p class="lead">“In the faces of laborers there is a language whose readers died in a terrible collision with prosperity.” Majed Al-Ahdal wrote this line in 2016 beneath one of the portraits in his series <i>Proletarian</i>, and the work takes its name from it.</p><p>The project gathers forty-six faces photographed between 2016 and 2018 in the markets, streets, and pilgrimage sites of Makkah, and sometimes in Madinah and Jeddah. Among them are laborers, vendors, bakers, and butchers from Pakistan, Bangladesh, Sudan, Burma, Afghanistan, West Africa, Yemen, and Egypt, and pilgrims from many lands, Saudis among them in the Hajj camps. Each face is accompanied by a text: some in the sitter’s own voice, some about them, and some long reflections that begin with a face and travel on into literature and history.</p><p>The work does not present these faces as obscure or exotic. It presents them as texts written plainly, in fatigue, exile, waiting, old age, and laughter too. What is missing is the reader. And Makkah, the city where all of them meet, sharpens the question: how does one pass so many faces every day and read nothing in them?</p></div>
  </div>
  <div class="strip" aria-hidden="true">{strip}</div>
</section>

<section class="faces wrap" id="faces">
  <div class="faces-head">
    <h2>الوجوه <i lang="en" dir="ltr">The Faces</i></h2>
    <p class="count"><span id="shown">{ar_digits(n)}</span> من {ar_digits(n)} <i lang="en" dir="ltr">of {n}</i></p>
  </div>
  <div class="chips" role="group" aria-label="تصفية حسب الأصل · Filter by origin">
    {''.join(chips)}
  </div>
  <div class="grid" id="grid">
{tiles}
  </div>
</section>
"""
    return layout(
        title="الوجوه: لغةٌ مات قارئوها — Faces: An Unread Language",
        desc="«في وجوه الكادحين لغةٌ مات قارئوها في حادث اصطدامٍ شنيعٍ مع الرفاه». ستّةٌ وأربعون وجهًا ونصوصها بالعربية مترجمة إلى الإنجليزية · Forty-six faces from Makkah, with texts in Arabic and English.",
        rel=rel, body=body, body_class="home", scripts='<script src="js/main.js" defer></script>',
    )


def page_face(x, prev, nxt, faces):
    rel = "../../"
    meta_ar, meta_en = [], []
    if x["origin_ar"]:
        meta_ar.append(f'<span class="m-origin">{esc(x["origin_ar"])}</span>')
        meta_en.append(f'<span class="m-origin">{esc(x["origin_en"])}</span>')
    if x["place_ar"]:
        meta_ar.append(f'<span>{esc(x["place_ar"])}</span>')
        meta_en.append(f'<span>{esc(x["place_en"])}</span>')
    meta_ar.append(f'<span>{date_ar(x["date"])}</span>')
    meta_en.append(f'<span>{date_en(x["date"])}</span>')
    pro = ""
    if x["pro"]:
        pro = (f'<p class="series">من سلسلة «Proletarian» — العدد {ar_digits(x["pro"])}'
               f'<span lang="en" dir="ltr">From the “Proletarian” series, no. {x["pro"]}</span></p>')
    credit = ""
    if x["credit"]:
        credit = f'<p class="series">{esc(x["credit"][0])}<span lang="en" dir="ltr">{esc(x["credit"][1])}</span></p>'
    notes = ""
    if x["notes_en"]:
        lis = "".join(f"<li>{esc(n)}</li>" for n in x["notes_en"])
        notes = f'<aside class="notes" lang="en" dir="ltr"><h3>Translator’s notes</h3><ul>{lis}</ul></aside>'
    voice = ""
    if x["voice"]:
        voice = '<span class="voice">بصوت صاحب الوجه<i lang="en" dir="ltr">in the sitter’s voice</i></span>'

    def nav(item, cls, label_ar, label_en):
        if not item:
            return f'<span class="pn {cls} off"></span>'
        return (f'<a class="pn {cls}" href="{rel}face/{item["id"]}/">'
                f'<img src="{rel}img/{item["id"]}-t.jpg" alt="" width="64" height="80" loading="lazy">'
                f'<span><small>{label_ar} <i lang="en" dir="ltr">{label_en}</i></small>'
                f'<b>{esc(item["ar_label"])}</b><i lang="en" dir="ltr">{esc(item["en_label"])}</i></span></a>')

    body = f"""
<article class="face wrap" data-prev="{prev['id'] if prev else ''}" data-next="{nxt['id'] if nxt else ''}">
  <p class="crumb"><a href="{rel}#faces">← الوجوه <i lang="en" dir="ltr">All faces</i></a></p>
  <div class="face-grid">
    <figure class="photo">
      <img src="{rel}img/{x['id']}.jpg" width="{x['w']}" height="{x['h']}" alt="{esc(x['ar_label'])} — {esc(x['en_label'])}" fetchpriority="high">
    </figure>
    <div class="reading" data-lang="both" id="reading">
      <header class="face-head">
        <p class="num"><b>{ar_digits(int(x['id']))}</b><i lang="en" dir="ltr">{x['id']} / {len(faces)}</i></p>
        <h1><span class="h-ar">{esc(x['ar_label'])}</span><span class="h-en" lang="en" dir="ltr">{esc(x['en_label'])}</span></h1>
        <div class="meta"><p class="m-ar">{' · '.join(meta_ar)}</p><p class="m-en" lang="en" dir="ltr">{' · '.join(meta_en)}</p></div>
        {pro}{credit}
        <div class="langbar" role="group" aria-label="اللغة · Language">
          <button data-l="ar">عربي</button><button data-l="both" class="is-on">معًا · Both</button><button data-l="en" lang="en" dir="ltr">English</button>
        </div>
      </header>
      <section class="txt ar" lang="ar" dir="rtl">
        {voice}
        {render_text(x['text_ar'])}
      </section>
      <section class="txt en" lang="en" dir="ltr">
        {render_text(x['text_en'])}
        {notes}
      </section>
    </div>
  </div>
  <nav class="pager" aria-label="التنقل · Navigation">
    {nav(prev, 'prev', 'السابق', 'Previous')}
    {nav(nxt, 'next', 'التالي', 'Next')}
  </nav>
</article>
"""
    first = re.sub(r"\s+", " ", x["text_ar"]).strip()[:150]
    return layout(
        title=f"{x['ar_label']} — {x['en_label']} · الوجوه: لغةٌ مات قارئوها",
        desc=f"{first}… · {x['en_label']}",
        rel=rel, body=body, og=f"img/{x['id']}.jpg", body_class="facepage",
        scripts=f'<script src="{rel}js/main.js" defer></script>',
    )


def page_about(faces):
    rel = "../"
    n = len(faces)
    body = f"""
<article class="about wrap">
  <h1><span class="h-ar">عن المشروع</span><span class="h-en" lang="en" dir="ltr">About the project</span></h1>
  <div class="about-cols">
    <section class="txt ar" lang="ar" dir="rtl">
      <p>هذا المشروع جزءٌ من القصّ الاجتماعي، أي من روايةِ المجتمع بوجوه أهله. ومكةُ مَصهَرةٌ لكثيرٍ من الأعراق والجنسيّات والثقافات: يفِد إليها الناس حجّاجًا ومعتمرين، ويقيم فيها كثيرون عمّالًا وباعةً وصنّاعًا، ويلتقي في أسواقها وطرقاتها بشتونٌ وبنغال وسودانيّون وطوارق وروهنجيا وتركستانيّون ومصريّون ويمنيّون وسعوديّون.</p>
      <p>وفي العالم الحديث، وتحت عقودٍ من التمايز الاقتصادي بين الأقطار، يكون الاقتصادُ والبحثُ عن اللقمة الطيّبة محرّكَ الهجرة. هجرةٌ تأكل العمر دون حقوقٍ تُذكر، واغترابٌ لا يزيده انقضاءُ العمر إلا حدّة. وفي كلّ وجهٍ من هذه الوجوه صفحةٌ من ذلك القصّ.</p>
      <p>ظهرت هذه الوجوه أولَ مرّةٍ في أغسطس ٢٠١٦ على إنستغرام ضمن سلسلةٍ باسم «Proletarian»، يرافق كلَّ وجهٍ نصّ، ثم اتّسعت لتشمل وجوهًا لقيَها الكاتب في الأسواق والمشاعر والجبال وحول الحرمين، إلى أغسطس ٢٠١٨.</p>
      <p>يجمع هذا الموقع {ar_digits(n)} وجهًا بترتيبها الزمني. بعض النصوص بصوت صاحب الوجه، وبعضها عنه، وبعضها تأمّلٌ طويلٌ يبدأ من وجهٍ ويمضي إلى الأدب والتاريخ. الأصل العربي كما نُشر، مع تنظيمٍ طباعيّ فقط، وإلى جانبه ترجمةٌ إنجليزية ومعها ملاحظات المترجم حيث يلزم.</p>
      <p>الأصول المذكورة (بلدٌ أو قومٌ أو إقليم) مأخوذةٌ من النص نفسه أو من وسومه أو من توضيحات الكاتب، ولا تُنسب إلى أحدٍ ما لم يقله النصّ.</p>
    </section>
    <section class="txt en" lang="en" dir="ltr">
      <p>This project is part of social storytelling: the telling of a society through the faces of its people. Makkah is a crucible of many races, nationalities, and cultures. People come to it as pilgrims, for Hajj and umrah, and many settle there as laborers, vendors, and craftsmen. In its markets and streets Pashtuns, Bengalis, Sudanese, Tuareg, Rohingya, Turkestanis, Egyptians, Yemenis, and Saudis meet.</p>
      <p>In the modern world, after decades of economic inequality between nations, economics and the search for an honest morsel are what drive migration. It is a migration that consumes a lifetime with hardly any rights to speak of, and an estrangement that the passing of years only sharpens. Each of these faces is a page of that telling.</p>
      <p>These faces first appeared in August 2016 on Instagram, in a series called “Proletarian,” each accompanied by a text. The series then widened to include faces the author met in markets, pilgrim camps, on mountain paths, and around the two Holy Mosques, until August 2018.</p>
      <p>This site gathers {n} faces in chronological order. Some of the texts are in the voice of the person pictured, some are about them, and some are long reflections that begin with a face and travel on into literature and history. The Arabic is as published, with typographic tidying only; beside it stands an English translation, with translator’s notes where they are needed.</p>
      <p>The origins named here (a country, a people, a region) are taken from the text itself, from its hashtags, or from the author’s own clarifications, and are not attributed to anyone beyond what the text says.</p>
    </section>
  </div>
</article>
"""
    return layout(
        title="عن المشروع — About · الوجوه: لغةٌ مات قارئوها",
        desc="عن مشروع «الوجوه: لغةٌ مات قارئوها»: صور ونصوص عن ناسٍ من بلادٍ شتّى في مكة · About “Faces: An Unread Language.”",
        rel=rel, body=body, body_class="aboutpage",
    )


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#a9441f"/><path d="M20 22a12 12 0 1 1 12 20c-6 0-9-3-9-7 0-3 2-5 5-5" fill="none" stroke="#f2eadc" stroke-width="5" stroke-linecap="round"/><path d="M28 44c-4 4-3 9 3 9" fill="none" stroke="#f2eadc" stroke-width="5" stroke-linecap="round"/></svg>"""


def main():
    faces = load_data()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    for sub in ("css", "js", "fonts"):
        shutil.copytree(SITE / sub, DIST / sub)
    (DIST / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    build_images(faces)
    (DIST / "index.html").write_text(page_index(faces), encoding="utf-8")
    (DIST / "about").mkdir()
    (DIST / "about" / "index.html").write_text(page_about(faces), encoding="utf-8")
    for i, x in enumerate(faces):
        d = DIST / "face" / x["id"]
        d.mkdir(parents=True)
        prev = faces[i - 1] if i > 0 else None
        nxt = faces[i + 1] if i + 1 < len(faces) else None
        (d / "index.html").write_text(page_face(x, prev, nxt, faces), encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    size = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print(f"تم البناء ✓  {len(faces)} وجهًا · {2 + len(faces)} صفحة · {size/1e6:.1f}MB في dist/")


if __name__ == "__main__":
    main()
