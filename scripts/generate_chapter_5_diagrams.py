# -*- coding: utf-8 -*-
"""
Diagram Generator for T-Lingua Chapter 5:
- Hình 5.1: Biểu đồ Gantt kế hoạch triển khai dự án T-Lingua (25/08/2026 - 30/10/2026)
- Hình 5.2: Sơ đồ quy trình phối hợp làm việc nhóm và CI/CD Git Workflow
"""

import os
import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT_DIR = r"C:\Du_an\T_Langua_Test\docs\img"
os.makedirs(OUT_DIR, exist_ok=True)

def render_html_to_png(html_content, out_png_path, width=1400, height=850):
    tmp_html = out_png_path.replace(".png", "_temp.html")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    
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

# ==============================================================================
# HÌNH 5.1: Biểu đồ Gantt kế hoạch triển khai dự án T-Lingua
# ==============================================================================
def generate_hinh_5_1():
    # Width 1400, Height 860
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 1400px;
    height: 860px;
  }
  .container {
    width: 1360px;
    height: 820px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    display: flex;
    flex-direction: column;
  }
  svg { width: 100%; height: 100%; }
</style>
</head>
<body>
<div class="container">
  <svg viewBox="0 0 1310 770">
    <defs>
      <!-- Gradients for Gantt bars -->
      <linearGradient id="gP1" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#60a5fa"/>
      </linearGradient>
      <linearGradient id="gP2" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#0284c7"/><stop offset="100%" stop-color="#38bdf8"/>
      </linearGradient>
      <linearGradient id="gP3" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#0d9488"/><stop offset="100%" stop-color="#2dd4bf"/>
      </linearGradient>
      <linearGradient id="gP4" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#7c3aed"/><stop offset="100%" stop-color="#a78bfa"/>
      </linearGradient>
      <linearGradient id="gP5" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#ea580c"/><stop offset="100%" stop-color="#fb923c"/>
      </linearGradient>
      <linearGradient id="gP6" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#4f46e5"/><stop offset="100%" stop-color="#818cf8"/>
      </linearGradient>
      <linearGradient id="gP7" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#e11d48"/><stop offset="100%" stop-color="#fb7185"/>
      </linearGradient>
      <linearGradient id="gP8" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#059669"/><stop offset="100%" stop-color="#34d399"/>
      </linearGradient>
      <filter id="shadow" x="-5%" y="-10%" width="110%" height="130%">
        <feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity="0.15"/>
      </filter>
    </defs>

    <!-- Header info banner -->
    <rect x="0" y="0" width="1310" height="50" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
    <text x="20" y="30" font-size="14" font-weight="700" fill="#1e293b">DỰ ÁN T-LINGUA: KẾ HOẠCH TIẾN ĐỘ THỰC HIỆN TỔNG THỂ (25/08/2026 - 30/10/2026)</text>
    <rect x="940" y="14" width="160" height="24" rx="12" fill="#dbeafe"/>
    <text x="1020" y="30" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1d4ed8">Tổng thời gian: 10 Tuần</text>
    <rect x="1115" y="14" width="175" height="24" rx="12" fill="#dcfce7"/>
    <text x="1202" y="30" text-anchor="middle" font-size="11.5" font-weight="700" fill="#15803d">Trạng thái: 100% Hoàn thành</text>

    <!-- Table Header Columns -->
    <!-- Col 1: Phase Name (0 - 320) -->
    <!-- Col 2: Owner (320 - 450) -->
    <!-- Timeline Area: 450 - 1300 (width = 850px for 10 weeks: 85px/week) -->
    <rect x="0" y="60" width="320" height="40" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1"/>
    <text x="160" y="85" text-anchor="middle" font-size="12.5" font-weight="700" fill="#334155">Giai đoạn thực hiện (WBS / Phase)</text>

    <rect x="320" y="60" width="130" height="40" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1"/>
    <text x="385" y="85" text-anchor="middle" font-size="12.5" font-weight="700" fill="#334155">Phụ trách</text>

    <!-- Timeline weeks 1 to 10 -->
    <!-- Week width = 85px each -->
    <!-- W1: 25/8, W2: 1/9, W3: 8/9, W4: 15/9, W5: 22/9, W6: 29/9, W7: 6/10, W8: 13/10, W9: 20/10, W10: 27/10 -->
    <!-- 450 + 85*i -->
    <g>
      <rect x="450" y="60" width="85" height="40" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>
      <text x="492" y="78" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1e293b">Tuần 1</text>
      <text x="492" y="93" text-anchor="middle" font-size="9.5" fill="#64748b">25/08</text>

      <rect x="535" y="60" width="85" height="40" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>
      <text x="577" y="78" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1e293b">Tuần 2</text>
      <text x="577" y="93" text-anchor="middle" font-size="9.5" fill="#64748b">01/09</text>

      <rect x="620" y="60" width="85" height="40" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>
      <text x="662" y="78" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1e293b">Tuần 3</text>
      <text x="662" y="93" text-anchor="middle" font-size="9.5" fill="#64748b">08/09</text>

      <rect x="705" y="60" width="85" height="40" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>
      <text x="747" y="78" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1e293b">Tuần 4</text>
      <text x="747" y="93" text-anchor="middle" font-size="9.5" fill="#64748b">15/09</text>

      <rect x="790" y="60" width="85" height="40" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>
      <text x="832" y="78" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1e293b">Tuần 5</text>
      <text x="832" y="93" text-anchor="middle" font-size="9.5" fill="#64748b">22/09</text>

      <rect x="875" y="60" width="85" height="40" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>
      <text x="917" y="78" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1e293b">Tuần 6</text>
      <text x="917" y="93" text-anchor="middle" font-size="9.5" fill="#64748b">29/09</text>

      <rect x="960" y="60" width="85" height="40" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>
      <text x="1002" y="78" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1e293b">Tuần 7</text>
      <text x="1002" y="93" text-anchor="middle" font-size="9.5" fill="#64748b">06/10</text>

      <rect x="1045" y="60" width="85" height="40" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>
      <text x="1087" y="78" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1e293b">Tuần 8</text>
      <text x="1087" y="93" text-anchor="middle" font-size="9.5" fill="#64748b">13/10</text>

      <rect x="1130" y="60" width="85" height="40" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>
      <text x="1172" y="78" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1e293b">Tuần 9</text>
      <text x="1172" y="93" text-anchor="middle" font-size="9.5" fill="#64748b">20/10</text>

      <rect x="1215" y="60" width="85" height="40" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1"/>
      <text x="1257" y="78" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1e293b">Tuần 10</text>
      <text x="1257" y="93" text-anchor="middle" font-size="9.5" fill="#64748b">27/10</text>
    </g>

    <!-- Grid background lines for timeline -->
    <g stroke="#f1f5f9" stroke-width="1">
      <line x1="535" y1="100" x2="535" y2="670"/>
      <line x1="620" y1="100" x2="620" y2="670"/>
      <line x1="705" y1="100" x2="705" y2="670"/>
      <line x1="790" y1="100" x2="790" y2="670"/>
      <line x1="875" y1="100" x2="875" y2="670"/>
      <line x1="960" y1="100" x2="960" y2="670"/>
      <line x1="1045" y1="100" x2="1045" y2="670"/>
      <line x1="1130" y1="100" x2="1130" y2="670"/>
      <line x1="1215" y1="100" x2="1215" y2="670"/>
      <line x1="1300" y1="100" x2="1300" y2="670"/>
    </g>

    <!-- ROWS (Height = 65px each, 8 rows => 100 + 8*65 = 620) -->

    <!-- ROW 1: Phase 1 (25/8 - 29/8) (5 days) -->
    <!-- y = 105 -->
    <rect x="0" y="105" width="1300" height="60" fill="#ffffff" stroke="#e2e8f0" stroke-width="1"/>
    <text x="15" y="132" font-size="12" font-weight="700" fill="#1e293b">Phase 1: Khởi động &amp; Đánh giá hiện trạng</text>
    <text x="15" y="150" font-size="10.5" fill="#64748b">Kick-off, RACI, rà soát backend &amp; client</text>
    <rect x="330" y="122" width="110" height="24" rx="4" fill="#eff6ff"/>
    <text x="385" y="138" text-anchor="middle" font-size="11" font-weight="600" fill="#1d4ed8">Đô &amp; Thọ</text>
    <!-- Bar: 25/8 -> 29/8 (Tuần 1: x=450 to 510) -->
    <rect x="450" y="118" width="65" height="32" rx="6" fill="url(#gP1)" filter="url(#shadow)"/>
    <text x="482" y="138" text-anchor="middle" font-size="11" font-weight="700" fill="#ffffff">5d</text>

    <!-- ROW 2: Phase 2 (28/8 - 6/9) (10 days) -->
    <!-- y = 175 -->
    <rect x="0" y="175" width="1300" height="60" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
    <text x="15" y="202" font-size="12" font-weight="700" fill="#1e293b">Phase 2: Yêu cầu, Thiết kế &amp; Đo Baseline</text>
    <text x="15" y="220" font-size="10.5" fill="#64748b">Chốt MVP, 500 mẫu Fresh500, baseline BLEU/Latency</text>
    <rect x="330" y="192" width="110" height="24" rx="4" fill="#eff6ff"/>
    <text x="385" y="208" text-anchor="middle" font-size="11" font-weight="600" fill="#1d4ed8">Đô &amp; Thọ</text>
    <!-- Bar: 28/8 -> 6/9 (x=495 to 615, w=120) -->
    <rect x="495" y="188" width="120" height="32" rx="6" fill="url(#gP2)" filter="url(#shadow)"/>
    <text x="555" y="208" text-anchor="middle" font-size="11" font-weight="700" fill="#ffffff">10 ngày</text>

    <!-- ROW 3: Phase 3 (7/9 - 27/9) (21 days) -->
    <!-- y = 245 -->
    <rect x="0" y="245" width="1300" height="60" fill="#ffffff" stroke="#e2e8f0" stroke-width="1"/>
    <text x="15" y="272" font-size="12" font-weight="700" fill="#1e293b">Phase 3: Hoàn thiện Web Admin &amp; Quản trị</text>
    <text x="15" y="290" font-size="10.5" fill="#64748b">Argon2id, MFA, RBAC, Dictionary, MQM QA, Audit log</text>
    <rect x="330" y="262" width="110" height="24" rx="4" fill="#f0fdfa"/>
    <text x="385" y="278" text-anchor="middle" font-size="11" font-weight="600" fill="#0f766e">Thọ &amp; Đô</text>
    <!-- Bar: 7/9 -> 27/9 (Tuần 3 -> Tuần 5: x=610 to 865, w=255) -->
    <rect x="610" y="258" width="255" height="32" rx="6" fill="url(#gP3)" filter="url(#shadow)"/>
    <text x="737" y="278" text-anchor="middle" font-size="11" font-weight="700" fill="#ffffff">21 ngày (Web Admin &amp; MQM QA)</text>

    <!-- ROW 4: Phase 4 (7/9 - 5/10) (29 days) -->
    <!-- y = 315 -->
    <rect x="0" y="315" width="1300" height="60" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
    <text x="15" y="342" font-size="12" font-weight="700" fill="#1e293b">Phase 4: Nâng chất lượng dịch &amp; Huấn luyện LoRA</text>
    <text x="15" y="360" font-size="10.5" fill="#64748b">Translation Memory, Glossary, LoRA Whisper &amp; NLLB</text>
    <rect x="330" y="332" width="110" height="24" rx="4" fill="#faf5ff"/>
    <text x="385" y="348" text-anchor="middle" font-size="11" font-weight="600" fill="#6b21a8">Đô (Chính) &amp; Thọ</text>
    <!-- Bar: 7/9 -> 5/10 (Tuần 3 -> Tuần 7: x=610 to 960, w=350) -->
    <rect x="610" y="328" width="350" height="32" rx="6" fill="url(#gP4)" filter="url(#shadow)"/>
    <text x="785" y="348" text-anchor="middle" font-size="11" font-weight="700" fill="#ffffff">29 ngày (Huấn luyện LoRA &amp; Quality Gate)</text>

    <!-- ROW 5: Phase 5 (14/9 - 10/10) (27 days) -->
    <!-- y = 385 -->
    <rect x="0" y="385" width="1300" height="60" fill="#ffffff" stroke="#e2e8f0" stroke-width="1"/>
    <text x="15" y="412" font-size="12" font-weight="700" fill="#1e293b">Phase 5: Tối ưu tốc độ &amp; Ổn định đường ống</text>
    <text x="15" y="430" font-size="10.5" fill="#64748b">WebRTC VAD 500ms, CTranslate2 INT8, P95 &lt; 1.2s</text>
    <rect x="330" y="402" width="110" height="24" rx="4" fill="#fff7ed"/>
    <text x="385" y="418" text-anchor="middle" font-size="11" font-weight="600" fill="#c2410c">Đô &amp; Thọ</text>
    <!-- Bar: 14/9 -> 10/10 (Tuần 4 -> Tuần 8: x=695 to 1020, w=325) -->
    <rect x="695" y="398" width="325" height="32" rx="6" fill="url(#gP5)" filter="url(#shadow)"/>
    <text x="857" y="418" text-anchor="middle" font-size="11" font-weight="700" fill="#ffffff">27 ngày (Tối ưu VAD, CTranslate2 INT8)</text>

    <!-- ROW 6: Phase 6 (1/10 - 15/10) (15 days) -->
    <!-- y = 455 -->
    <rect x="0" y="455" width="1300" height="60" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
    <text x="15" y="482" font-size="12" font-weight="700" fill="#1e293b">Phase 6: Tích hợp Frontend – Backend</text>
    <text x="15" y="500" font-size="10.5" fill="#64748b">Dual-Mic Mutex Lock, WebSocket stream, Haptic feedback</text>
    <rect x="330" y="472" width="110" height="24" rx="4" fill="#eef2ff"/>
    <text x="385" y="488" text-anchor="middle" font-size="11" font-weight="600" fill="#3730a3">Đô &amp; Thọ</text>
    <!-- Bar: 1/10 -> 15/10 (Tuần 6 -> Tuần 8: x=900 to 1080, w=180) -->
    <rect x="900" y="468" width="180" height="32" rx="6" fill="url(#gP6)" filter="url(#shadow)"/>
    <text x="990" y="488" text-anchor="middle" font-size="11" font-weight="700" fill="#ffffff">15 ngày (E2E Integration)</text>

    <!-- ROW 7: Phase 7 (12/10 - 23/10) (12 days) -->
    <!-- y = 525 -->
    <rect x="0" y="525" width="1300" height="60" fill="#ffffff" stroke="#e2e8f0" stroke-width="1"/>
    <text x="15" y="552" font-size="12" font-weight="700" fill="#1e293b">Phase 7: Kiểm thử toàn diện, Bảo mật &amp; UAT</text>
    <text x="15" y="570" font-size="10.5" fill="#64748b">Deep Chaos 109 Test Suite, OWASP, PII &amp; Consent audit</text>
    <rect x="330" y="542" width="110" height="24" rx="4" fill="#fff1f2"/>
    <text x="385" y="558" text-anchor="middle" font-size="11" font-weight="600" fill="#be123c">Đô &amp; Thọ</text>
    <!-- Bar: 12/10 -> 23/10 (Tuần 8 -> Tuần 9: x=1035 to 1180, w=145) -->
    <rect x="1035" y="538" width="145" height="32" rx="6" fill="url(#gP7)" filter="url(#shadow)"/>
    <text x="1107" y="558" text-anchor="middle" font-size="11" font-weight="700" fill="#ffffff">12d (Chaos &amp; UAT)</text>

    <!-- ROW 8: Phase 8 (24/10 - 30/10) (7 days) -->
    <!-- y = 595 -->
    <rect x="0" y="595" width="1300" height="60" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
    <text x="15" y="622" font-size="12" font-weight="700" fill="#1e293b">Phase 8: Triển khai, Đóng gói &amp; Bàn giao</text>
    <text x="15" y="640" font-size="10.5" fill="#64748b">Diễn tập Canary 90/10, Rollback &lt; 1s, Go-Live 30/10</text>
    <rect x="330" y="612" width="110" height="24" rx="4" fill="#ecfdf5"/>
    <text x="385" y="628" text-anchor="middle" font-size="11" font-weight="600" fill="#047857">Đô &amp; Thọ</text>
    <!-- Bar: 24/10 -> 30/10 (Tuần 9 -> Tuần 10: x=1180 to 1290, w=110) -->
    <rect x="1180" y="608" width="110" height="32" rx="6" fill="url(#gP8)" filter="url(#shadow)"/>
    <text x="1235" y="628" text-anchor="middle" font-size="11" font-weight="700" fill="#ffffff">7d (Go-Live)</text>

    <!-- Milestones markers at bottom (y = 680 to 760) -->
    <rect x="0" y="670" width="1300" height="90" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
    <text x="20" y="695" font-size="12" font-weight="700" fill="#0f172a">CÁC CỘT MỐC QUYẾT ĐỊNH (PROJECT MILESTONES):</text>

    <!-- Milestone 1 -->
    <g transform="translate(615, 680)">
      <polygon points="0,5 6,0 12,5 6,10" fill="#0284c7"/>
      <text x="6" y="24" text-anchor="middle" font-size="10" font-weight="700" fill="#0369a1">M1: 06/09</text>
      <text x="6" y="37" text-anchor="middle" font-size="9" fill="#475569">Baseline chốt</text>
    </g>

    <!-- Milestone 2 -->
    <g transform="translate(865, 680)">
      <polygon points="0,5 6,0 12,5 6,10" fill="#0d9488"/>
      <text x="6" y="24" text-anchor="middle" font-size="10" font-weight="700" fill="#0f766e">M2: 27/09</text>
      <text x="6" y="37" text-anchor="middle" font-size="9" fill="#475569">Admin &amp; MQM</text>
    </g>

    <!-- Milestone 3 -->
    <g transform="translate(960, 680)">
      <polygon points="0,5 6,0 12,5 6,10" fill="#7c3aed"/>
      <text x="6" y="24" text-anchor="middle" font-size="10" font-weight="700" fill="#6d28d9">M3: 05/10</text>
      <text x="6" y="37" text-anchor="middle" font-size="9" fill="#475569">Quality Gate</text>
    </g>

    <!-- Milestone 4 -->
    <g transform="translate(1020, 680)">
      <polygon points="0,5 6,0 12,5 6,10" fill="#ea580c"/>
      <text x="6" y="24" text-anchor="middle" font-size="10" font-weight="700" fill="#c2410c">M4: 10/10</text>
      <text x="6" y="37" text-anchor="middle" font-size="9" fill="#475569">Perf Gate P95</text>
    </g>

    <!-- Milestone 5 -->
    <g transform="translate(1080, 680)">
      <polygon points="0,5 6,0 12,5 6,10" fill="#4f46e5"/>
      <text x="6" y="24" text-anchor="middle" font-size="10" font-weight="700" fill="#4338ca">M5: 15/10</text>
      <text x="6" y="37" text-anchor="middle" font-size="9" fill="#475569">Integ Freeze</text>
    </g>

    <!-- Milestone 6 -->
    <g transform="translate(1180, 680)">
      <polygon points="0,5 6,0 12,5 6,10" fill="#e11d48"/>
      <text x="6" y="24" text-anchor="middle" font-size="10" font-weight="700" fill="#be123c">M6: 23/10</text>
      <text x="6" y="37" text-anchor="middle" font-size="9" fill="#475569">UAT &amp; Security</text>
    </g>

    <!-- Milestone 7 -->
    <g transform="translate(1280, 680)">
      <polygon points="0,5 6,0 12,5 6,10" fill="#059669"/>
      <text x="6" y="24" text-anchor="middle" font-size="10" font-weight="700" fill="#047857">M7: 30/10</text>
      <text x="6" y="37" text-anchor="middle" font-size="9" fill="#047857">Go-Live 100%</text>
    </g>
  </svg>
