# -*- coding: utf-8 -*-
"""
Test renderer for ERD diagrams matching the exact visual style of [DALN]2210.pdf.
"""
import os
import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT_DIR = r"C:\Du_an\T_Langua_Test\docs\img\csdl"
os.makedirs(OUT_DIR, exist_ok=True)

def render_svg_to_png(svg_content, out_png_path, width=1200, height=800):
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #ffffff;
    display: flex;
    justify-content: center;
    align-items: center;
    width: {width}px;
    height: {height}px;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  }}
</style>
</head>
<body>
{svg_content}
</body>
</html>
"""
    tmp_html = out_png_path.replace(".png", "_temp.html")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html)
    
    cmd = [
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        f"--window-size={width},{height}",
        f"--screenshot={out_png_path}",
        tmp_html
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if os.path.exists(tmp_html):
        os.remove(tmp_html)
    print(f"Rendered: {out_png_path}")

# Test drawing Group 1: Users, Auth Sessions, API Keys, Audit Logs
svg_nhom_1 = """
<svg width="1100" height="650" viewBox="0 0 1100 650" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="shadow" x="-5%" y="-5%" width="115%" height="115%">
      <feDropShadow dx="2" dy="3" stdDeviation="2" flood-color="#1e293b" flood-opacity="0.12"/>
    </filter>
  </defs>

  <!-- Entity: USERS -->
  <g class="entity" transform="translate(430, 40)">
    <rect x="0" y="0" width="240" height="90" rx="3" ry="3" fill="#ffffff" stroke="#1e293b" stroke-width="2" filter="url(#shadow)"/>
    <text x="120" y="52" text-anchor="middle" font-family="'Segoe UI', Roboto, sans-serif" font-weight="600" font-size="16" fill="#0f172a" letter-spacing="0.5">USERS</text>
  </g>

  <!-- Connectors from USERS (x=550, y=130) -->
  
  <!-- Path to AUTH_SESSIONS: down to y=230, left to x=180, down to y=380 -->
  <path d="M 500 130 L 500 230 L 180 230 L 180 380" fill="none" stroke="#1e293b" stroke-width="2"/>
  <!-- USERS One-End Ticks (at 500, 130 heading down) -->
  <line x1="492" y1="145" x2="508" y2="145" stroke="#1e293b" stroke-width="2"/>
  <line x1="492" y1="152" x2="508" y2="152" stroke="#1e293b" stroke-width="2"/>
  <!-- AUTH_SESSIONS Many-End (at 180, 380 entering top) -->
  <circle cx="180" cy="358" r="4.5" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
  <line x1="170" y1="380" x2="180" y2="366" stroke="#1e293b" stroke-width="2"/>
  <line x1="190" y1="380" x2="180" y2="366" stroke="#1e293b" stroke-width="2"/>
  <line x1="180" y1="380" x2="180" y2="366" stroke="#1e293b" stroke-width="2"/>
  <text x="240" y="222" font-family="'Segoe UI', Roboto, sans-serif" font-size="13" fill="#334155" text-anchor="middle">phiên đăng nhập 1-N</text>

  <!-- Path to AUDIT_LOGS: straight down from x=550, y=130 to y=380 -->
  <path d="M 550 130 L 550 380" fill="none" stroke="#1e293b" stroke-width="2"/>
  <!-- USERS One-End Ticks -->
  <line x1="542" y1="145" x2="558" y2="145" stroke="#1e293b" stroke-width="2"/>
  <line x1="542" y1="152" x2="558" y2="152" stroke="#1e293b" stroke-width="2"/>
  <!-- AUDIT_LOGS Many-End -->
  <circle cx="550" cy="358" r="4.5" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
  <line x1="540" y1="380" x2="550" y2="366" stroke="#1e293b" stroke-width="2"/>
  <line x1="560" y1="380" x2="550" y2="366" stroke="#1e293b" stroke-width="2"/>
  <line x1="550" y1="380" x2="550" y2="366" stroke="#1e293b" stroke-width="2"/>
  <text x="550" y="280" font-family="'Segoe UI', Roboto, sans-serif" font-size="13" fill="#334155" text-anchor="middle" background="#ffffff">ghi vết kiểm toán 1-N</text>

  <!-- Path to API_KEYS: down to y=230, right to x=920, down to y=380 -->
  <path d="M 600 130 L 600 230 L 920 230 L 920 380" fill="none" stroke="#1e293b" stroke-width="2"/>
  <!-- USERS One-End Ticks -->
  <line x1="592" y1="145" x2="608" y2="145" stroke="#1e293b" stroke-width="2"/>
  <line x1="592" y1="152" x2="608" y2="152" stroke="#1e293b" stroke-width="2"/>
  <!-- API_KEYS Many-End -->
  <circle cx="920" cy="358" r="4.5" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
  <line x1="910" y1="380" x2="920" y2="366" stroke="#1e293b" stroke-width="2"/>
  <line x1="930" y1="380" x2="920" y2="366" stroke="#1e293b" stroke-width="2"/>
  <line x1="920" y1="380" x2="920" y2="366" stroke="#1e293b" stroke-width="2"/>
  <text x="840" y="222" font-family="'Segoe UI', Roboto, sans-serif" font-size="13" fill="#334155" text-anchor="middle">sở hữu khóa API 1-N</text>

  <!-- Entity: AUTH_SESSIONS -->
  <g class="entity" transform="translate(60, 380)">
    <rect x="0" y="0" width="240" height="90" rx="3" ry="3" fill="#ffffff" stroke="#1e293b" stroke-width="2" filter="url(#shadow)"/>
    <text x="120" y="52" text-anchor="middle" font-family="'Segoe UI', Roboto, sans-serif" font-weight="600" font-size="16" fill="#0f172a" letter-spacing="0.5">AUTH_SESSIONS</text>
  </g>

  <!-- Entity: AUDIT_LOGS -->
  <g class="entity" transform="translate(430, 380)">
    <rect x="0" y="0" width="240" height="90" rx="3" ry="3" fill="#ffffff" stroke="#1e293b" stroke-width="2" filter="url(#shadow)"/>
    <text x="120" y="52" text-anchor="middle" font-family="'Segoe UI', Roboto, sans-serif" font-weight="600" font-size="16" fill="#0f172a" letter-spacing="0.5">AUDIT_LOGS</text>
  </g>

  <!-- Entity: API_KEYS -->
  <g class="entity" transform="translate(800, 380)">
    <rect x="0" y="0" width="240" height="90" rx="3" ry="3" fill="#ffffff" stroke="#1e293b" stroke-width="2" filter="url(#shadow)"/>
    <text x="120" y="52" text-anchor="middle" font-family="'Segoe UI', Roboto, sans-serif" font-weight="600" font-size="16" fill="#0f172a" letter-spacing="0.5">API_KEYS</text>
  </g>
</svg>
"""

out_file = os.path.join(OUT_DIR, "hinh_3_29_nhom_tai_khoan_nguoi_dung_phan_quyen.png")
render_svg_to_png(svg_nhom_1, out_file, width=1100, height=540)

