# -*- coding: utf-8 -*-
"""
استخراج سلسلة «وجوه العيش» من أرشيف إنستغرام:
  - ينتقي 47 منشورًا (بورتريه + نص) بترتيبها الزمني
  - ينظّف النص العربي (وسوم، ترقيم Proletarian، علامات اقتباس شاردة، مسافة الواو)
  - ينسخ الصور إلى images/NN.jpg
  - يكتب data/faces.json (بيانات وصفية + نص عربي) — الترجمة الإنجليزية في data/en/
تشغيل:  python3 tools/extract.py
"""
import html as H
import json
import os
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
IG = Path("/Users/majed/Documents/Documents - Majed Adnan Alahdal Alahdal-Salla-Device/"
          "Claude code/My Personal Brand/Social media/instagram-data")
EXPORT = Path("/Users/majed/Downloads/instagram-majed3dnan-2026-07-10-097Vv9i7/"
              "your_instagram_activity/media/archived_posts.html")
EXPORT_MEDIA = Path("/Users/majed/Downloads/instagram-majed3dnan-2026-07-10-vKNqU4wd")

# ———— الاختيار ————
# كل عنصر: (المصدر, المعرّف, الرقم في سلسلة Proletarian أو None,
#           العنوان عربي, العنوان إنجليزي, الأصل عربي, الأصل إنجليزي,
#           المكان عربي, المكان إنجليزي, بصوت صاحبه؟)
# المصدر: "p" منشور عام (الكود)، "a" مؤرشف (رقم الكتلة 0..7)
N = None
SEL = [
    ("a", 7, 1, "من بلاد البردّوني", "From al-Baradouni's Country", "اليمن", "Yemen", N, N, True),
    ("a", 6, 3, "من البشتون", "A Pashtun", "البشتون", "Pashtun", N, N, True),
    ("a", 5, 4, "بنغاليّ", "A Bengali", "البنغال", "Bengal", N, N, True),
    ("p", "BIsST8hh25N", 5, "من بلاد الفيتوري", "From al-Fitouri's Land", "السودان", "Sudan", N, N, True),
    ("p", "BIwhWVlhAI_", 6, "رشيديّ من بدو السودان", "A Rashaida Bedouin of Sudan", "الرشايدة (السودان)", "Rashaida (Sudan)", N, N, False),
    ("p", "BIyKo6ihSe0", 7, "لغةٌ مات قارؤوها", "A Language Whose Readers Died", N, N, N, N, False),
    ("p", "BIzssZyBjYu", 8, "جزّار من غرب أفريقيا", "A Butcher from West Africa", "غرب أفريقيا", "West Africa", N, N, True),
    ("p", "BI0tp3IBDLW", 9, "مصريٌّ أنا", "I Am Egyptian", "مصر", "Egypt", N, N, True),
    ("p", "BI5IDH9B8Fi", 10, "اسمي رمضان", "My Name Is Ramadan", "بنغلاديش", "Bangladesh", N, N, True),
    ("p", "BJEVq2Chfkf", 11, "أول من وجّه لوجهي كاميرا", "The First to Point a Camera at My Face", N, N, N, N, True),
    ("p", "BJGfDm4BW1k", 12, "على قمّة هرم الحياة", "At the Peak of Life's Pyramid", N, N, N, N, True),
    ("p", "BJJ2wxQhLFK", 13, "يا حابسَ الظلّ", "O Captor of Shadows", N, N, N, N, True),
    ("p", "BJQbfi1BeLM", 14, "أنا خبّاز", "I Am a Baker", N, N, N, N, True),
    ("p", "BJW3djaBNgn", 15, "روحي لم تصل بعد", "My Soul Has Not Arrived Yet", N, N, N, N, True),
    ("p", "BJm8Gcwhpz8", 16, "تركستانيّ", "A Turkestani", "تركستان", "Turkestan", N, N, True),
    ("p", "BJr0nZCBUHl", N, "زقاق السمك", "The Fish Alley", N, N, "سوق النكّاسة — مكة المكرمة", "Nakkasah Market — Makkah", False),
    ("p", "BJ2MFwBBvgb", N, "حَمَام سلام", "Doves of Peace", "بورما (الروهنجيا)", "Burma (Rohingya)", "سوق النكّاسة — مكة المكرمة", "Nakkasah Market — Makkah", False),
    ("p", "BJ3Lgr0B-JN", N, "الحزن والجمال توأمان", "Sorrow and Beauty, Twins", N, N, "سوق النكّاسة — مكة المكرمة", "Nakkasah Market — Makkah", False),
    ("p", "BJ5c8XAhXUW", N, "في السوق القديم", "In the Old Market", N, N, "سوق النكّاسة — مكة المكرمة", "Nakkasah Market — Makkah", False),
    ("p", "BJ57foChm6q", N, "شيخ برماويّ يبيع السمك", "A Burmese Elder Selling Fish", "بورما", "Burma", "سوق النكّاسة — مكة المكرمة", "Nakkasah Market — Makkah", False),
    ("p", "BJ8JnTyBGix", N, "ابتسامة خالدة", "A Timeless Smile", N, N, "سوق النكّاسة — مكة المكرمة", "Nakkasah Market — Makkah", False),
    ("p", "BKDM2uXhRPQ", N, "نعود إلى ذلك الملف", "Returning to That File", N, N, "سوق النكّاسة — مكة المكرمة", "Nakkasah Market — Makkah", False),
    ("p", "BKGP2VYBDb_", N, "بائع الفاكهة الاستوائية", "The Tropical-Fruit Seller", N, N, "سوق النكّاسة — مكة المكرمة", "Nakkasah Market — Makkah", False),
    ("p", "BKYtVyDBQ54", N, "صاحب أكثِّ شاربٍ في المخيّم", "The Man with the Thickest Mustache in Camp", "السعودية", "Saudi Arabia", "مِنى", "Mina", False),
    ("p", "BKYo-nlBWB9", N, "وجوه من الحجّ", "Faces of Hajj", N, N, N, N, False),
    ("p", "BKbppU9Boof", N, "الحاجّ الأنيق", "The Elegant Pilgrim", "السعودية", "Saudi Arabia", N, N, False),
    ("p", "BKfpTXqhPq4", N, "حين يرفع الوجهُ رايته البيضاء", "When the Face Raises Its White Flag", "السعودية", "Saudi Arabia", N, N, False),
    ("p", "BKjj9fShz2D", N, "شيخ أفغانيّ", "An Afghan Elder", "أفغانستان", "Afghanistan", "المطاف — مكة المكرمة", "The Mataf — Makkah", False),
    ("p", "BLKfanZF81q", N, "الحاجّ إبراهيم، من الطوارق", "Hajj Ibrahim, a Tuareg", "الطوارق", "Tuareg", N, N, False),
    ("p", "BOPGWQKFZCs", N, "بائع الهدايا", "The Gift Seller", "باكستان", "Pakistan", "جبل النور (حراء) — مكة المكرمة", "Jabal al-Nour (Hira) — Makkah", False),
    ("p", "BOdI-92FC_P", N, "أبٌ وابنته", "A Father and His Daughter", "باكستان", "Pakistan", "جبل ثور — مكة المكرمة", "Jabal Thawr — Makkah", False),
    ("p", "BPdfzU0jkPV", N, "حازمٌ رغم البطاطا", "Resolute Despite the Potato Chips", N, N, N, N, False),
    ("p", "BPn14wJlvP1", N, "وجهٌ من البنجاب", "A Face from Punjab", "البنجاب", "Punjab", "في الطريق إلى رُهاط", "On the road to Rahat", False),
    ("p", "BQBq6wZleWZ", N, "أحمد خليل", "Ahmad Khalil", "البنجاب (باكستان)", "Punjab (Pakistan)", "جدّة البلد", "Jeddah, al-Balad", False),
    ("a", 4, N, "الأفق الذي لم يعد بعيدًا", "A Horizon No Longer Far", "الروهنجيا", "Rohingya", "سوق النكّاسة — مكة المكرمة", "Nakkasah Market — Makkah", True),
    ("a", 3, N, "في انتظارٍ باسمٍ", "A Smiling Wait", "بنغلاديش", "Bangladesh", "سوق النكّاسة — مكة المكرمة", "Nakkasah Market — Makkah", False),
    ("a", 2, N, "وجوه الشيوخ", "The Elders' Faces", "البشتون", "Pashtun", "المدينة المنورة", "Madinah", False),
    ("a", 1, N, "صديق الشيخ البشتوني", "The Pashtun Elder's Friend", N, N, "المسجد النبوي — المدينة المنورة", "The Prophet's Mosque — Madinah", False),
    ("a", 0, N, "فيك الكثير الكثير منه", "So Much of Him Is in You", N, N, "المدينة المنورة", "Madinah", False),
    ("p", "BU2sR4vBxzz", N, "معتمر من باكستان", "A Pilgrim from Pakistan", "باكستان", "Pakistan", "شارع إبراهيم الخليل — مكة المكرمة", "Ibrahim al-Khalil Street — Makkah", False),
    ("p", "BVIYzRehopR", N, "الحاجّ شكري الشيخ", "Hajj Shukri al-Sheikh", "مصر (البحيرة)", "Egypt (Beheira)", "أجياد (بير بليلة) — مكة المكرمة", "Ajyad (Bir Bulayla) — Makkah", False),
    ("p", "BVIaQ3DBhMc", N, "الحاجّ نظام الدين جنيد", "Hajj Nizamuddin Junaid", "الهند (بومباي)", "India (Bombay)", "أجياد (بير بليلة) — مكة المكرمة", "Ajyad (Bir Bulayla) — Makkah", False),
    ("p", "BfBxwgshOXZ", N, "عرفتُه يمنيًّا", "I Knew Him for a Yemeni", "اليمن", "Yemen", N, N, False),
    ("p", "BhzGmegAyH6", N, "واشتعل الرأس شمسًا", "The Head Ablaze with Sun", N, N, "مكة المكرمة — رمضان", "Makkah — Ramadan", False),
    ("p", "BmEw5Y-Bods", N, "يا للأجداد", "O Ancestors", "الرشايدة (السودان)", "Rashaida (Sudan)", N, N, True),
    ("p", "BmGYi14BUHD", N, "أوسطهم طريقة", "The Middle One", "باكستان", "Pakistan", "مكة المكرمة", "Makkah", True),
]

