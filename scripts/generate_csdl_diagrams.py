# -*- coding: utf-8 -*-
"""
Professional ERD diagram generator for T-Lingua Section 3.4
Strictly following the style of [DALN]2210.pdf (Phenikaa University standards).
Outputs high-res PNG diagrams into docs/img/csdl/.
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

def make_box(x, y, w, h, name):
    return f"""
    <g class="entity" transform="translate({x}, {y})">
      <rect x="0" y="0" width="{w}" height="{h}" rx="3" ry="3" fill="#ffffff" stroke="#1e293b" stroke-width="2" filter="url(#shadow)"/>
      <text x="{w/2}" y="{h/2 + 5}" text-anchor="middle" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-weight="600" font-size="14.5" fill="#0f172a" letter-spacing="0.5">{name}</text>
    </g>
    """

def draw_crow_ticks(x, y, dx, dy):
    """Draws || crossbars at point (x, y) along direction (dx, dy)."""
    px, py = -dy, dx
    res = ""
    for dist in [12, 18]:
        cx = x + dx * dist
        cy = y + dy * dist
        x1, y1 = cx + px * 8, cy + py * 8
        x2, y2 = cx - px * 8, cy - py * 8
        res += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#1e293b" stroke-width="2"/>\n'
    return res

def draw_crow_many(x, y, dx, dy):
    """Draws o< (circle + crow's foot fork) touching box at (x, y) arriving from direction (-dx, -dy)."""
    px, py = -dy, dx
    res = ""
    # Circle at dist 22
    cx = x + dx * 22
    cy = y + dy * 22
    res += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.5" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>\n'
    # Fork point at dist 14
    fx = x + dx * 14
    fy = y + dy * 14
    # Three prongs touching box at dist 0
    res += f'<line x1="{fx:.1f}" y1="{fy:.1f}" x2="{x + px * 10:.1f}" y2="{y + py * 10:.1f}" stroke="#1e293b" stroke-width="2"/>\n'
    res += f'<line x1="{fx:.1f}" y1="{fy:.1f}" x2="{x - px * 10:.1f}" y2="{y - py * 10:.1f}" stroke="#1e293b" stroke-width="2"/>\n'
    res += f'<line x1="{fx:.1f}" y1="{fy:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#1e293b" stroke-width="2"/>\n'
    return res

def draw_connection(points, from_type='1', to_type='N', label='', label_pos=None):
    """
    Renders an orthogonal connector between points.
    points: list of (x, y) tuples.
    from_type: '1' or 'N'
    to_type: '1' or 'N'
    """
    path_d = f"M {points[0][0]} {points[0][1]} " + " ".join([f"L {p[0]} {p[1]}" for p in points[1:]])
    res = f'<path d="{path_d}" fill="none" stroke="#1e293b" stroke-width="2"/>\n'
    
    # Start connector
    x0, y0 = points[0]
    x1, y1 = points[1]
    dx0 = 1 if x1 > x0 else (-1 if x1 < x0 else 0)
    dy0 = 1 if y1 > y0 else (-1 if y1 < y0 else 0)
    if from_type == '1':
        res += draw_crow_ticks(x0, y0, dx0, dy0)
    elif from_type == 'N':
        res += draw_crow_many(x0, y0, dx0, dy0)

    # End connector
    xe0, ye0 = points[-1]
    xe1, ye1 = points[-2]
    dxe = 1 if xe1 > xe0 else (-1 if xe1 < xe0 else 0)
    dye = 1 if ye1 > ye0 else (-1 if ye1 < ye0 else 0)
    if to_type == '1':
        res += draw_crow_ticks(xe0, ye0, dxe, dye)
    elif to_type == 'N':
        res += draw_crow_many(xe0, ye0, dxe, dye)

    # Label with white backdrop
    if label:
        if label_pos:
            lx, ly = label_pos
        else:
            mid_idx = len(points) // 2
            lx = (points[mid_idx-1][0] + points[mid_idx][0]) / 2
            ly = (points[mid_idx-1][1] + points[mid_idx][1]) / 2 - 10
        tw = len(label) * 7.5 + 14
        res += f"""
        <g transform="translate({lx}, {ly})">
          <rect x="{-tw/2}" y="-13" width="{tw}" height="20" fill="#ffffff" rx="2" ry="2"/>
          <text x="0" y="2" text-anchor="middle" font-family="'Segoe UI', Roboto, sans-serif" font-size="12" fill="#334155">{label}</text>
        </g>
        """
    return res

def wrap_svg(width, height, content):
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="shadow" x="-5%" y="-5%" width="115%" height="115%">
      <feDropShadow dx="2" dy="3" stdDeviation="2" flood-color="#1e293b" flood-opacity="0.12"/>
    </filter>
  </defs>
{content}
</svg>"""

# ==============================================================================
# 1. HINH 3.28: Sơ đồ CSDL tổng thể hệ thống T-Lingua (17 bảng, Zero Box Intersections)
# ==============================================================================
def generate_hinh_3_28():
    W, H = 1600, 1150
    content = ""
    
    # 4 Columns Grid Layout with ample corridors:
    # Col 1: x = 100..320 (W=220)
    # Col 2: x = 440..680 (W=240)
    # Col 3: x = 800..1040 (W=240)
    # Col 4: x = 1170..1430 (W=260)

    # ROW 1 (y=50)
    content += make_box(100, 50, 220, 80, "AUTH_SESSIONS")
    content += make_box(800, 50, 240, 80, "USERS")
    content += make_box(1170, 50, 260, 80, "API_KEYS")

    # ROW 2 (y=240)
    content += make_box(100, 240, 220, 80, "PIPELINE_METRICS")
    content += make_box(440, 240, 240, 80, "TRANSLATION_LOGS")
    content += make_box(800, 240, 240, 80, "AUDIT_LOGS")
    content += make_box(1170, 240, 260, 80, "TRANSLATION_MEMORY_ENTRIES")

    # ROW 3 (y=430)
    content += make_box(100, 430, 220, 80, "AUDIO_ASSETS")
    content += make_box(440, 430, 240, 80, "TRAINING_AUDIO_ASSETS")
    content += make_box(800, 430, 240, 80, "QUALITY_REVIEWS")

    # ROW 4 (y=650)
    content += make_box(100, 650, 220, 80, "SYSTEM_SETTINGS")
    content += make_box(440, 650, 240, 80, "TRAINING_DATASETS")
    content += make_box(800, 650, 240, 80, "TRAINING_JOBS")
    content += make_box(1170, 650, 260, 80, "MODEL_ARTIFACTS")

    # ROW 5 (y=840)
    content += make_box(800, 840, 240, 80, "TRAINING_JOB_EVENTS")
    content += make_box(1170, 840, 260, 80, "MODEL_DEPLOYMENTS")

    # ROW 6 (y=1000)
    content += make_box(1170, 1000, 260, 80, "DEPLOYMENT_EVENTS")

    # --- CONNECTORS ---
    # USERS -> AUTH_SESSIONS: straight horizontal along y=90
    content += draw_connection([(800, 90), (320, 90)], from_type='1', to_type='N', label="phiên đăng nhập 1-N", label_pos=(560, 75))
    # USERS -> API_KEYS: straight horizontal along y=90
    content += draw_connection([(1040, 90), (1170, 90)], from_type='1', to_type='N', label="sở hữu khóa 1-N", label_pos=(1105, 75))
    # USERS -> AUDIT_LOGS: straight vertical along x=920
    content += draw_connection([(920, 130), (920, 240)], from_type='1', to_type='N', label="ghi vết kiểm toán 1-N", label_pos=(920, 185))

    # USERS -> TRANSLATION_LOGS: corridor between rows 1 and 2
    content += draw_connection([(830, 130), (830, 175), (560, 175), (560, 240)], from_type='1', to_type='N', label="thực hiện dịch 1-N", label_pos=(695, 160))

    # USERS -> QUALITY_REVIEWS: corridor x=1090 between Col 3 and Col 4
    content += draw_connection([(1040, 115), (1095, 115), (1095, 470), (1040, 470)], from_type='1', to_type='N', label="chuyên gia đánh giá 1-N", label_pos=(1095, 350))

    # USERS -> TRANSLATION_MEMORY_ENTRIES: corridor to x=1300
    content += draw_connection([(1020, 130), (1020, 180), (1300, 180), (1300, 240)], from_type='1', to_type='N', label="quản lý thuật ngữ 1-N", label_pos=(1180, 165))

    # TRANSLATION_LOGS -> PIPELINE_METRICS: straight horizontal along y=280
    content += draw_connection([(440, 280), (320, 280)], from_type='1', to_type='N', label="đo kiểm vi mô 1-N", label_pos=(380, 265))

    # TRANSLATION_LOGS -> AUDIO_ASSETS: out bottom at x=480, down to corridor y=370, left to x=210, down to AUDIO_ASSETS
    content += draw_connection([(480, 320), (480, 370), (210, 370), (210, 430)], from_type='1', to_type='1', label="lưu tệp âm thanh 1-1", label_pos=(330, 355))

    # TRANSLATION_LOGS -> TRAINING_AUDIO_ASSETS: straight vertical along x=560
    content += draw_connection([(560, 320), (560, 430)], from_type='1', to_type='1', label="trích xuất âm thanh 1-1", label_pos=(560, 375))

    # TRANSLATION_LOGS -> QUALITY_REVIEWS: corridor x=740 between Col 2 and Col 3
    content += draw_connection([(680, 290), (740, 290), (740, 460), (800, 460)], from_type='1', to_type='1', label="thẩm định MQM 1-1", label_pos=(740, 385))

    # QUALITY_REVIEWS -> TRAINING_DATASETS: corridor y=575
    content += draw_connection([(800, 490), (740, 490), (740, 575), (560, 575), (560, 650)], from_type='1', to_type='N', label="đóng gói tập dữ liệu 1-N", label_pos=(650, 560))

    # TRAINING_DATASETS -> TRAINING_JOBS: straight horizontal along y=690
    content += draw_connection([(680, 690), (800, 690)], from_type='1', to_type='N', label="khởi tạo huấn luyện 1-N", label_pos=(740, 675))

    # TRAINING_JOBS -> TRAINING_JOB_EVENTS: straight vertical along x=920
    content += draw_connection([(920, 730), (920, 840)], from_type='1', to_type='N', label="ghi nhận telemetry 1-N", label_pos=(920, 785))

    # TRAINING_JOBS -> MODEL_ARTIFACTS: straight horizontal along y=690
    content += draw_connection([(1040, 690), (1170, 690)], from_type='1', to_type='1', label="đóng gói trọng số 1-1", label_pos=(1105, 675))

    # MODEL_ARTIFACTS -> MODEL_DEPLOYMENTS: straight vertical along x=1300
    content += draw_connection([(1300, 730), (1300, 840)], from_type='1', to_type='N', label="triển khai phục vụ 1-N", label_pos=(1300, 785))

    # MODEL_DEPLOYMENTS -> DEPLOYMENT_EVENTS: straight vertical along x=1300
    content += draw_connection([(1300, 920), (1300, 1000)], from_type='1', to_type='N', label="lịch sử thăng cấp / rollback 1-N", label_pos=(1300, 960))

    # USERS -> SYSTEM_SETTINGS: outer corridor on left along x=45
    content += draw_connection([(800, 70), (760, 70), (760, 25), (45, 25), (45, 690), (100, 690)], from_type='1', to_type='N', label="thiết lập tham số 1-N", label_pos=(45, 360))

    # SYSTEM_SETTINGS -> AUDIT_LOGS: corridor between Col 2 and Col 3 along x=720, up to corridor y=350, right to x=860, up to bottom of AUDIT_LOGS
    content += draw_connection([(320, 690), (380, 690), (380, 520), (720, 520), (720, 350), (860, 350), (860, 320)], from_type='1', to_type='N', label="lưu vết cấu hình 1-N", label_pos=(540, 505))

    svg = wrap_svg(W, H, content)
    out_file = os.path.join(OUT_DIR, "hinh_3_28_sodo_csdl_tong_the_t_lingua.png")
    render_svg_to_png(svg, out_file, width=W, height=H)

# ==============================================================================
# 2. HINH 3.29: Sơ đồ CSDL nhóm tài khoản, người dùng và phân quyền
# ==============================================================================
def generate_hinh_3_29():
    W, H = 1100, 540
    content = ""
    content += make_box(430, 45, 240, 85, "USERS")
    content += make_box(60, 360, 240, 85, "AUTH_SESSIONS")
    content += make_box(430, 360, 240, 85, "AUDIT_LOGS")
    content += make_box(800, 360, 240, 85, "API_KEYS")

    content += draw_connection([(490, 130), (490, 230), (180, 230), (180, 360)], from_type='1', to_type='N', label="phiên đăng nhập 1-N", label_pos=(280, 215))
    content += draw_connection([(550, 130), (550, 360)], from_type='1', to_type='N', label="ghi vết kiểm toán 1-N", label_pos=(550, 245))
    content += draw_connection([(610, 130), (610, 230), (920, 230), (920, 360)], from_type='1', to_type='N', label="sở hữu khóa API 1-N", label_pos=(820, 215))

    svg = wrap_svg(W, H, content)
    out_file = os.path.join(OUT_DIR, "hinh_3_29_nhom_tai_khoan_nguoi_dung_phan_quyen.png")
    render_svg_to_png(svg, out_file, width=W, height=H)

# ==============================================================================
# 3. HINH 3.30: Sơ đồ CSDL nhóm dịch thuật, tài sản âm thanh và đo kiểm Telemetry
# ==============================================================================
def generate_hinh_3_30():
    W, H = 1100, 560
    content = ""
    content += make_box(430, 40, 240, 85, "USERS")
    content += make_box(430, 210, 240, 85, "TRANSLATION_LOGS")
    content += make_box(130, 390, 250, 85, "PIPELINE_METRICS")
    content += make_box(720, 390, 250, 85, "AUDIO_ASSETS")

    content += draw_connection([(550, 125), (550, 210)], from_type='1', to_type='N', label="thực hiện dịch 1-N", label_pos=(550, 168))
    content += draw_connection([(490, 295), (490, 340), (255, 340), (255, 390)], from_type='1', to_type='N', label="đo kiểm vi mô 1-N", label_pos=(360, 328))
    content += draw_connection([(610, 295), (610, 340), (845, 340), (845, 390)], from_type='1', to_type='1', label="lưu tệp âm thanh 1-1", label_pos=(740, 328))

    svg = wrap_svg(W, H, content)
    out_file = os.path.join(OUT_DIR, "hinh_3_30_nhom_dich_thuat_audio_telemetry.png")
    render_svg_to_png(svg, out_file, width=W, height=H)

# ==============================================================================
# 4. HINH 3.31: Sơ đồ CSDL nhóm bộ nhớ dịch và kiểm chuẩn chất lượng (TM & QA)
# ==============================================================================
def generate_hinh_3_31():
    W, H = 1200, 580
    content = ""
    content += make_box(160, 45, 250, 85, "TRANSLATION_LOGS")
    content += make_box(790, 45, 250, 85, "USERS")
    content += make_box(475, 220, 250, 85, "QUALITY_REVIEWS")
    content += make_box(160, 410, 250, 85, "TRAINING_AUDIO_ASSETS")
    content += make_box(790, 410, 280, 85, "TRANSLATION_MEMORY_ENTRIES")

    # Connectors
    # TRANSLATION_LOGS -> QUALITY_REVIEWS
    content += draw_connection([(285, 130), (285, 262), (475, 262)], from_type='1', to_type='1', label="thẩm định MQM 1-1", label_pos=(370, 248))
    # USERS -> QUALITY_REVIEWS
    content += draw_connection([(915, 130), (915, 262), (725, 262)], from_type='1', to_type='N', label="chuyên gia đánh giá 1-N", label_pos=(830, 248))
    # TRANSLATION_LOGS -> TRAINING_AUDIO_ASSETS
    content += draw_connection([(210, 130), (210, 410)], from_type='1', to_type='1', label="trích xuất âm thanh 1-1", label_pos=(210, 280))
    # USERS -> TRANSLATION_MEMORY_ENTRIES
    content += draw_connection([(960, 130), (960, 410)], from_type='1', to_type='N', label="quản lý thuật ngữ 1-N", label_pos=(960, 340))

    svg = wrap_svg(W, H, content)
    out_file = os.path.join(OUT_DIR, "hinh_3_31_nhom_bo_nho_dich_qa.png")
    render_svg_to_png(svg, out_file, width=W, height=H)

# ==============================================================================
# 5. HINH 3.32: Sơ đồ CSDL nhóm MLOps, dữ liệu và vòng đời mô hình
# ==============================================================================
def generate_hinh_3_32():
    W, H = 1200, 680
    content = ""
    content += make_box(60, 70, 240, 85, "TRAINING_DATASETS")
    content += make_box(480, 70, 240, 85, "TRAINING_JOBS")
    content += make_box(900, 70, 240, 85, "MODEL_ARTIFACTS")

    content += make_box(480, 270, 240, 85, "TRAINING_JOB_EVENTS")
    content += make_box(900, 270, 240, 85, "MODEL_DEPLOYMENTS")
    content += make_box(900, 470, 240, 85, "DEPLOYMENT_EVENTS")

    content += draw_connection([(300, 112), (480, 112)], from_type='1', to_type='N', label="khởi tạo huấn luyện 1-N", label_pos=(390, 98))
    content += draw_connection([(720, 112), (900, 112)], from_type='1', to_type='1', label="đóng gói trọng số 1-1", label_pos=(810, 98))
    content += draw_connection([(600, 155), (600, 270)], from_type='1', to_type='N', label="ghi nhận telemetry 1-N", label_pos=(600, 212))
    content += draw_connection([(1020, 155), (1020, 270)], from_type='1', to_type='N', label="triển khai phục vụ 1-N", label_pos=(1020, 212))
    content += draw_connection([(1020, 355), (1020, 470)], from_type='1', to_type='N', label="lịch sử thăng cấp / rollback 1-N", label_pos=(1020, 412))

    svg = wrap_svg(W, H, content)
    out_file = os.path.join(OUT_DIR, "hinh_3_32_nhom_mlops_vong_doi_mo_hinh.png")
    render_svg_to_png(svg, out_file, width=W, height=H)

# ==============================================================================
# 6. HINH 3.33: Sơ đồ CSDL nhóm cấu hình và tham số hệ thống
# ==============================================================================
def generate_hinh_3_33():
    W, H = 1000, 480
    content = ""
    content += make_box(380, 45, 240, 85, "USERS")
    content += make_box(380, 215, 240, 85, "SYSTEM_SETTINGS")
    content += make_box(380, 375, 240, 85, "AUDIT_LOGS")

    content += draw_connection([(500, 130), (500, 215)], from_type='1', to_type='N', label="thiết lập tham số 1-N", label_pos=(500, 172))
    content += draw_connection([(500, 300), (500, 375)], from_type='1', to_type='N', label="lưu vết cấu hình 1-N", label_pos=(500, 338))

    svg = wrap_svg(W, H, content)
    out_file = os.path.join(OUT_DIR, "hinh_3_33_nhom_cau_hinh_he_thong.png")
    render_svg_to_png(svg, out_file, width=W, height=H)

if __name__ == "__main__":
    print("Regenerating all 6 ERD diagrams for Section 3.4...")
    generate_hinh_3_28()
    generate_hinh_3_29()
    generate_hinh_3_30()
    generate_hinh_3_31()
    generate_hinh_3_32()
    generate_hinh_3_33()
    print("All diagrams generated successfully!")
