import os
import re

# المسار الذي يحتوي على ملفات الفيديو
BASE_DIR = "tuaa/video"
INDEX_FILE = os.path.join(BASE_DIR, "index.html")

# الكلمات التي يتم تجاهلها عند البحث عن تشابه
STOP_WORDS = {
    "مع", "في", "على", "من", "إلى", "الى", "عن",
    "ال", "و", "او", "أو", "html"
}

def extract_words(filename):
    """استخراج الكلمات الهامة من اسم الملف"""
    name = filename.replace(".html", "")
    # تقسيم الاسم بناءً على الفواصل والشرطات
    parts = re.split(r"[-_ ]+", name)
    return set(
        p for p in parts
        if p not in STOP_WORDS and len(p) > 2
    )

# التأكد من وجود المجلد
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# جلب جميع ملفات html باستثناء الفهرس
files = [
    f for f in os.listdir(BASE_DIR)
    if f.endswith(".html") and f != "index.html"
]

# تحليل كلمات كل ملف لمرة واحدة لزيادة السرعة
file_words = {f: extract_words(f) for f in files}

# 1. إنشاء ملف الفهرس الرئيسي (index.html)
with open(INDEX_FILE, "w", encoding="utf-8") as idx:
    idx.write("""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>جميع الفيديوهات - أرشيف 2026</title>
<meta name="robots" content="index,follow">
<style>
body{font-family:sans-serif;background:#000;color:#ccc;padding:20px;line-height:1.6}
.container{max-width:1000px;margin:auto}
a{color:#f90;text-decoration:none;transition:0.3s}
a:hover{color:#fff}
li{margin-bottom:12px;list-style:none;border-bottom:1px solid #111;padding-bottom:8px}
h1{color:#ff0055;border-bottom:2px solid #ff0055;display:inline-block}
</style>
</head>
<body>
<div class="container">
<h1>أرشيف الفيديوهات الحصرية</h1>
<ul>
""")

    for f in files:
        title = f.replace("-", " ").replace(".html", "")
        idx.write(f'<li><a href="{f}">🎬 {title}</a></li>\n')

    idx.write("""
</ul>
</div>
</body>
</html>
""")

# 2. إضافة روابط "مواضيع مشابهة" داخل كل صفحة فيديو
for f in files:
    path = os.path.join(BASE_DIR, f)

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()

        # إذا كانت الصفحة تحتوي بالفعل على قسم المشابه، نتخطاها لتجنب التكرار
        if "related" in content or "سكس مشابه" in content:
            continue

        # البحث عن أكثر الملفات تشابهاً في الكلمات
        similarities = []
        for other in files:
            if other == f:
                continue
            common = file_words[f] & file_words[other]
            if len(common) >= 1:
                similarities.append((other, len(common)))

        # ترتيب النتائج حسب الأكثر تشابهاً وأخذ أول 3
        similarities.sort(key=lambda x: x[1], reverse=True)
        related = [x[0] for x in similarities[:3]]

        if not related:
            continue

        # بناء صندوق الروابط المشابهة
        box = """
<div class="related-box" style="margin-top:40px; padding:20px; background:#050505; border:1px solid #111; border-radius:10px;">
<h3 style="color:#ff0055; margin-top:0;">🔥 مقاطع سكس مشابهة قد تعجبك:</h3>
<ul style="list-style:none; padding:0;">
"""
        for r in related:
            title = r.replace("-", " ").replace(".html", "")
            box += f'<li style="margin-bottom:10px;"><a href="{r}" style="color:#f90; text-decoration:none;">⭐ {title}</a></li>\n'

        box += "</ul>\n</div>"

        # حقن الصندوق قبل وسم الإغلاق </body>
        if "</body>" in content:
            content = content.replace("</body>", box + "\n</body>")
        else:
            content += box

        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
            
    except Exception as e:
        print(f"Error processing {f}: {e}")

print(f"✔ تم بنجاح إنشاء index.html وتحديث {len(files)} ملف.")