# نصوص تُكتب يدويًا لأن وسومها داخل الجملة أو لأن لها شكلًا خاصًا
OVERRIDE = {
    "BVIYzRehopR": "الحاج شكري الشيخ من محافظة البحيرة، سألته عن سر «الصَّفنة» فقال: بالي سرحان مع عيالي في مصر.",
    "BVIaQ3DBhMc": "الحاج نظام الدين جنيد من بومباي، الهند.",
    "BU2sR4vBxzz": "أحد المعتمرين من پاكستان، في شارع إبراهيم الخليل، بمكة المكرمة.",
    "BPdfzU0jkPV": "حازمٌ رغم البطاطا. أحبّ هؤلاء القوم.",
    "BhzGmegAyH6": "واشتعل الرأس شمسًا..",
    "BfBxwgshOXZ": ("من ذلك الوجه؟ يبدو أنّه (جَنَدِي)\nلا.. بل (يَريْمِي).. سأدعو جدَّ مبتَعدِ!\n"
                    "لعلّه (دُبَعِيٌّ) أصل والدهِ\nمِن (يافعٍ).. أمّه من سورةِ المَسَدِ\n"
                    "عرفتُه يمنيًّا في تلفُّتِه.. خوفٌ\nوعيناه.. تاريخٌ من الرَّمَدِ\n"
                    "— البردّونيّ البصير، في «غريبان وكانا هما البلد»"),
    "BQBq6wZleWZ": ("أحمد خليل من إقليم البنجاب، باكستان. يعمل في محل لتجارة الأقمشة في البلد بجدّة. سألته عن بلاده، "
                    "فكانت هذه الزّفرة. سيبردُ كلُّ جرحٍ يا أحمد، فاطمئنَّ. كلّنا يا أحمد طيرٌ يحنُّ إلى عُشّه، "
                    "و كلّنا ريشةٌ تحملها أكفُّ القدر إلى حيثُ ارتضتْ العنايةُ الإلهيّة. أسلّيك يا أحمد بترنيمةٍ "
                    "لأبي بكر سالم، يحفظها اليمانُون الذين يشاركونك المنافي، و يقتسمون معك رغيف الغُربة عن ظهر قلب. "
                    "يقول فيها:\n«كما الرّيشة\nيا طير يا ضاوي.. إلى عشّك\nقل لي: متى بضوي على عشّي؟\n"
                    "ملّيت - شفنا- هذي العِيشة\nقلبي من الفُرقا.. كما الرِّيشة!»"),
    "BmEw5Y-Bods": ("يا للأجداد، لم يكن بينهم عرّافٌ صادق.. هربنا إلى الخصب قبل قرون حين كان الخصب فوق الأرض، "
                    "في مراعٍ نرعى بها شويهات ونوقًا. لم يخبرنا العرّاف عن الخصب تحت الأرض. عدنا، لم تتغيّر الأرض، "
                    "الجدب ذاته، عدنا بأغنامنا التي سمّنّاها في المراعي البعيدة، ويبدو أننا تأخرنا كثيرًا.. "
                    "لم تخبرني، هل تريد ذبايح؟\n— رشيدي"),
    "BmGYi14BUHD": ("السودانيّون ليسوا أحسن منّا في شيء.. كلنا مغترب، كلنا يعمل في بيع الماشية. خذ لنا صورة وانشرها "
                    "حيث شئت، حتى ولو في «أمريكا!» لكن لا تنسَ إرسالها لوزير فهو وحده من يمتلك واتسابًا في جواله.\n"
                    "— أوسطهم طريقة."),
}


