# -*- coding: utf-8 -*-
"""
High-resolution diagram and chart generator for T-Lingua Chapter 4.
Phenikaa University Thesis Standard.
Generates Figures 4.2 to 4.8 using Headless Chrome rendering.
"""

import os
import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT_DIR = r"C:\Du_an\T_Langua_Test\docs\img"
os.makedirs(OUT_DIR, exist_ok=True)

def render_html_to_png(html_content, out_png_path, width=1200, height=800):
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
# HÌNH 4.2: Lưu đồ thuật toán WebRTC VAD và cơ chế ngắt câu 500ms
# ==============================================================================
def generate_hinh_4_2():
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 1200px;
    height: 900px;
  }
  .container {
    width: 1160px;
    height: 860px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    position: relative;
  }
  .title {
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 20px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  svg {
    width: 100%;
    height: 780px;
  }
</style>
</head>
<body>
<div class="container">
  <div class="title">Lưu đồ thuật toán tách âm WebRTC VAD & Cơ chế ngắt câu tự động (500ms Cutoff)</div>
  <svg viewBox="0 0 1100 760">
    <defs>
      <linearGradient id="gradStart" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#3b82f6"/>
        <stop offset="100%" stop-color="#1d4ed8"/>
      </linearGradient>
      <linearGradient id="gradProcess" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#f8fafc"/>
        <stop offset="100%" stop-color="#f1f5f9"/>
      </linearGradient>
      <linearGradient id="gradDecision" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#fef3c7"/>
        <stop offset="100%" stop-color="#fde68a"/>
      </linearGradient>
      <linearGradient id="gradAction" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#e0f2fe"/>
        <stop offset="100%" stop-color="#bae6fd"/>
      </linearGradient>
      <linearGradient id="gradFinish" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#10b981"/>
        <stop offset="100%" stop-color="#047857"/>
      </linearGradient>
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
        <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.1"/>
      </filter>
      <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#475569"/>
      </marker>
      <marker id="arrowRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#ef4444"/>
      </marker>
      <marker id="arrowGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#10b981"/>
      </marker>
    </defs>

    <!-- 1. START -->
    <rect x="440" y="10" width="220" height="50" rx="25" fill="url(#gradStart)" filter="url(#shadow)"/>
    <text x="550" y="42" text-anchor="middle" font-size="15" font-weight="700" fill="#ffffff">BẮT ĐẦU PHIÊN STREAM</text>

    <!-- Arrow 1 -> 2 -->
    <path d="M 550 60 L 550 95" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

    <!-- 2. Nhận chunk âm thanh -->
    <rect x="410" y="95" width="280" height="60" rx="8" fill="url(#gradProcess)" stroke="#cbd5e1" stroke-width="2" filter="url(#shadow)"/>
    <text x="550" y="122" text-anchor="middle" font-size="14" font-weight="600" fill="#1e293b">Nhận gói PCM 16kHz (20ms / 320 bytes)</text>
    <text x="550" y="142" text-anchor="middle" font-size="12" fill="#64748b">Trích xuất từ WebSocket Client Audio Stream</text>

    <!-- Arrow 2 -> 3 -->
    <path d="M 550 155 L 550 190" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

    <!-- 3. VAD Analysis -->
    <rect x="420" y="190" width="260" height="60" rx="8" fill="url(#gradAction)" stroke="#0284c7" stroke-width="2" filter="url(#shadow)"/>
    <text x="550" y="217" text-anchor="middle" font-size="14" font-weight="600" fill="#0369a1">Phân tích năng lượng & phổ WebRTC VAD</text>
    <text x="550" y="237" text-anchor="middle" font-size="12" fill="#0284c7">Aggressiveness Mode = 3 (Bộ lọc nhiễu cao)</text>

    <!-- Arrow 3 -> 4 -->
    <path d="M 550 250 L 550 285" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

    <!-- 4. Decision: Có giọng nói (is_speech)? -->
    <polygon points="550,285 700,345 550,405 400,345" fill="url(#gradDecision)" stroke="#d97706" stroke-width="2" filter="url(#shadow)"/>
    <text x="550" y="340" text-anchor="middle" font-size="14" font-weight="700" fill="#92400e">Có tiếng nói?</text>
    <text x="550" y="360" text-anchor="middle" font-size="12" fill="#b45309">(is_speech == True)</text>

    <!-- Branch YES: To Right (Active Speech Processing) -->
    <path d="M 700 345 L 830 345" stroke="#10b981" stroke-width="2" marker-end="url(#arrowGreen)"/>
    <text x="750" y="335" font-size="13" font-weight="700" fill="#10b981">ĐÚNG (Có)</text>

    <!-- Box Speech Active -->
    <rect x="830" y="315" width="240" height="120" rx="8" fill="#ecfdf5" stroke="#10b981" stroke-width="2" filter="url(#shadow)"/>
    <text x="950" y="342" text-anchor="middle" font-size="14" font-weight="700" fill="#065f46">XỬ LÝ ĐOẠN NÓI</text>
    <text x="950" y="366" text-anchor="middle" font-size="12" fill="#047857">• Đặt State = ACTIVE_SPEECH</text>
    <text x="950" y="388" text-anchor="middle" font-size="12" fill="#047857">• Ghi âm vào Audio RingBuffer</text>
    <text x="950" y="410" text-anchor="middle" font-size="12" fill="#047857">• Reset silence_frames = 0</text>
    <text x="950" y="425" text-anchor="middle" font-size="11" fill="#059669">• Phát sự kiện SPEECH_START tới Client</text>

    <!-- Loop back from Speech Active to Read Next Frame -->
    <path d="M 950 435 L 950 470 L 1090 470 L 1090 125 L 690 125" stroke="#10b981" stroke-width="1.8" stroke-dasharray="5,5" marker-end="url(#arrowGreen)"/>
    <text x="1020" y="460" font-size="11" font-weight="600" fill="#059669">Tiếp tục đọc frame tiếp theo</text>

    <!-- Branch NO: Downwards (Silence Detection) -->
    <path d="M 550 405 L 550 455" stroke="#ef4444" stroke-width="2" marker-end="url(#arrowRed)"/>
    <text x="560" y="430" font-size="13" font-weight="700" fill="#ef4444">SAI (Yên lặng)</text>

    <!-- 5. Decision: Trạng thái hiện tại có đang ACTIVE_SPEECH? -->
    <polygon points="550,455 690,510 550,565 410,510" fill="url(#gradDecision)" stroke="#d97706" stroke-width="2" filter="url(#shadow)"/>
    <text x="550" y="505" text-anchor="middle" font-size="13" font-weight="700" fill="#92400e">Đang trong lượt nói?</text>
    <text x="550" y="525" text-anchor="middle" font-size="12" fill="#b45309">(State == ACTIVE)?</text>

    <!-- Branch NO of 5: Left (Idle Silence / Noise Floor) -->
    <path d="M 410 510 L 260 510" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>
    <text x="320" y="500" font-size="13" font-weight="700" fill="#64748b">CHƯA NÓI</text>

    <rect x="20" y="480" width="240" height="60" rx="8" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" filter="url(#shadow)"/>
    <text x="140" y="505" text-anchor="middle" font-size="13" font-weight="600" fill="#334155">Bỏ qua Frame (Nhiễu nền)</text>
    <text x="140" y="525" text-anchor="middle" font-size="11" fill="#64748b">Cập nhật ngưỡng năng lượng nền</text>

    <!-- Loop back from Noise drop to next frame -->
    <path d="M 140 480 L 140 125 L 410 125" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,5" marker-end="url(#arrow)"/>

    <!-- Branch YES of 5: Downwards (Counting Silence) -->
    <path d="M 550 565 L 550 600" stroke="#10b981" stroke-width="2" marker-end="url(#arrowGreen)"/>
    <text x="560" y="585" font-size="13" font-weight="700" fill="#10b981">ĐANG NÓI (Khoảng lặng)</text>

    <!-- 6. Increment Silence Counter -->
    <rect x="420" y="600" width="260" height="45" rx="6" fill="url(#gradProcess)" stroke="#cbd5e1" stroke-width="1.5" filter="url(#shadow)"/>
    <text x="550" y="628" text-anchor="middle" font-size="13" font-weight="600" fill="#1e293b">silence_frames += 1 (tăng thêm 20ms)</text>

    <!-- Arrow 6 -> 7 -->
    <path d="M 550 645 L 550 675" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

    <!-- 7. Decision: Cutoff Reached? (silence_frames >= 25 frames == 500ms) -->
    <polygon points="550,675 700,720 550,765 400,720" fill="url(#gradDecision)" stroke="#d97706" stroke-width="2" filter="url(#shadow)"/>
    <text x="550" y="715" text-anchor="middle" font-size="13" font-weight="700" fill="#92400e">Khoảng lặng &gt;= 500ms?</text>
    <text x="550" y="733" text-anchor="middle" font-size="11" fill="#b45309">(silence_frames &gt;= 25)</text>

    <!-- Branch NO of 7: Left loop back to receive next frame -->
    <path d="M 400 720 L 320 720 L 320 140 L 410 140" stroke="#f59e0b" stroke-width="2" stroke-dasharray="4,4" marker-end="url(#arrow)"/>
    <text x="330" y="710" font-size="12" font-weight="700" fill="#d97706">Chưa đủ 500ms</text>

    <!-- Branch YES of 7: Right to Finalize Cutoff -->
    <path d="M 700 720 L 820 720" stroke="#10b981" stroke-width="2.5" marker-end="url(#arrowGreen)"/>
    <text x="735" y="710" font-size="13" font-weight="700" fill="#10b981">ĐỦ 500ms (KẾT THÚC CÂU)</text>

    <!-- 8. Action Finalize & Dispatch -->
    <rect x="820" y="685" width="250" height="70" rx="8" fill="url(#gradFinish)" filter="url(#shadow)"/>
    <text x="945" y="712" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">KÍCH HOẠT SILENCE_CUTOFF</text>
    <text x="945" y="732" text-anchor="middle" font-size="12" fill="#d1fae5">• Đóng gói Audio Turn (WAV 16kHz)</text>
    <text x="945" y="748" text-anchor="middle" font-size="11" fill="#ecfdf5">• Đẩy vào hàng đợi STT Worker (Whisper)</text>

  </svg>
</div>
</body>
</html>"""
    render_html_to_png(html, os.path.join(OUT_DIR, "hinh_4_2_luu_do_thuat_toan_webrtc_vad.png"), width=1200, height=900)

# ==============================================================================
# HÌNH 4.3: Cơ chế khóa tương hỗ Dual-Mic Mutex trong phiên dịch song phương
# ==============================================================================
def generate_hinh_4_3():
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 1200px;
    height: 800px;
  }
  .container {
    width: 1160px;
    height: 760px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  }
  .title {
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 20px;
    text-transform: uppercase;
  }
</style>
</head>
<body>
<div class="container">
  <div class="title">Cơ chế khóa tương hỗ chống xung đột âm thanh (Dual-Mic Mutex Lock Architecture)</div>
  <svg viewBox="0 0 1100 680" style="width:100%; height:670px;">
    <defs>
      <linearGradient id="userABg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#eff6ff"/>
        <stop offset="100%" stop-color="#dbeafe"/>
      </linearGradient>
      <linearGradient id="userBBg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#fff1f2"/>
        <stop offset="100%" stop-color="#ffe4e6"/>
      </linearGradient>
      <linearGradient id="actorBg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#f8fafc"/>
        <stop offset="100%" stop-color="#e2e8f0"/>
      </linearGradient>
      <linearGradient id="lockGranted" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#10b981"/>
        <stop offset="100%" stop-color="#059669"/>
      </linearGradient>
      <linearGradient id="lockDenied" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#ef4444"/>
        <stop offset="100%" stop-color="#dc2626"/>
      </linearGradient>
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
        <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.1"/>
      </filter>
      <marker id="arrBlue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#2563eb"/>
      </marker>
      <marker id="arrRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#ef4444"/>
      </marker>
      <marker id="arrGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#10b981"/>
      </marker>
    </defs>

    <!-- LEFT: User A (Vietnamese Speaker) -->
    <rect x="30" y="40" width="270" height="580" rx="10" fill="url(#userABg)" stroke="#3b82f6" stroke-width="2" filter="url(#shadow)"/>
    <text x="165" y="75" text-anchor="middle" font-size="16" font-weight="700" fill="#1d4ed8">NGƯỜI DÙNG A (MIC A)</text>
    <text x="165" y="95" text-anchor="middle" font-size="12" fill="#2563eb">Ngôn ngữ: Tiếng Việt (vi-VN)</text>

    <rect x="50" y="130" width="230" height="90" rx="8" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5"/>
    <text x="165" y="160" text-anchor="middle" font-size="13" font-weight="600" fill="#1e293b">1. Nhấn nút Mic A (Nói)</text>
    <text x="165" y="180" text-anchor="middle" font-size="11" fill="#475569">Gửi START_SPEAKING(vi)</text>
    <text x="165" y="200" text-anchor="middle" font-size="11" fill="#2563eb">Kèm Audio Stream PCM</text>

    <rect x="50" y="270" width="230" height="90" rx="8" fill="#ecfdf5" stroke="#10b981" stroke-width="1.5"/>
    <text x="165" y="300" text-anchor="middle" font-size="13" font-weight="700" fill="#065f46">3. Nhận LOCK_ACQUIRED</text>
    <text x="165" y="322" text-anchor="middle" font-size="11" fill="#047857">UI: Sóng âm hoạt động (Xanh)</text>
    <text x="165" y="340" text-anchor="middle" font-size="11" fill="#047857">Toàn quyền truyền giọng nói</text>

    <rect x="50" y="470" width="230" height="90" rx="8" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5"/>
    <text x="165" y="500" text-anchor="middle" font-size="13" font-weight="600" fill="#1e293b">6. Dứt câu &gt; 500ms</text>
    <text x="165" y="522" text-anchor="middle" font-size="11" fill="#475569">Nhận kết quả dịch tiếng Anh</text>
    <text x="165" y="540" text-anchor="middle" font-size="11" fill="#10b981">Phát âm thanh câu dịch</text>

    <!-- CENTER: SessionActor (Mutex Coordinator) -->
    <rect x="360" y="40" width="380" height="580" rx="10" fill="url(#actorBg)" stroke="#64748b" stroke-width="2" filter="url(#shadow)"/>
    <text x="550" y="75" text-anchor="middle" font-size="16" font-weight="700" fill="#0f172a">SESSION ACTOR (COORDINATOR)</text>
    <text x="550" y="95" text-anchor="middle" font-size="12" fill="#475569">Bộ điều phối phiên dịch song ngữ thời gian thực</text>

    <!-- Mutex State Box -->
    <rect x="390" y="120" width="320" height="110" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
    <text x="550" y="145" text-anchor="middle" font-size="13" font-weight="700" fill="#334155">BỘ ĐIỀU KHIỂN TRẠNG THÁI KHÓA (MUTEX)</text>
    <rect x="410" y="160" width="280" height="55" rx="6" fill="url(#lockGranted)"/>
    <text x="550" y="185" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">LOCK OWNER: USER_A</text>
    <text x="550" y="202" text-anchor="middle" font-size="11" fill="#ecfdf5">active_channel = 'vi' | locked = True</text>

    <!-- Conflict Resolution Logic -->
    <rect x="390" y="260" width="320" height="170" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
    <text x="550" y="285" text-anchor="middle" font-size="13" font-weight="700" fill="#334155">CƠ CHẾ GIẢI QUYẾT XUNG ĐỘT</text>
    <text x="410" y="315" font-size="12" fill="#1e293b">• Kiểm tra: <tspan font-weight="700" fill="#dc2626">is_locked() == True</tspan></text>
    <text x="410" y="338" font-size="12" fill="#1e293b">• Yêu cầu từ B bị từ chối tức thì (Zero-Latency)</text>
    <text x="410" y="360" font-size="12" fill="#1e293b">• Trả về gói tin: <tspan font-weight="700" fill="#dc2626">MUTEX_REJECTED</tspan></text>
    <text x="410" y="382" font-size="12" fill="#1e293b">• Lý do: <tspan font-style="italic">"Kênh đối phương đang phát âm"</tspan></text>
    <text x="410" y="405" font-size="11" fill="#64748b">• Chống nhiễu chéo âm thanh (Acoustic Echo)</text>

    <!-- Release State Box -->
    <rect x="390" y="460" width="320" height="120" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
    <text x="550" y="485" text-anchor="middle" font-size="13" font-weight="700" fill="#334155">GIẢI PHÓNG KHÓA (MUTEX_RELEASE)</text>
    <text x="410" y="515" font-size="12" fill="#1e293b">• Kích hoạt sau khi TTS phát hoàn tất</text>
    <text x="410" y="538" font-size="12" fill="#1e293b">• active_channel = None | locked = False</text>
    <text x="410" y="560" font-size="12" fill="#10b981" font-weight="700">• Broadcast CHANNEL_AVAILABLE tới 2 Mic</text>

    <!-- RIGHT: User B (English Speaker) -->
    <rect x="800" y="40" width="270" height="580" rx="10" fill="url(#userBBg)" stroke="#f43f5e" stroke-width="2" filter="url(#shadow)"/>
    <text x="935" y="75" text-anchor="middle" font-size="16" font-weight="700" fill="#e11d48">NGƯỜI DÙNG B (MIC B)</text>
    <text x="935" y="95" text-anchor="middle" font-size="12" fill="#f43f5e">Ngôn ngữ: Tiếng Anh (en-US)</text>

    <rect x="820" y="160" width="230" height="90" rx="8" fill="#ffffff" stroke="#fda4af" stroke-width="1.5"/>
    <text x="935" y="190" text-anchor="middle" font-size="13" font-weight="600" fill="#1e293b">2. Nhấn nói cùng lúc</text>
    <text x="935" y="210" text-anchor="middle" font-size="11" fill="#475569">Gửi START_SPEAKING(en)</text>
    <text x="935" y="230" text-anchor="middle" font-size="11" fill="#e11d48">Cố gắng chiếm kênh</text>

    <rect x="820" y="300" width="230" height="100" rx="8" fill="#fff1f2" stroke="#e11d48" stroke-width="2"/>
    <text x="935" y="328" text-anchor="middle" font-size="13" font-weight="700" fill="#9f1239">4. Nhận MUTEX_REJECTED</text>
    <text x="935" y="350" text-anchor="middle" font-size="11" fill="#e11d48">• Rung phản hồi (Haptic Warning)</text>
    <text x="935" y="370" text-anchor="middle" font-size="11" fill="#e11d48">• UI: Nút Mic B mờ/vàng (Chờ)</text>
    <text x="935" y="388" text-anchor="middle" font-size="11" fill="#9f1239">• Thông báo: "Người đối diện đang nói"</text>

    <rect x="820" y="470" width="230" height="90" rx="8" fill="#f0fdf4" stroke="#86efac" stroke-width="1.5"/>
    <text x="935" y="500" text-anchor="middle" font-size="13" font-weight="600" fill="#1e293b">7. Kênh rảnh trở lại</text>
    <text x="935" y="522" text-anchor="middle" font-size="11" fill="#15803d">Nhận CHANNEL_AVAILABLE</text>
    <text x="935" y="540" text-anchor="middle" font-size="11" fill="#15803d">Nút Mic B sẵn sàng nhận lệnh nói</text>

    <!-- ARROWS CONNECTING -->
    <!-- 1. A request to Actor -->
    <path d="M 280 175 L 390 175" stroke="#2563eb" stroke-width="2" marker-end="url(#arrBlue)"/>
    <!-- 2. B request to Actor -->
    <path d="M 820 205 L 710 205" stroke="#e11d48" stroke-width="2" marker-end="url(#arrRed)"/>
    <!-- 3. Actor grant A -->
    <path d="M 390 315 L 280 315" stroke="#10b981" stroke-width="2" marker-end="url(#arrGreen)"/>
    <!-- 4. Actor reject B -->
    <path d="M 710 350 L 820 350" stroke="#ef4444" stroke-width="2.5" marker-end="url(#arrRed)"/>
    <!-- 5. Release to both -->
    <path d="M 390 520 L 280 520" stroke="#64748b" stroke-width="1.5" stroke-dasharray="4,4" marker-end="url(#arrBlue)"/>
    <path d="M 710 520 L 820 520" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4,4" marker-end="url(#arrGreen)"/>
  </svg>
</div>
</body>
</html>"""
    render_html_to_png(html, os.path.join(OUT_DIR, "hinh_4_3_co_che_khoa_mutex_dual_mic.png"), width=1200, height=800)

# ==============================================================================
# HÌNH 4.4: Quy trình kiểm chuẩn chất lượng dịch thuật MQM Human-in-the-Loop
# ==============================================================================
def generate_hinh_4_4():
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 1200px;
    height: 750px;
  }
  .container {
    width: 1160px;
    height: 710px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  }
  .title {
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 20px;
    text-transform: uppercase;
  }
</style>
</head>
<body>
<div class="container">
  <div class="title">Quy trình thẩm định và kiểm chuẩn chất lượng dịch thuật MQM (Human-in-the-Loop)</div>
  <svg viewBox="0 0 1100 620" style="width:100%; height:610px;">
    <defs>
      <linearGradient id="stepGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#f8fafc"/>
        <stop offset="100%" stop-color="#f1f5f9"/>
      </linearGradient>
      <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#3b82f6"/>
        <stop offset="100%" stop-color="#1d4ed8"/>
      </linearGradient>
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
        <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.1"/>
      </filter>
      <marker id="arr" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#475569"/>
      </marker>
      <marker id="arrGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#10b981"/>
      </marker>
      <marker id="arrRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#ef4444"/>
      </marker>
    </defs>

    <!-- STEP 1: Ingestion -->
    <rect x="20" y="50" width="210" height="200" rx="8" fill="url(#stepGrad)" stroke="#cbd5e1" stroke-width="2" filter="url(#shadow)"/>
    <rect x="20" y="50" width="210" height="40" rx="8" fill="#2563eb"/>
    <text x="125" y="75" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">1. TIẾP NHẬN BẢN GHI</text>
    <text x="125" y="115" text-anchor="middle" font-size="12" font-weight="600" fill="#1e293b">Nguồn dữ liệu:</text>
    <text x="125" y="140" text-anchor="middle" font-size="11" fill="#475569">• Người dùng gắn cờ (Flag)</text>
    <text x="125" y="162" text-anchor="middle" font-size="11" fill="#475569">• STT Confidence &lt; 0.75</text>
    <text x="125" y="184" text-anchor="middle" font-size="11" fill="#475569">• Mẫu ngẫu nhiên Fresh500</text>
    <text x="125" y="210" text-anchor="middle" font-size="11" font-style="italic" fill="#2563eb">Đẩy vào QA Ingestion Queue</text>

    <!-- Arrow 1 -> 2 -->
    <path d="M 230 150 L 290 150" stroke="#475569" stroke-width="2" marker-end="url(#arr)"/>

    <!-- STEP 2: Taxonomy Assessment -->
    <rect x="290" y="30" width="260" height="240" rx="8" fill="url(#stepGrad)" stroke="#0284c7" stroke-width="2" filter="url(#shadow)"/>
    <rect x="290" y="30" width="260" height="40" rx="8" fill="#0284c7"/>
    <text x="420" y="55" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">2. PHÂN LOẠI LỖI MQM</text>
    <text x="310" y="95" font-size="12" font-weight="700" fill="#0369a1">• Accuracy (Độ chính xác):</text>
    <text x="325" y="115" font-size="11" fill="#334155">- Mistranslation, Omission, Addition</text>
    <text x="310" y="140" font-size="12" font-weight="700" fill="#0369a1">• Fluency (Độ lưu loát):</text>
    <text x="325" y="160" font-size="11" fill="#334155">- Grammar, Spelling, Typography</text>
    <text x="310" y="185" font-size="12" font-weight="700" fill="#0369a1">• Terminology (Thuật ngữ):</text>
    <text x="325" y="205" font-size="11" fill="#334155">- Inconsistent with Glossary</text>
    <text x="310" y="230" font-size="12" font-weight="700" fill="#0369a1">• Style & Locale Convention</text>

    <!-- Arrow 2 -> 3 -->
    <path d="M 550 150 L 610 150" stroke="#475569" stroke-width="2" marker-end="url(#arr)"/>

    <!-- STEP 3: Scoring & Penalty calculation -->
    <rect x="610" y="30" width="230" height="240" rx="8" fill="url(#stepGrad)" stroke="#d97706" stroke-width="2" filter="url(#shadow)"/>
    <rect x="610" y="30" width="230" height="40" rx="8" fill="#d97706"/>
    <text x="725" y="55" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">3. TRỪ ĐIỂM TRỌNG SỐ</text>
    <text x="630" y="95" font-size="12" font-weight="700" fill="#b45309">Thang điểm phạt MQM:</text>
    <text x="630" y="125" font-size="11" fill="#1e293b">• <tspan font-weight="700">Minor (-1 điểm):</tspan> Lỗi nhỏ</text>
    <text x="630" y="150" font-size="11" fill="#1e293b">• <tspan font-weight="700">Major (-5 điểm):</tspan> Sai lệch nghĩa</text>
    <text x="630" y="175" font-size="11" fill="#1e293b">• <tspan font-weight="700" fill="#dc2626">Critical (-10 điểm):</tspan> Độc hại / Nguy hại</text>
    <rect x="625" y="195" width="200" height="60" rx="6" fill="#fef3c7" stroke="#f59e0b" stroke-width="1"/>
    <text x="725" y="220" text-anchor="middle" font-size="12" font-weight="700" fill="#92400e">MQM_Score = 100 - Sum(Phạt)</text>
    <text x="725" y="240" text-anchor="middle" font-size="10" fill="#b45309">Ngưỡng đạt tiêu chuẩn: &gt;= 85 điểm</text>

    <!-- Arrow 3 -> Decision -->
    <path d="M 840 150 L 910 150" stroke="#475569" stroke-width="2" marker-end="url(#arr)"/>

    <!-- STEP 4: Decision (Score >= 85?) -->
    <polygon points="990,100 1090,150 990,200 890,150" fill="#fef3c7" stroke="#d97706" stroke-width="2" filter="url(#shadow)"/>
    <text x="990" y="145" text-anchor="middle" font-size="13" font-weight="700" fill="#92400e">Điểm &gt;= 85?</text>
    <text x="990" y="165" text-anchor="middle" font-size="11" fill="#b45309">(Đạt chuẩn)</text>

    <!-- Branch YES: To Bottom Right (Approved Dataset) -->
    <path d="M 990 200 L 990 350" stroke="#10b981" stroke-width="2.5" marker-end="url(#arrGreen)"/>
    <text x="1005" y="260" font-size="12" font-weight="700" fill="#10b981">ĐẠT (YES)</text>

    <rect x="850" y="350" width="240" height="150" rx="8" fill="#ecfdf5" stroke="#10b981" stroke-width="2" filter="url(#shadow)"/>
    <rect x="850" y="350" width="240" height="35" rx="8" fill="#059669"/>
    <text x="970" y="373" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">PHÊ DUYỆT (APPROVED)</text>
    <text x="970" y="410" text-anchor="middle" font-size="12" fill="#047857">• Nạp vào Gold Standard TM</text>
    <text x="970" y="435" text-anchor="middle" font-size="12" fill="#047857">• Đánh dấu Gold Dataset</text>
    <text x="970" y="460" text-anchor="middle" font-size="12" fill="#047857">• Đưa vào kho dữ liệu huấn luyện LoRA</text>
    <text x="970" y="485" text-anchor="middle" font-size="11" font-weight="600" fill="#065f46">Trạng thái: READY_FOR_TRAIN</text>

    <!-- Branch NO: To Bottom Center (Post-Editing) -->
    <path d="M 990 100 L 990 40 L 450 40 L 450 350" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5" marker-end="url(#arrRed)"/>
    <text x="750" y="30" font-size="12" font-weight="700" fill="#ef4444">KHÔNG ĐẠT (&lt; 85 Điểm) -&gt; CHUYỂN HẬU BIÊN TẬP</text>

    <!-- STEP 5: Human Post-Editing -->
    <rect x="330" y="350" width="260" height="150" rx="8" fill="#fff1f2" stroke="#e11d48" stroke-width="2" filter="url(#shadow)"/>
    <rect x="330" y="350" width="260" height="35" rx="8" fill="#e11d48"/>
    <text x="460" y="373" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">HẬU BIÊN TẬP (POST-EDITING)</text>
    <text x="460" y="410" text-anchor="middle" font-size="12" fill="#9f1239">• Chuyên viên ngôn ngữ chỉnh sửa bản dịch</text>
    <text x="460" y="435" text-anchor="middle" font-size="12" fill="#9f1239">• Bổ sung thuật ngữ thiếu vào Glossary</text>
    <text x="460" y="460" text-anchor="middle" font-size="12" fill="#9f1239">• Lưu vết thay đổi: Target_PostEdited</text>
    <text x="460" y="485" text-anchor="middle" font-size="11" font-weight="600" fill="#e11d48">Tái thẩm định MQM sau chỉnh sửa</text>

    <!-- Arrow Post-Editing -> Approved -->
    <path d="M 590 425 L 850 425" stroke="#10b981" stroke-width="2.5" marker-end="url(#arrGreen)"/>
    <text x="700" y="415" text-anchor="middle" font-size="12" font-weight="700" fill="#10b981">Đã sửa đạt chuẩn &gt;= 85</text>

    <!-- Bottom summary banner -->
    <rect x="20" y="530" width="1060" height="60" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="550" y="555" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">VÒNG LẶP ĐÓNG BĂNG VÀ XUẤT BẢN DATASET (FREEZE DATASET VÒNG ĐỜI MLOPS)</text>
    <text x="550" y="575" text-anchor="middle" font-size="12" fill="#64748b">Dữ liệu được kiểm duyệt đạt chuẩn MQM sẽ được đóng gói dưới định dạng JSONL/Parquet, tạo bệ phóng tinh chỉnh LoRA Adapter định kỳ</text>
  </svg>
</div>
</body>
</html>"""
    render_html_to_png(html, os.path.join(OUT_DIR, "hinh_4_4_quy_trinh_kiem_chuan_mqm_qa.png"), width=1200, height=750)

# ==============================================================================
# HÌNH 4.5: Kiến trúc nạp nóng LoRA Adapter và cơ chế điều hướng Canary Routing
# ==============================================================================
def generate_hinh_4_5():
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 1200px;
    height: 820px;
  }
  .container {
    width: 1160px;
    height: 780px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  }
  .title {
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 20px;
    text-transform: uppercase;
  }
</style>
</head>
<body>
<div class="container">
  <div class="title">Kiến trúc nạp nóng LoRA Adapter & Cơ chế điều hướng thử nghiệm Canary Routing</div>
  <svg viewBox="0 0 1100 700" style="width:100%; height:690px;">
    <defs>
      <linearGradient id="gradGate" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#3b82f6"/>
        <stop offset="100%" stop-color="#1d4ed8"/>
      </linearGradient>
      <linearGradient id="gradStable" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#ecfdf5"/>
        <stop offset="100%" stop-color="#d1fae5"/>
      </linearGradient>
      <linearGradient id="gradCanary" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#fffbeb"/>
        <stop offset="100%" stop-color="#fef3c7"/>
      </linearGradient>
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
        <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.1"/>
      </filter>
      <marker id="arr" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#475569"/>
      </marker>
      <marker id="arrGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#10b981"/>
      </marker>
      <marker id="arrAmber" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#f59e0b"/>
      </marker>
    </defs>

    <!-- Top: Client Traffic -->
    <rect x="420" y="20" width="260" height="60" rx="8" fill="#1e293b" filter="url(#shadow)"/>
    <text x="550" y="47" text-anchor="middle" font-size="15" font-weight="700" fill="#ffffff">LƯU LƯỢNG YÊU CẦU DỊCH</text>
    <text x="550" y="67" text-anchor="middle" font-size="12" fill="#94a3b8">100% Traffic từ Mobile App & REST API</text>

    <!-- Arrow Traffic -> Canary Router -->
    <path d="M 550 80 L 550 120" stroke="#475569" stroke-width="2.5" marker-end="url(#arr)"/>

    <!-- CANARY ROUTER / GATEWAY -->
    <rect x="360" y="120" width="380" height="90" rx="10" fill="url(#gradGate)" filter="url(#shadow)"/>
    <text x="550" y="152" text-anchor="middle" font-size="16" font-weight="700" fill="#ffffff">CANARY ROUTER & TRAFFIC SPLITTER</text>
    <text x="550" y="175" text-anchor="middle" font-size="12" fill="#bfdbfe">Điều hướng lưu lượng dựa trên trọng số cấu hình động</text>
    <text x="550" y="195" text-anchor="middle" font-size="11" fill="#93c5fd">Trọng số mặc định: 90% Stable | 10% Canary Staging</text>

    <!-- Branch Left: Stable 90% -->
    <path d="M 440 210 L 440 270 L 250 270 L 250 310" stroke="#10b981" stroke-width="3" marker-end="url(#arrGreen)"/>
    <text x="310" y="260" font-size="14" font-weight="700" fill="#10b981">90% Lưu lượng (Stable)</text>

    <!-- Branch Right: Canary 10% -->
    <path d="M 660 210 L 660 270 L 850 270 L 850 310" stroke="#f59e0b" stroke-width="3" marker-end="url(#arrAmber)"/>
    <text x="700" y="260" font-size="14" font-weight="700" fill="#d97706">10% Lưu lượng (Canary)</text>

    <!-- LEFT CONTAINER: STABLE WORKER POOL -->
    <rect x="50" y="310" width="400" height="230" rx="10" fill="url(#gradStable)" stroke="#10b981" stroke-width="2" filter="url(#shadow)"/>
    <rect x="50" y="310" width="400" height="40" rx="10" fill="#059669"/>
    <text x="250" y="335" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">STABLE TRANSLATION WORKER (V1.0)</text>

    <rect x="70" y="365" width="360" height="55" rx="6" fill="#ffffff" stroke="#a7f3d0" stroke-width="1.5"/>
    <text x="250" y="390" text-anchor="middle" font-size="13" font-weight="700" fill="#065f46">Mô hình gốc NLLB-200 1.3B Base</text>
    <text x="250" y="408" text-anchor="middle" font-size="11" fill="#047857">CTranslate2 INT8 Caching Engine</text>

    <rect x="70" y="430" width="360" height="55" rx="6" fill="#ffffff" stroke="#a7f3d0" stroke-width="1.5"/>
    <text x="250" y="455" text-anchor="middle" font-size="13" font-weight="700" fill="#065f46">LoRA Adapter v1.0 Production</text>
    <text x="250" y="473" text-anchor="middle" font-size="11" fill="#047857">Trọng số thích ứng hiện hành (Độ trễ trung bình: 584ms)</text>

    <text x="250" y="520" text-anchor="middle" font-size="12" font-weight="600" fill="#047857">Độ ổn định: 99.98% | Error Rate: 0.02%</text>

    <!-- RIGHT CONTAINER: CANARY WORKER POOL -->
    <rect x="650" y="310" width="400" height="230" rx="10" fill="url(#gradCanary)" stroke="#f59e0b" stroke-width="2" filter="url(#shadow)"/>
    <rect x="650" y="310" width="400" height="40" rx="10" fill="#d97706"/>
    <text x="850" y="335" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">CANARY STAGING WORKER (V1.1-CANDIDATE)</text>

    <rect x="670" y="365" width="360" height="55" rx="6" fill="#ffffff" stroke="#fde68a" stroke-width="1.5"/>
    <text x="850" y="390" text-anchor="middle" font-size="13" font-weight="700" fill="#92400e">Mô hình gốc NLLB-200 1.3B Base</text>
    <text x="850" y="408" text-anchor="middle" font-size="11" fill="#b45309">Chia sẻ bộ nhớ trọng số cơ sở (Zero Copy)</text>

    <rect x="670" y="430" width="360" height="55" rx="6" fill="#ffffff" stroke="#fde68a" stroke-width="1.5"/>
    <text x="850" y="455" text-anchor="middle" font-size="13" font-weight="700" fill="#92400e">LoRA Adapter v1.1 Hot-Swapped</text>
    <text x="850" y="473" text-anchor="middle" font-size="11" fill="#b45309">Adapter nạp nóng động trong RAM (PEFT Safetensors)</text>

    <text x="850" y="520" text-anchor="middle" font-size="12" font-weight="600" fill="#b45309">Thuật toán nạp không gián đoạn (Zero-Downtime Hot Swap)</text>

    <!-- BOTTOM: Telemetry & Automated Rollback / Promotion Controller -->
    <rect x="50" y="570" width="1000" height="110" rx="10" fill="#f8fafc" stroke="#64748b" stroke-width="2" filter="url(#shadow)"/>
    <text x="550" y="600" text-anchor="middle" font-size="15" font-weight="700" fill="#0f172a">HỆ THỐNG GIÁM SÁT TELEMETRY & ĐIỀU PHỐI VÒNG ĐỜI MÔ HÌNH TỰ ĐỘNG</text>

    <path d="M 250 540 L 250 570" stroke="#10b981" stroke-width="2" marker-end="url(#arrGreen)"/>
    <path d="M 850 540 L 850 570" stroke="#f59e0b" stroke-width="2" marker-end="url(#arrAmber)"/>

    <text x="250" y="630" text-anchor="middle" font-size="12" fill="#334155"><tspan font-weight="700">Kịch bản 1: Thành công</tspan> (chrF++ tăng &gt; 1.5 điểm, P95 &lt; 1000ms)</text>
    <text x="250" y="650" text-anchor="middle" font-size="11" fill="#059669">Nâng cấp tự động Canary lên 100% (Promote to Production)</text>

    <text x="850" y="630" text-anchor="middle" font-size="12" fill="#334155"><tspan font-weight="700">Kịch bản 2: Bất thường</tspan> (Lỗi tăng &gt; 1% hoặc sụt giảm chrF++)</text>
    <text x="850" y="650" text-anchor="middle" font-size="11" fill="#dc2626">Tự động hủy lưu lượng Canary về 0% (Instant Rollback)</text>
  </svg>
</div>
</body>
</html>"""
    render_html_to_png(html, os.path.join(OUT_DIR, "hinh_4_5_kien_truc_lora_canary_routing.png"), width=1200, height=820)

# ==============================================================================
# HÌNH 4.6: Biểu đồ so sánh độ trễ đường ống dịch Baseline vs Optimized (Fresh500)
# ==============================================================================
def generate_hinh_4_6():
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 1200px;
    height: 750px;
  }
  .container {
    width: 1160px;
    height: 710px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  }
  .title {
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 8px;
    text-transform: uppercase;
  }
  .subtitle {
    text-align: center;
    font-size: 13px;
    color: #64748b;
    margin-bottom: 24px;
  }
</style>
</head>
<body>
<div class="container">
  <div class="title">Biểu đồ so sánh độ trễ xử lý đường ống dịch trước và sau tối ưu</div>
  <div class="subtitle">Thực nghiệm trên tập ngữ liệu Fresh500 (500 mẫu hội thoại tự nhiên, 20 lĩnh vực chuyên sâu)</div>
  <svg viewBox="0 0 1100 580" style="width:100%; height:580px;">
    <!-- Grid lines -->
    <line x1="120" y1="460" x2="1050" y2="460" stroke="#cbd5e1" stroke-width="1.5"/>
    <line x1="120" y1="380" x2="1050" y2="380" stroke="#f1f5f9" stroke-width="1"/>
    <line x1="120" y1="300" x2="1050" y2="300" stroke="#f1f5f9" stroke-width="1"/>
    <line x1="120" y1="220" x2="1050" y2="220" stroke="#f1f5f9" stroke-width="1"/>
    <line x1="120" y1="140" x2="1050" y2="140" stroke="#f1f5f9" stroke-width="1"/>
    <line x1="120" y1="60" x2="1050" y2="60" stroke="#f1f5f9" stroke-width="1"/>

    <!-- Y-axis labels (ms) -->
    <text x="100" y="465" text-anchor="end" font-size="12" fill="#64748b">0 ms</text>
    <text x="100" y="385" text-anchor="end" font-size="12" fill="#64748b">500 ms</text>
    <text x="100" y="305" text-anchor="end" font-size="12" fill="#64748b">1,000 ms (SLA)</text>
    <text x="100" y="225" text-anchor="end" font-size="12" fill="#64748b">1,500 ms</text>
    <text x="100" y="145" text-anchor="end" font-size="12" fill="#64748b">2,000 ms</text>
    <text x="100" y="65" text-anchor="end" font-size="12" fill="#64748b">2,500 ms</text>

    <!-- SLA Target Line 1000ms -->
    <line x1="120" y1="300" x2="1050" y2="300" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="6,4"/>
    <text x="1040" y="292" text-anchor="end" font-size="11" font-weight="700" fill="#ef4444">Ngưỡng SLA Đàm thoại Thời gian thực &lt; 1,000 ms</text>

    <!-- GROUP 1: STT Whisper Latency -->
    <!-- Scale: 460 is 0ms, 60 is 2500ms => 400px for 2500ms => 0.16 px/ms -->
    <!-- Base 720ms => 720 * 0.16 = 115.2px. y = 460 - 115.2 = 344.8 -->
    <rect x="180" y="345" width="45" height="115" rx="4" fill="#94a3b8"/>
    <text x="202" y="335" text-anchor="middle" font-size="12" font-weight="700" fill="#475569">720 ms</text>

    <!-- Opt 245ms => 245 * 0.16 = 39.2px. y = 460 - 39.2 = 420.8 -->
    <rect x="235" y="421" width="45" height="39" rx="4" fill="#3b82f6"/>
    <text x="257" y="413" text-anchor="middle" font-size="12" font-weight="700" fill="#1d4ed8">245 ms</text>
    <text x="230" y="485" text-anchor="middle" font-size="13" font-weight="600" fill="#1e293b">STT (Whisper)</text>
    <text x="230" y="503" text-anchor="middle" font-size="11" font-weight="700" fill="#16a34a">Giảm 66.0%</text>

    <!-- GROUP 2: MT NLLB Latency -->
    <!-- Base 510ms => 510 * 0.16 = 81.6px. y = 460 - 81.6 = 378.4 -->
    <rect x="360" y="378" width="45" height="82" rx="4" fill="#94a3b8"/>
    <text x="382" y="370" text-anchor="middle" font-size="12" font-weight="700" fill="#475569">510 ms</text>

    <!-- Opt 182ms => 182 * 0.16 = 29.1px. y = 460 - 29.1 = 430.9 -->
    <rect x="415" y="431" width="45" height="29" rx="4" fill="#3b82f6"/>
    <text x="437" y="423" text-anchor="middle" font-size="12" font-weight="700" fill="#1d4ed8">182 ms</text>
    <text x="410" y="485" text-anchor="middle" font-size="13" font-weight="600" fill="#1e293b">MT (NLLB-200)</text>
    <text x="410" y="503" text-anchor="middle" font-size="11" font-weight="700" fill="#16a34a">Giảm 64.3%</text>

    <!-- GROUP 3: TTS Piper VITS Latency -->
    <!-- Base 299ms => 299 * 0.16 = 47.8px. y = 460 - 47.8 = 412.2 -->
    <rect x="540" y="412" width="45" height="48" rx="4" fill="#94a3b8"/>
    <text x="562" y="404" text-anchor="middle" font-size="12" font-weight="700" fill="#475569">299 ms</text>

    <!-- Opt 157ms => 157 * 0.16 = 25.1px. y = 460 - 25.1 = 434.9 -->
    <rect x="595" y="435" width="45" height="25" rx="4" fill="#3b82f6"/>
    <text x="617" y="427" text-anchor="middle" font-size="12" font-weight="700" fill="#1d4ed8">157 ms</text>
    <text x="590" y="485" text-anchor="middle" font-size="13" font-weight="600" fill="#1e293b">TTS (Piper VITS)</text>
    <text x="590" y="503" text-anchor="middle" font-size="11" font-weight="700" fill="#16a34a">Giảm 47.5%</text>

    <!-- GROUP 4: TOTAL MEAN LATENCY -->
    <!-- Base 1530ms => 1530 * 0.16 = 244.8px. y = 460 - 244.8 = 215.2 -->
    <rect x="720" y="215" width="55" height="245" rx="4" fill="#f87171"/>
    <text x="747" y="205" text-anchor="middle" font-size="13" font-weight="700" fill="#b91c1c">1,530 ms</text>

    <!-- Opt 584ms => 584 * 0.16 = 93.4px. y = 460 - 93.4 = 366.6 -->
    <rect x="785" y="367" width="55" height="93" rx="4" fill="#10b981"/>
    <text x="812" y="357" text-anchor="middle" font-size="13" font-weight="700" fill="#047857">584 ms</text>
    <text x="780" y="485" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">Tổng trễ trung bình</text>
    <text x="780" y="503" text-anchor="middle" font-size="12" font-weight="700" fill="#16a34a">Giảm 61.8% (-946ms)</text>

    <!-- GROUP 5: P95 LATENCY -->
    <!-- Base 2140ms => 2140 * 0.16 = 342.4px. y = 460 - 342.4 = 117.6 -->
    <rect x="910" y="118" width="55" height="342" rx="4" fill="#f87171"/>
    <text x="937" y="108" text-anchor="middle" font-size="13" font-weight="700" fill="#b91c1c">2,140 ms</text>

    <!-- Opt 964ms => 964 * 0.16 = 154.2px. y = 460 - 154.2 = 305.8 -->
    <rect x="975" y="306" width="55" height="154" rx="4" fill="#10b981"/>
    <text x="1002" y="296" text-anchor="middle" font-size="13" font-weight="700" fill="#047857">964 ms</text>
    <text x="970" y="485" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">Độ trễ P95</text>
    <text x="970" y="503" text-anchor="middle" font-size="12" font-weight="700" fill="#16a34a">Giảm 55.0% (&lt; 1s)</text>

    <!-- Legend -->
    <rect x="350" y="535" width="400" height="35" rx="6" fill="#f8fafc" stroke="#e2e8f0"/>
    <rect x="370" y="547" width="16" height="12" rx="2" fill="#94a3b8"/>
    <text x="395" y="558" font-size="12" fill="#475569">Ban đầu (Baseline)</text>
    <rect x="520" y="547" width="16" height="12" rx="2" fill="#10b981"/>
    <text x="545" y="558" font-size="12" fill="#047857">Sau tối ưu (Optimized)</text>
    <rect x="680" y="547" width="16" height="12" rx="2" fill="#3b82f6"/>
    <text x="705" y="558" font-size="12" fill="#1d4ed8">Từng công đoạn</text>
  </svg>
</div>
</body>
</html>"""
    render_html_to_png(html, os.path.join(OUT_DIR, "hinh_4_6_bieu_do_so_sanh_do_tre_fresh500.png"), width=1200, height=750)

# ==============================================================================
# HÌNH 4.7: Biểu đồ đường cong hội tụ (Loss Curve) trong quá trình huấn luyện LoRA
# ==============================================================================
def generate_hinh_4_7():
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 1200px;
    height: 750px;
  }
  .container {
    width: 1160px;
    height: 710px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  }
  .title {
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 8px;
    text-transform: uppercase;
  }
  .subtitle {
    text-align: center;
    font-size: 13px;
    color: #64748b;
    margin-bottom: 24px;
  }
</style>
</head>
<body>
<div class="container">
  <div class="title">Đường cong hội tụ (Loss Curve) và Điểm chrF++ khi huấn luyện LoRA Adapter</div>
  <div class="subtitle">Mô hình NLLB-200 1.3B, Rank=16, Alpha=32, LR=2e-4, Tập huấn luyện 3 Epochs (300 Steps)</div>
  <svg viewBox="0 0 1100 580" style="width:100%; height:580px;">
    <!-- Grid -->
    <line x1="100" y1="460" x2="1020" y2="460" stroke="#cbd5e1" stroke-width="1.5"/>
    <line x1="100" y1="360" x2="1020" y2="360" stroke="#f1f5f9" stroke-width="1"/>
    <line x1="100" y1="260" x2="1020" y2="260" stroke="#f1f5f9" stroke-width="1"/>
    <line x1="100" y1="160" x2="1020" y2="160" stroke="#f1f5f9" stroke-width="1"/>
    <line x1="100" y1="60" x2="1020" y2="60" stroke="#f1f5f9" stroke-width="1"/>

    <!-- Y-axis Left: Loss (0 to 4.0) -->
    <!-- 460 is 0.0, 60 is 4.0 => 400px / 4.0 = 100px per 1.0 Loss -->
    <text x="80" y="465" text-anchor="end" font-size="12" fill="#ef4444" font-weight="700">0.0</text>
    <text x="80" y="365" text-anchor="end" font-size="12" fill="#ef4444" font-weight="700">1.0</text>
    <text x="80" y="265" text-anchor="end" font-size="12" fill="#ef4444" font-weight="700">2.0</text>
    <text x="80" y="165" text-anchor="end" font-size="12" fill="#ef4444" font-weight="700">3.0</text>
    <text x="80" y="65" text-anchor="end" font-size="12" fill="#ef4444" font-weight="700">4.0</text>
    <text x="40" y="25" text-anchor="start" font-size="12" font-weight="700" fill="#dc2626">Cross-Entropy Loss (Trục trái)</text>

    <!-- Y-axis Right: chrF++ (55% to 70%) -->
    <text x="1040" y="465" text-anchor="start" font-size="12" fill="#2563eb" font-weight="700">55.0</text>
    <text x="1040" y="365" text-anchor="start" font-size="12" fill="#2563eb" font-weight="700">60.0</text>
    <text x="1040" y="265" text-anchor="start" font-size="12" fill="#2563eb" font-weight="700">65.0</text>
    <text x="1040" y="165" text-anchor="start" font-size="12" fill="#2563eb" font-weight="700">70.0</text>
    <text x="1040" y="25" text-anchor="end" font-size="12" font-weight="700" fill="#2563eb">Điểm chrF++ (Trục phải)</text>

    <!-- X-axis: Steps (0 to 300) -->
    <!-- 100 is Step 0, 1020 is Step 300 => 920px / 300 = 3.066 px/step -->
    <text x="100" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 0</text>
    <text x="253" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 50</text>
    <text x="406" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 100 (Epoch 1)</text>
    <text x="560" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 150</text>
    <text x="713" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 200 (Epoch 2)</text>
    <text x="866" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 250</text>
    <text x="1020" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 300 (Epoch 3)</text>

    <!-- Training Loss Curve (Red solid) -->
    <!-- Loss: 3.42 (y=118), 2.25 (y=235), 1.62 (y=298), 1.21 (y=339), 0.94 (y=366), 0.78 (y=382), 0.62 (y=398) -->
    <path d="M 100 118 Q 253 235 406 298 T 713 366 T 1020 398" fill="none" stroke="#ef4444" stroke-width="3.5"/>
    <circle cx="100" cy="118" r="4" fill="#ef4444"/>
    <circle cx="406" cy="298" r="4" fill="#ef4444"/>
    <circle cx="713" cy="366" r="4" fill="#ef4444"/>
    <circle cx="1020" cy="398" r="5" fill="#dc2626"/>
    <text x="1020" y="385" font-size="12" font-weight="700" fill="#dc2626">Loss = 0.62</text>

    <!-- Validation Loss Curve (Orange dashed) -->
    <path d="M 100 125 Q 253 245 406 305 T 713 375 T 1020 405" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="6,4"/>
    <circle cx="1020" cy="405" r="4" fill="#d97706"/>
    <text x="1020" y="425" font-size="11" font-weight="600" fill="#d97706">Val Loss = 0.71</text>

    <!-- chrF++ Curve (Blue solid) -->
    <!-- Scale: 55.0 is y=460, 70.0 is y=160 (15 pts = 300px => 20px per pt) -->
    <!-- 58.99 => y = 460 - (3.99*20) = 380.2 -->
    <!-- Step 100: 61.40 => y = 460 - (6.40*20) = 332 -->
    <!-- Step 200: 63.85 => y = 460 - (8.85*20) = 283 -->
    <!-- Step 300: 65.26 => y = 460 - (10.26*20) = 254.8 -->
    <path d="M 100 380 Q 253 355 406 332 T 713 283 T 1020 255" fill="none" stroke="#2563eb" stroke-width="3.5"/>
    <circle cx="100" cy="380" r="4" fill="#2563eb"/>
    <circle cx="406" cy="332" r="4" fill="#2563eb"/>
    <circle cx="713" cy="283" r="4" fill="#2563eb"/>
    <circle cx="1020" cy="255" r="5" fill="#1d4ed8"/>
    <text x="1020" y="245" font-size="12" font-weight="700" fill="#1d4ed8">chrF++ = 65.26 (+6.27)</text>

    <!-- Callout Box: Hardware & Footprint -->
    <rect x="140" y="80" width="320" height="95" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="155" y="105" font-size="13" font-weight="700" fill="#1e293b">THÔNG SỐ HUẤN LUYỆN LORA PEFT</text>
    <text x="155" y="125" font-size="12" fill="#334155">• VRAM sử dụng: <tspan font-weight="700" fill="#047857">5.48 GB</tspan> (Tối ưu cho GPU đơn)</text>
    <text x="155" y="145" font-size="12" fill="#334155">• Thời gian hội tụ 3 Epochs: <tspan font-weight="700" fill="#047857">31.92 giây</tspan></text>
    <text x="155" y="165" font-size="11" fill="#64748b">• Kích thước file adapter: 14.8 MB (Nạp tức thì)</text>

    <!-- Legend -->
    <rect x="350" y="525" width="400" height="35" rx="6" fill="#f8fafc" stroke="#e2e8f0"/>
    <line x1="370" y1="542" x2="395" y2="542" stroke="#ef4444" stroke-width="3"/>
    <text x="405" y="546" font-size="12" fill="#ef4444">Train Loss</text>
    <line x1="490" y1="542" x2="515" y2="542" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="4,3"/>
    <text x="525" y="546" font-size="12" fill="#f59e0b">Val Loss</text>
    <line x1="600" y1="542" x2="625" y2="542" stroke="#2563eb" stroke-width="3"/>
    <text x="635" y="546" font-size="12" fill="#2563eb">chrF++ Score</text>
  </svg>
</div>
</body>
</html>"""
    render_html_to_png(html, os.path.join(OUT_DIR, "hinh_4_7_bieu_do_loss_curve_lora_training.png"), width=1200, height=750)

# ==============================================================================
# HÌNH 4.8: Biểu đồ kết quả kiểm thử ma trận ngoại lệ Deep Chaos 109 Test Cases
# ==============================================================================
def generate_hinh_4_8():
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 1200px;
    height: 750px;
  }
  .container {
    width: 1160px;
    height: 710px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  }
  .title {
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 8px;
    text-transform: uppercase;
  }
  .subtitle {
    text-align: center;
    font-size: 13px;
    color: #64748b;
    margin-bottom: 24px;
  }
</style>
</head>
<body>
<div class="container">
  <div class="title">Kết quả kiểm thử ma trận ngoại lệ và xung đột khắc nghiệt (Deep Chaos 109 Test Suite)</div>
  <div class="subtitle">109/109 kịch bản kiểm thử khắc nghiệt đạt kết quả PASS (100% Tỷ lệ thành công)</div>
  <svg viewBox="0 0 1100 580" style="width:100%; height:580px;">
    <!-- Group 1 -->
    <rect x="50" y="30" width="1000" height="85" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="80" y="60" font-size="14" font-weight="700" fill="#1e293b">Nhóm 1: Mô phỏng phần cứng Mic (Mất quyền, ngắt kết nối đột ngột, jack cắm)</text>
    <text x="80" y="85" font-size="12" fill="#64748b">22 Kịch bản | Trạng thái: SessionActor tự động dọn dẹp tài nguyên & cảnh báo UI</text>
    <!-- Bar 1 -->
    <rect x="680" y="50" width="250" height="30" rx="6" fill="#10b981"/>
    <text x="805" y="70" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">22 / 22 PASS (100%)</text>
    <circle cx="960" cy="65" r="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
    <text x="960" y="70" text-anchor="middle" font-size="14" font-weight="800" fill="#047857">✓</text>

    <!-- Group 2 -->
    <rect x="50" y="130" width="1000" height="85" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="80" y="160" font-size="14" font-weight="700" fill="#1e293b">Nhóm 2: Chuyển đổi ngôn ngữ & Xung đột trạng thái Dual-Mic Mutex</text>
    <text x="80" y="185" font-size="12" fill="#64748b">25 Kịch bản | Trạng thái: Chặn thành công 100% xung đột tranh chấp kênh, 0 lỗi đè âm</text>
    <!-- Bar 2 -->
    <rect x="680" y="150" width="250" height="30" rx="6" fill="#10b981"/>
    <text x="805" y="170" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">25 / 25 PASS (100%)</text>
    <circle cx="960" cy="165" r="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
    <text x="960" y="170" text-anchor="middle" font-size="14" font-weight="800" fill="#047857">✓</text>

    <!-- Group 3 -->
    <rect x="50" y="230" width="1000" height="85" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="80" y="260" font-size="14" font-weight="700" fill="#1e293b">Nhóm 3: Đường ống âm thanh, Nhiễu nền cực đoan & Mất gói tin (Packet Loss)</text>
    <text x="80" y="285" font-size="12" fill="#64748b">20 Kịch bản | Trạng thái: WebRTC VAD 500ms cắt câu chuẩn xác, bộ đệm thích ứng bù jitter</text>
    <!-- Bar 3 -->
    <rect x="680" y="250" width="250" height="30" rx="6" fill="#10b981"/>
    <text x="805" y="270" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">20 / 20 PASS (100%)</text>
    <circle cx="960" cy="265" r="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
    <text x="960" y="270" text-anchor="middle" font-size="14" font-weight="800" fill="#047857">✓</text>

    <!-- Group 4 -->
    <rect x="50" y="330" width="1000" height="85" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="80" y="360" font-size="14" font-weight="700" fill="#1e293b">Nhóm 4: Bão mạng (Network Chaos), Mất mạng giữa chừng & Reconnect WebSocket</text>
    <text x="80" y="385" font-size="12" fill="#64748b">24 Kịch bản | Trạng thái: Tái kết nối tự động có backoff, bảo toàn ngữ cảnh phiên dịch</text>
    <!-- Bar 4 -->
    <rect x="680" y="350" width="250" height="30" rx="6" fill="#10b981"/>
    <text x="805" y="370" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">24 / 24 PASS (100%)</text>
    <circle cx="960" cy="365" r="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
    <text x="960" y="370" text-anchor="middle" font-size="14" font-weight="800" fill="#047857">✓</text>

    <!-- Group 5 -->
    <rect x="50" y="430" width="1000" height="85" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="80" y="460" font-size="14" font-weight="700" fill="#1e293b">Nhóm 5: Tính toàn vẹn dịch thuật, Cách ly dữ liệu người dùng & Xâm thực bộ nhớ</text>
    <text x="80" y="485" font-size="12" fill="#64748b">18 Kịch bản | Trạng thái: Zero Memory Leak, bảo mật RBAC và cô lập phiên triệt để</text>
    <!-- Bar 5 -->
    <rect x="680" y="450" width="250" height="30" rx="6" fill="#10b981"/>
    <text x="805" y="470" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">18 / 18 PASS (100%)</text>
    <circle cx="960" cy="465" r="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
    <text x="960" y="470" text-anchor="middle" font-size="14" font-weight="800" fill="#047857">✓</text>

    <!-- TOTAL FOOTER -->
    <rect x="50" y="530" width="1000" height="40" rx="6" fill="#0f172a"/>
    <text x="80" y="555" font-size="14" font-weight="700" fill="#ffffff">TỔNG HỢP TOÀN BỘ MA TRẬN KIỂM THỬ KHẮC NGHIỆT:</text>
    <text x="950" y="555" text-anchor="end" font-size="14" font-weight="700" fill="#34d399">109 / 109 KỊCH BẢN THÀNH CÔNG (100%)</text>
  </svg>
</div>
</body>
</html>"""
    render_html_to_png(html, os.path.join(OUT_DIR, "hinh_4_8_bieu_do_ma_tran_chaos_stress_test.png"), width=1200, height=750)

if __name__ == "__main__":
    print("Starting generation of Chapter 4 diagrams...")
    generate_hinh_4_2()
    generate_hinh_4_3()
    generate_hinh_4_4()
    generate_hinh_4_5()
    generate_hinh_4_6()
    generate_hinh_4_7()
    generate_hinh_4_8()
    print("All Chapter 4 diagrams rendered successfully!")