</div>
</body>
</html>
"""
    out_png = os.path.join(OUT_DIR, "hinh_5_1_bieu_do_gantt_ke_hoach_du_an.png")
    render_html_to_png(html, out_png, width=1400, height=860)

# ==============================================================================
# HÌNH 5.2: Sơ đồ quy trình phối hợp làm việc nhóm và CI/CD Git Workflow
# ==============================================================================
def generate_hinh_5_2():
    # Width 1360, Height 750
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 1360px;
    height: 750px;
  }
  .container {
    width: 1320px;
    height: 710px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    display: flex;
    flex-direction: column;
  }
  svg { width: 100%; height: 100%; }
</style>
</head>
<body>
<div class="container">
  <svg viewBox="0 0 1270 660">
    <defs>
      <linearGradient id="gHeader" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#1e293b"/><stop offset="100%" stop-color="#334155"/>
      </linearGradient>
      <linearGradient id="gCol1" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#eff6ff"/><stop offset="100%" stop-color="#dbeafe"/>
      </linearGradient>
      <linearGradient id="gCol2" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#fdf4ff"/><stop offset="100%" stop-color="#fae8ff"/>
      </linearGradient>
      <linearGradient id="gCol3" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#f0fdf4"/><stop offset="100%" stop-color="#dcfce7"/>
      </linearGradient>
      <linearGradient id="gCol4" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#fff7ed"/><stop offset="100%" stop-color="#ffedd5"/>
      </linearGradient>
      <filter id="shadow" x="-5%" y="-10%" width="110%" height="130%">
        <feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity="0.12"/>
      </filter>
    </defs>

    <!-- Top info bar -->
    <rect x="0" y="0" width="1270" height="46" rx="6" fill="url(#gHeader)"/>
    <text x="25" y="28" font-size="14" font-weight="700" fill="#ffffff">QUY TRÌNH PHỐI HỢP LÀM VIỆC NHÓM AGILE VÀ QUẢN TRỊ MÃ NGUỒN GIT FLOW / CI-CD</text>
    <text x="1245" y="28" text-anchor="end" font-size="12" fill="#94a3b8">Hệ thống T-Lingua (Hà Văn Đô &amp; Nguyễn Quang Thọ)</text>

    <!-- 4 Workflow Pillars -->
    <!-- Pillar 1: Lập kế hoạch & Quản lý Task (x = 10, w = 295) -->
    <rect x="10" y="60" width="295" height="580" rx="10" fill="url(#gCol1)" stroke="#bfdbfe" stroke-width="1.5"/>
    <rect x="25" y="75" width="265" height="36" rx="6" fill="#2563eb"/>
    <text x="157" y="98" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">1. KẾ HOẠCH &amp; TASK BACKLOG</text>

    <g transform="translate(25, 125)">
      <!-- Box 1.1 -->
      <rect x="0" y="0" width="265" height="95" rx="6" fill="#ffffff" stroke="#93c5fd" stroke-width="1" filter="url(#shadow)"/>
      <text x="15" y="24" font-size="12" font-weight="700" fill="#1e3a8a">Quản trị Backlog (Jira / WBS):</text>
      <text x="15" y="44" font-size="11" fill="#334155">• 61 tasks chi tiết chia 8 phases</text>
      <text x="15" y="62" font-size="11" fill="#334155">• Tiêu chí chấp thuận Definition of Done</text>
      <text x="15" y="80" font-size="11" fill="#334155">• Đánh giá ưu tiên P0 / P1 / P2</text>

      <!-- Box 1.2 -->
      <rect x="0" y="110" width="265" height="105" rx="6" fill="#ffffff" stroke="#93c5fd" stroke-width="1" filter="url(#shadow)"/>
      <text x="15" y="134" font-size="12" font-weight="700" fill="#1e3a8a">Giao tiếp &amp; Đồng bộ hàng ngày:</text>
      <text x="15" y="154" font-size="11" fill="#334155">• Daily Standup 15m (3 câu hỏi cốt lõi)</text>
      <text x="15" y="172" font-size="11" fill="#334155">• Weekly Retrospective tổng kết tuần</text>
      <text x="15" y="190" font-size="11" fill="#334155">• Trao đổi kỹ thuật qua Telegram/Meet</text>
      <text x="15" y="206" font-size="10.5" fill="#2563eb">→ Giải quyết rào cản kỹ thuật tức thì</text>

      <!-- Box 1.3 -->
      <rect x="0" y="230" width="265" height="110" rx="6" fill="#ffffff" stroke="#93c5fd" stroke-width="1" filter="url(#shadow)"/>
      <text x="15" y="254" font-size="12" font-weight="700" fill="#1e3a8a">Hợp đồng giao diện (API Contract):</text>
      <text x="15" y="274" font-size="11" fill="#334155">• Chốt JSON Schema &amp; WebSocket Protobuf</text>
      <text x="15" y="292" font-size="11" fill="#334155">• Mock server cho client phát triển trước</text>
      <text x="15" y="310" font-size="11" fill="#334155">• Tránh phụ thuộc chéo giữa FE &amp; BE</text>
      <text x="15" y="328" font-size="10.5" fill="#059669">→ Hai kỹ sư song song độc lập</text>
    </g>

    <!-- Arrow 1 -> 2 -->
    <path d="M 305 340 L 325 340" stroke="#3b82f6" stroke-width="3" fill="none" marker-end="url(#arrow)"/>

    <!-- Pillar 2: Phát triển & Git Branching (x = 325, w = 300) -->
    <rect x="325" y="60" width="300" height="580" rx="10" fill="url(#gCol2)" stroke="#f0abfc" stroke-width="1.5"/>
    <rect x="340" y="75" width="270" height="36" rx="6" fill="#9333ea"/>
    <text x="475" y="98" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">2. QUẢN LÝ MÃ NGUỒN GIT FLOW</text>

    <g transform="translate(340, 125)">
      <!-- Box 2.1 -->
      <rect x="0" y="0" width="270" height="135" rx="6" fill="#ffffff" stroke="#d8b4fe" stroke-width="1" filter="url(#shadow)"/>
      <text x="15" y="24" font-size="12" font-weight="700" fill="#581c87">Chiến lược phân nhánh (Branching):</text>
      <rect x="15" y="34" width="70" height="20" rx="3" fill="#fee2e2"/><text x="50" y="48" text-anchor="middle" font-size="10.5" font-weight="700" fill="#b91c1c">main</text>
      <text x="95" y="48" font-size="11" fill="#334155">Production (v1.0.0 Tagged)</text>

      <rect x="15" y="60" width="70" height="20" rx="3" fill="#e0e7ff"/><text x="50" y="74" text-anchor="middle" font-size="10.5" font-weight="700" fill="#4338ca">develop</text>
      <text x="95" y="74" font-size="11" fill="#334155">Nhánh tích hợp liên tục</text>

      <rect x="15" y="86" width="70" height="20" rx="3" fill="#f3e8ff"/><text x="50" y="100" text-anchor="middle" font-size="10.5" font-weight="700" fill="#6b21a8">feature/*</text>
      <text x="95" y="100" font-size="11" fill="#334155">Nhánh tính năng độc lập</text>

      <rect x="15" y="112" width="70" height="18" rx="3" fill="#fef3c7"/><text x="50" y="125" text-anchor="middle" font-size="10" font-weight="700" fill="#b45309">fix / perf</text>
      <text x="95" y="125" font-size="10.5" fill="#334155">Sửa lỗi &amp; Tối ưu hiệu năng</text>

      <!-- Box 2.2 -->
      <rect x="0" y="150" width="270" height="120" rx="6" fill="#ffffff" stroke="#d8b4fe" stroke-width="1" filter="url(#shadow)"/>
      <text x="15" y="174" font-size="12" font-weight="700" fill="#581c87">Quy ước Commit chuẩn mực:</text>
      <text x="15" y="196" font-size="10.5" fill="#334155"><tspan font-weight="700" fill="#2563eb">feat:</tspan> Thêm tính năng mới (WebSocket VAD)</text>
      <text x="15" y="214" font-size="10.5" fill="#334155"><tspan font-weight="700" fill="#dc2626">fix:</tspan> Sửa lỗi xung đột Mutex thoại</text>
      <text x="15" y="232" font-size="10.5" fill="#334155"><tspan font-weight="700" fill="#d97706">perf:</tspan> Nén mô hình CTranslate2 INT8</text>
      <text x="15" y="250" font-size="10.5" fill="#334155"><tspan font-weight="700" fill="#059669">test:</tspan> Bộ kiểm thử Deep Chaos 109</text>
    </g>

    <!-- Arrow 2 -> 3 -->
    <path d="M 625 340 L 645 340" stroke="#9333ea" stroke-width="3" fill="none"/>

    <!-- Pillar 3: Review chéo & CI/CD Gate (x = 645, w = 300) -->
    <rect x="645" y="60" width="300" height="580" rx="10" fill="url(#gCol3)" stroke="#86efac" stroke-width="1.5"/>
    <rect x="660" y="75" width="270" height="36" rx="6" fill="#16a34a"/>
    <text x="795" y="98" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">3. REVIEW CHÉO &amp; QUALITY GATE</text>

    <g transform="translate(660, 125)">
      <!-- Box 3.1 -->
      <rect x="0" y="0" width="270" height="110" rx="6" fill="#ffffff" stroke="#86efac" stroke-width="1" filter="url(#shadow)"/>
      <text x="15" y="24" font-size="12" font-weight="700" fill="#14532d">Bắt buộc Review chéo (Peer Review):</text>
      <text x="15" y="44" font-size="11" fill="#334155">• 100% PR cần Approve từ đồng đội</text>
      <text x="15" y="62" font-size="11" fill="#334155">• Hà Văn Đô review kiến trúc &amp; API FE</text>
      <text x="15" y="80" font-size="11" fill="#334155">• Nguyễn Quang Thọ review tích hợp BE</text>
      <text x="15" y="98" font-size="10.5" fill="#16a34a">→ Không cho phép tự merge code</text>

      <!-- Box 3.2 -->
      <rect x="0" y="125" width="270" height="150" rx="6" fill="#ffffff" stroke="#86efac" stroke-width="1" filter="url(#shadow)"/>
      <text x="15" y="149" font-size="12" font-weight="700" fill="#14532d">Cổng kiểm định tự động (CI Pipeline):</text>
      <text x="15" y="171" font-size="10.5" fill="#334155">✓ <tspan font-weight="600">Linting &amp; Format:</tspan> flake8, black, dart analyze</text>
      <text x="15" y="191" font-size="10.5" fill="#334155">✓ <tspan font-weight="600">Unit Tests:</tspan> pytest (88.5% coverage)</text>
      <text x="15" y="211" font-size="10.5" fill="#334155">✓ <tspan font-weight="600">Quality Gate:</tspan> BLEU &gt; 35.0, chrF++ &gt; 65.0</text>
      <text x="15" y="231" font-size="10.5" fill="#334155">✓ <tspan font-weight="600">Security Audit:</tspan> Quét PII, JWT, hardcode key</text>
      <text x="15" y="251" font-size="10.5" fill="#334155">✓ <tspan font-weight="600">Performance Gate:</tspan> P95 latency &lt; 1.200 ms</text>
    </g>

    <!-- Arrow 3 -> 4 -->
    <path d="M 945 340 L 965 340" stroke="#16a34a" stroke-width="3" fill="none"/>

    <!-- Pillar 4: Triển khai Staging & Production (x = 965, w = 295) -->
    <rect x="965" y="60" width="295" height="580" rx="10" fill="url(#gCol4)" stroke="#fed7aa" stroke-width="1.5"/>
    <rect x="980" y="75" width="265" height="36" rx="6" fill="#ea580c"/>
    <text x="1112" y="98" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">4. STAGING &amp; CANARY DEPLOY</text>

    <g transform="translate(980, 125)">
      <!-- Box 4.1 -->
      <rect x="0" y="0" width="265" height="110" rx="6" fill="#ffffff" stroke="#fdba74" stroke-width="1" filter="url(#shadow)"/>
      <text x="15" y="24" font-size="12" font-weight="700" fill="#7c2d12">Môi trường Staging kiểm thử E2E:</text>
      <text x="15" y="44" font-size="11" fill="#334155">• Giả lập kết nối mạng 3G/4G chập chờn</text>
      <text x="15" y="62" font-size="11" fill="#334155">• Chạy ma trận Deep Chaos 109 Test Suite</text>
      <text x="15" y="80" font-size="11" fill="#334155">• Kiểm thử tải 50 phiên song phương</text>
      <text x="15" y="98" font-size="10.5" fill="#ea580c">→ Đạt 100% tiêu chí nghiệm thu UAT</text>

      <!-- Box 4.2 -->
      <rect x="0" y="125" width="265" height="150" rx="6" fill="#ffffff" stroke="#fdba74" stroke-width="1" filter="url(#shadow)"/>
      <text x="15" y="149" font-size="12" font-weight="700" fill="#7c2d12">Canary Rollout &amp; Production Deploy:</text>
      <text x="15" y="171" font-size="10.5" fill="#334155">• Điều phối Canary: 90% Stable / 10% Test</text>
      <text x="15" y="191" font-size="10.5" fill="#334155">• Giám sát Telemetry P95 &amp; tỷ lệ lỗi real-time</text>
      <text x="15" y="211" font-size="10.5" fill="#334155">• Tự động Rollback &lt; 1s nếu lỗi vượt 1%</text>
      <text x="15" y="231" font-size="10.5" fill="#334155">• Thăng cấp 100% khi ổn định 24h</text>
      <text x="15" y="251" font-size="10.5" font-weight="700" fill="#15803d">★ Sẵn sàng Go-Live (30/10/2026)</text>
    </g>
  </svg>
</div>
</body>
</html>
"""
    out_png = os.path.join(OUT_DIR, "hinh_5_2_quy_trinh_lam_viec_nhom_git_workflow.png")
    render_html_to_png(html, out_png, width=1360, height=750)

if __name__ == "__main__":
    print("Generating Chapter 5 diagrams...")
    generate_hinh_5_1()
    generate_hinh_5_2()
    print("All Chapter 5 diagrams generated successfully!")