# صور فيها أشرطة بيضاء مدمجة في الملف نفسه (تُقصّ عند النسخ)
TRIM_WHITE = set()


def trim_white(im):
    diff = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).convert("L")
    bbox = diff.point(lambda p: 255 if p > 14 else 0).getbbox()
    return im.crop(bbox) if bbox else im


def clean(raw: str) -> str:
    lines = [l.rstrip() for l in raw.strip().split("\n")]
    # حروف/رموز شاردة في أول سطر (حيلة تنسيق في إنستغرام)
    while lines and re.fullmatch(r"[\"“'‘ء ا.،/\-–]*", lines[0].strip()):
        lines.pop(0)
    if lines:
        first = lines[0].strip()
        # علامة اقتباس مفتوحة حقيقية (مغلقة في السطر نفسه) تبقى؛ والشاردة تُحذف
        if first[:1] == "“" and "”" in first[:80]:
            lines[0] = first
        else:
            lines[0] = re.sub(r"^[\"“'‘]+\s*", "", first)
        # ترقيم «(٢/١٣)» من سلسلة رحلة مرتبطة بالصور
        lines[0] = re.sub(r"^\([٠-٩0-9]+/[٠-٩0-9]+\)\s*", "", lines[0])
    if lines and not lines[0]:
        lines.pop(0)
    out = []
    for l in lines:
        s = l.strip()
        if re.fullmatch(r"Proletarian\s*\d*", s, re.I):
            continue
        s2 = re.sub(r"#[\w_\-']+", "", s).strip()
        if not s2 and s:  # سطر وسوم فقط
            continue
        if re.fullmatch(r"[\"“”'‘’]+", s2):  # سطر علامات اقتباس شاردة فقط
            continue
        s2 = re.sub(r"\s+[\"'’”]\s*$", "", s2)  # علامة اقتباس يتيمة في آخر السطر
        out.append(s2)
    text = "\n".join(out).strip()
    text = re.sub(r"[\"“'‘]\s*$", "", text).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def norm_waw(text: str) -> str:
    """مسافة الواو: «و كذا» → «وكذا» (واو العطف المنفصلة) — تنسيق فقط لا تغيير في الألفاظ."""
    return re.sub(r"(?<![؀-ۿ])و[ \t]+(?=[؀-ۿ«\"(])", "و", text)


