name: Update Sitemap and Smart Linking

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update-all:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Create linker.py dynamically
        # هذا الإجراء يقوم بكتابة محتوى السكربت في ملف قبل تشغيله لضمان عدم حدوث خطأ "الملف غير موجود"
        run: |
          cat << 'EOF' > linker.py
          import os
          import re

          BASE_DIR = "tuaa/video"
          INDEX_FILE = os.path.join(BASE_DIR, "index.html")

          STOP_WORDS = {"مع", "في", "على", "من", "إلى", "الى", "عن", "ال", "و", "او", "أو", "html"}

          def extract_words(filename):
              name = filename.replace(".html", "")
              parts = re.split(r"[-_ ]+", name)
              return set(p for p in parts if p not in STOP_WORDS and len(p) > 2)

          if not os.path.exists(BASE_DIR):
              os.makedirs(BASE_DIR)

          files = [f for f in os.listdir(BASE_DIR) if f.endswith(".html") and f != "index.html"]
          file_words = {f: extract_words(f) for f in files}

          with open(INDEX_FILE, "w", encoding="utf-8") as idx:
              idx.write('<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>أرشيف الفيديوهات</title><style>body{font-family:sans-serif;background:#000;color:#ccc;padding:20px}a{color:#f90;text-decoration:none}li{margin-bottom:8px}</style></head><body><h1>فيديوهات سكس حصرية</h1><ul>')
              for f in files:
                  title = f.replace("-", " ").replace(".html", "")
                  idx.write(f'<li><a href="{f}">🎬 {title}</a></li>\n')
              idx.write('</ul></body></html>')

          for f in files:
              path = os.path.join(BASE_DIR, f)
              try:
                  with open(path, "r", encoding="utf-8", errors="ignore") as file:
                      content = file.read()
                  if "related-box" in content: continue
                  similarities = []
                  for other in files:
                      if other == f: continue
                      common = file_words[f] & file_words[other]
                      if len(common) >= 1: similarities.append((other, len(common)))
                  similarities.sort(key=lambda x: x[1], reverse=True)
                  related = [x[0] for x in similarities[:3]]
                  if not related: continue
                  box = '<div class="related-box" style="margin-top:20px;border-top:1px solid #333"><h3>سكس مشابه</h3><ul>'
                  for r in related:
                      title = r.replace("-", " ").replace(".html", "")
                      box += f'<li><a href="{r}">{title}</a></li>\n'
                  box += '</ul></div>'
                  content = content.replace("</body>", box + "</body>") if "</body>" in content else content + box
                  with open(path, "w", encoding="utf-8") as file:
                      file.write(content)
              except Exception as e:
                  print(f"Error: {e}")
          print("Done!")
          EOF

      - name: Run Smart Linker
        run: python linker.py

      - name: Update sitemap.xml
        run: |
          SITEMAP="sitemap.xml"
          BASE_URL="https://pasuk-old.dicta.org.il"
          TMP_SITEMAP=$(mktemp)
          echo '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' > "$TMP_SITEMAP"
          
          if [ -d "tuaa/video" ]; then
            find tuaa/video -type f -name "*.html" | while read file; do
              echo "<url><loc>${BASE_URL}/${file}</loc><lastmod>$(date -I)</lastmod><priority>0.8</priority></url>" >> "$TMP_SITEMAP"
            done
          fi
          
          echo '</urlset>' >> "$TMP_SITEMAP"
          mv "$TMP_SITEMAP" "$SITEMAP"

      - name: Commit and Push changes
        run: |
          git config user.name "github-actions"
          git config user.email "github-actions@github.com"
          git add sitemap.xml
          if [ -d "tuaa/video" ]; then
            git add tuaa/video/*.html
          fi
          
          if git diff --quiet && git diff --staged --quiet; then
            echo "No changes to commit"
            exit 0
          fi
          
          git commit -m "Auto Smart Linking and Sitemap Update [skip ci]"
          git pull --rebase origin main
          git push origin main
