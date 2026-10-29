# -*- coding: utf-8 -*-
import os

IMG_DIR = r"C:\Du_an\T_Langua_Test\docs\img"
SVG_PATH = os.path.join(IMG_DIR, "hinh_3_1_kien_truc_phan_tang_cac_goi_lop.svg")
HTML_PATH = os.path.join(IMG_DIR, "hinh_3_1_source.html")

with open(HTML_PATH, "r", encoding="utf-8") as f:
    html_raw = f.read()

# Wrap clean HTML inside SVG foreignObject for standard high-fidelity vector rendering
svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1640" height="1380" viewBox="0 0 1640 1380">
  <foreignObject width="100%" height="100%">
    <div xmlns="http://www.w3.org/1999/xhtml">
      {html_raw}
    </div>
  </foreignObject>
</svg>
"""

with open(SVG_PATH, "w", encoding="utf-8") as f:
    f.write(svg_content)

print(f"SVG vector file created: {SVG_PATH}")