def load_archived():
    t = EXPORT.read_text(encoding="utf-8", errors="ignore")
    blocks = re.split(r'<div class="pam _3-95 _2ph- _a6-g uiBoxWhite noborder">', t)[1:]
    res = []
    for b in blocks:
        cap = re.search(r"<h2[^>]*>(.*?)</h2>", b, re.S)
        cap = H.unescape(re.sub(r"<[^>]+>", "\n", cap.group(1))).strip() if cap else ""
        img = re.findall(r'href="(media/[^"]+\.jpg)"', b)[0]
        d = re.search(r'class="_3-94 _a6-o">([^<]+)</div>', b).group(1).strip()
        dt = datetime.strptime(d, "%b %d, %Y %I:%M %p")
        res.append({"caption": cap, "img": EXPORT_MEDIA / img, "dt": dt})
    return res


def main():
    posts = {p["code"]: p for p in json.load(open(IG / "posts.json"))}
    arch = load_archived()
    items = []
    for src, key, pro, ar_l, en_l, o_ar, o_en, pl_ar, pl_en, voice in SEL:
        if src == "p":
            p = posts[key]
            cap, date = p["caption"] or "", p["date"]
            ts = p["ts"]
            img = IG / "images" / f"{key}_0.jpg"
            code = key
        else:
            a = arch[key]
            cap, date = a["caption"], a["dt"].strftime("%Y-%m-%d")
            ts = a["dt"].timestamp()
            img = a["img"]
            code = f"archived-{key}"
        text = norm_waw(OVERRIDE.get(key if src == "p" else None) or clean(cap))
        text = text.replace("في انتظار باسم.", "في انتظارٍ باسمٍ.")
        items.append(dict(src=src, code=code, key=key, ts=ts, date=date, pro=pro, ar_label=ar_l, en_label=en_l,
                          origin_ar=o_ar, origin_en=o_en, place_ar=pl_ar, place_en=pl_en, voice=voice,
                          text_ar=text, _img=str(img)))
    # الترتيب الزمني، وعند التعادل يُحسم برقم Proletarian
    items.sort(key=lambda x: (x["date"], x["pro"] or 99, x["ts"]))
    (ROOT / "images").mkdir(exist_ok=True)
    for old in (ROOT / "images").glob("*.jpg"):
        old.unlink()
    for i, it in enumerate(items, 1):
        it["id"] = f"{i:02d}"
        im = Image.open(it.pop("_img")).convert("RGB")
        if it.pop("key") in TRIM_WHITE:
            im = trim_white(im)
        it["w"], it["h"] = im.size
        im.save(ROOT / "images" / f"{it['id']}.jpg", quality=88, optimize=True, progressive=True)
    (ROOT / "data").mkdir(exist_ok=True)
    json.dump(items, open(ROOT / "data" / "faces.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tot = sum(len(it["text_ar"]) for it in items)
    print(f"{len(items)} وجهًا | مجموع الحروف العربية: {tot:,} | صور: {len(list((ROOT/'images').glob('*.jpg')))}")


if __name__ == "__main__":
    main()
