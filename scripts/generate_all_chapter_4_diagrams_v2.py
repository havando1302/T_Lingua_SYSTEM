# -*- coding: utf-8 -*-
"""
High-resolution Diagram & Flowchart Generator for T-Lingua Chapter 4 (V2)
Key improvements:
1. Removed all internal <div class="title"> headers as requested (standard academic figures use captions in document).
2. Added fill="none" to ALL SVG paths, polyline, and loopback arrows to eliminate black fill artifacts.
3. Redesigned Hình 4.4 (WebRTC VAD 500ms Cutoff flowchart):
   - Ample canvas size, no clipping, no text overlapping.
   - Clean spacing for "ĐỦ 500ms (KẾT THÚC CÂU)" and "KÍCH HOẠT SILENCE_CUTOFF".
4. Redesigned all other flowcharts (Hình 4.5, 4.6, 4.7, 4.8, 4.9, 4.10) with matching clean minimalist pastel aesthetics.
"""

import os
import shutil
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
# HÌNH 4.4: Lưu đồ thuật toán WebRTC VAD và cơ chế ngắt câu tự động (500ms Cutoff)
# ==============================================================================
def generate_hinh_4_4():
    # Width 1260, Height 900
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
    width: 1260px;
    height: 920px;
  }
  .container {
    width: 1220px;
    height: 880px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  }
  svg {
    width: 100%;
    height: 100%;
  }
</style>
</head>
<body>
<div class="container">
  <svg viewBox="0 0 1180 840">
    <defs>
      <!-- Gradients -->
      <linearGradient id="gradStart" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#3b82f6"/>
        <stop offset="100%" stop-color="#1d4ed8"/>
      </linearGradient>
      <linearGradient id="gradProcess" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#f8fafc"/>
        <stop offset="100%" stop-color="#f1f5f9"/>
      </linearGradient>
      <linearGradient id="gradDecision" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#fffbeb"/>
        <stop offset="100%" stop-color="#fef3c7"/>
      </linearGradient>
      <linearGradient id="gradAction" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#e0f2fe"/>
        <stop offset="100%" stop-color="#bae6fd"/>
      </linearGradient>
      <linearGradient id="gradFinish" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#10b981"/>
        <stop offset="100%" stop-color="#047857"/>
      </linearGradient>
      <!-- Shadow -->
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
        <feDropShadow dx="1" dy="2" stdDeviation="2.5" flood-opacity="0.08"/>
      </filter>
      <!-- Arrow markers -->
      <marker id="arr" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#334155"/>
      </marker>
      <marker id="arrRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#dc2626"/>
      </marker>
      <marker id="arrGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#16a34a"/>
      </marker>
      <marker id="arrAmber" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#d97706"/>
      </marker>
    </defs>

    <!-- ======================================================== -->
    <!-- 1. START NODE                                            -->
    <!-- ======================================================== -->
    <g transform="translate(470, 15)" filter="url(#shadow)">
      <rect x="0" y="0" width="240" height="46" rx="23" fill="url(#gradStart)"/>
      <text x="120" y="28" text-anchor="middle" font-size="14.5" font-weight="700" fill="#ffffff" letter-spacing="0.5">BẮT ĐẦU PHIÊN STREAM</text>
    </g>

    <!-- Arrow Start -> Ingestion -->
    <path d="M 590 61 L 590 95" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr)"/>

    <!-- ======================================================== -->
    <!-- 2. NHẬN GÓI PCM 16kHz                                     -->
    <!-- ======================================================== -->
    <g transform="translate(425, 95)" filter="url(#shadow)">
      <rect x="0" y="0" width="330" height="60" rx="8" fill="url(#gradProcess)" stroke="#cbd5e1" stroke-width="1.8"/>
      <text x="165" y="25" text-anchor="middle" font-size="13.5" font-weight="700" fill="#1e293b">Nhận gói PCM 16kHz (20ms / 320 bytes)</text>
      <text x="165" y="45" text-anchor="middle" font-size="11.5" fill="#64748b">Trích xuất từ luồng WebSocket Client Audio Stream</text>
    </g>

    <!-- Arrow Ingestion -> VAD Analysis -->
    <path d="M 590 155 L 590 190" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr)"/>

    <!-- ======================================================== -->
    <!-- 3. WEBRTC VAD ANALYSIS                                    -->
    <!-- ======================================================== -->
    <g transform="translate(435, 190)" filter="url(#shadow)">
      <rect x="0" y="0" width="310" height="58" rx="8" fill="url(#gradAction)" stroke="#0284c7" stroke-width="1.8"/>
      <text x="155" y="24" text-anchor="middle" font-size="13.5" font-weight="700" fill="#0369a1">Phân tích năng lượng & phổ WebRTC VAD</text>
      <text x="155" y="44" text-anchor="middle" font-size="11.5" fill="#0284c7">Aggressiveness Mode = 3 (Bộ lọc nhiễu tần số cao)</text>
    </g>

    <!-- Arrow VAD -> Decision 1 -->
    <path d="M 590 248 L 590 285" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr)"/>

    <!-- ======================================================== -->
    <!-- 4. DECISION 1: CÓ TIẾNG NÓI? (is_speech == True)         -->
    <!-- ======================================================== -->
    <g transform="translate(590, 335)" filter="url(#shadow)">
      <polygon points="0,-48 135,0 0,48 -135,0" fill="url(#gradDecision)" stroke="#d97706" stroke-width="2"/>
      <text x="0" y="-8" text-anchor="middle" font-size="13.5" font-weight="700" fill="#92400e">Có tiếng nói?</text>
      <text x="0" y="14" text-anchor="middle" font-size="11.5" font-weight="600" fill="#b45309">(is_speech == True)</text>
    </g>

    <!-- BRANCH YES of Decision 1 (To Right: Active Speech) -->
    <path d="M 725 335 L 860 335" fill="none" stroke="#16a34a" stroke-width="2.5" marker-end="url(#arrGreen)"/>
    <text x="785" y="323" text-anchor="middle" font-size="12.5" font-weight="700" fill="#16a34a">ĐÚNG (Có)</text>

    <!-- Box Active Speech -->
    <g transform="translate(860, 275)" filter="url(#shadow)">
      <rect x="0" y="0" width="280" height="125" rx="8" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
      <text x="140" y="26" text-anchor="middle" font-size="13.5" font-weight="700" fill="#065f46">XỬ LÝ ĐOẠN NÓI</text>
      <text x="20" y="50" font-size="11.5" fill="#047857">• Đặt State = ACTIVE_SPEECH</text>
      <text x="20" y="70" font-size="11.5" fill="#047857">• Ghi âm vào Audio RingBuffer</text>
      <text x="20" y="90" font-size="11.5" fill="#047857">• Đặt lại: silence_frames = 0</text>
      <text x="20" y="110" font-size="11.5" fill="#059669">• Phát sự kiện SPEECH_START tới Client</text>
    </g>

    <!-- Loopback: Active Speech -> Next Frame (fill="none" explicitly!) -->
    <path d="M 1000 400 L 1000 440 L 1150 440 L 1150 125 L 755 125" 
          fill="none" stroke="#10b981" stroke-width="1.8" stroke-dasharray="5,4" marker-end="url(#arrGreen)"/>
    <text x="1075" y="430" text-anchor="middle" font-size="10.5" font-weight="600" fill="#047857">Đọc frame kế tiếp</text>

    <!-- BRANCH NO of Decision 1 (Down: Silence Evaluation) -->
    <path d="M 590 383 L 590 435" fill="none" stroke="#dc2626" stroke-width="2" marker-end="url(#arrRed)"/>
    <text x="605" y="412" font-size="12" font-weight="700" fill="#dc2626">SAI (Yên lặng)</text>

    <!-- ======================================================== -->
    <!-- 5. DECISION 2: ĐANG TRONG LƯỢT NÓI? (State == ACTIVE)    -->
    <!-- ======================================================== -->
    <g transform="translate(590, 485)" filter="url(#shadow)">
      <polygon points="0,-48 135,0 0,48 -135,0" fill="url(#gradDecision)" stroke="#d97706" stroke-width="2"/>
      <text x="0" y="-8" text-anchor="middle" font-size="13" font-weight="700" fill="#92400e">Đang trong lượt nói?</text>
      <text x="0" y="14" text-anchor="middle" font-size="11.5" font-weight="600" fill="#b45309">(State == ACTIVE)?</text>
    </g>

    <!-- BRANCH NO of Decision 2 (To Left: Idle Silence / Noise Floor) -->
    <path d="M 455 485 L 320 485" fill="none" stroke="#64748b" stroke-width="2" marker-end="url(#arr)"/>
    <text x="385" y="473" text-anchor="middle" font-size="12" font-weight="700" fill="#64748b">CHƯA NÓI</text>

    <!-- Box Noise Floor Drop -->
    <g transform="translate(50, 455)" filter="url(#shadow)">
      <rect x="0" y="0" width="270" height="65" rx="8" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.6"/>
      <text x="135" y="27" text-anchor="middle" font-size="13" font-weight="700" fill="#334155">Bỏ qua Frame (Nhiễu nền)</text>
      <text x="135" y="48" text-anchor="middle" font-size="11" fill="#64748b">Cập nhật ngưỡng năng lượng nền</text>
    </g>

    <!-- Loopback: Noise Floor -> Next Frame (fill="none" explicitly!) -->
    <path d="M 185 455 L 185 125 L 425 125" 
          fill="none" stroke="#94a3b8" stroke-width="1.6" stroke-dasharray="5,4" marker-end="url(#arr)"/>

    <!-- BRANCH YES of Decision 2 (Down: Counting Silence) -->
    <path d="M 590 533 L 590 580" fill="none" stroke="#16a34a" stroke-width="2" marker-end="url(#arrGreen)"/>
    <text x="605" y="560" font-size="12" font-weight="700" fill="#16a34a">ĐANG NÓI (Khoảng lặng)</text>

    <!-- ======================================================== -->
    <!-- 6. INCREMENT SILENCE COUNTER                              -->
    <!-- ======================================================== -->
    <g transform="translate(435, 580)" filter="url(#shadow)">
      <rect x="0" y="0" width="310" height="46" rx="6" fill="url(#gradProcess)" stroke="#cbd5e1" stroke-width="1.8"/>
      <text x="155" y="28" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">silence_frames += 1 (tăng thêm 20ms)</text>
    </g>

    <!-- Arrow Counter -> Decision 3 -->
    <path d="M 590 626 L 590 665" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr)"/>

    <!-- ======================================================== -->
    <!-- 7. DECISION 3: CUTOFF REACHED? (silence_frames >= 25)    -->
    <!-- ======================================================== -->
    <g transform="translate(590, 715)" filter="url(#shadow)">
      <polygon points="0,-50 145,0 0,50 -145,0" fill="url(#gradDecision)" stroke="#d97706" stroke-width="2"/>
      <text x="0" y="-8" text-anchor="middle" font-size="13.5" font-weight="700" fill="#92400e">Khoảng lặng &gt;= 500ms?</text>
      <text x="0" y="14" text-anchor="middle" font-size="11.5" font-weight="600" fill="#b45309">(silence_frames &gt;= 25)</text>
    </g>

    <!-- BRANCH NO of Decision 3 (To Left: Chưa đủ 500ms, Loopback to Ingestion) -->
    <path d="M 445 715 L 360 715 L 360 145 L 425 145" 
          fill="none" stroke="#f59e0b" stroke-width="2" stroke-dasharray="5,4" marker-end="url(#arrAmber)"/>
    <text x="365" y="700" text-anchor="middle" font-size="11.5" font-weight="700" fill="#d97706">Chưa đủ 500ms</text>
    <text x="365" y="735" text-anchor="middle" font-size="10.5" fill="#b45309">(&lt; 25 frames)</text>

    <!-- BRANCH YES of Decision 3 (To Right: Đủ 500ms - Cutoff Finalize) -->
    <!-- Adjusted width and generous spacing so text never overlaps! -->
    <path d="M 735 715 L 835 715" fill="none" stroke="#16a34a" stroke-width="2.5" marker-end="url(#arrGreen)"/>
    <text x="785" y="700" text-anchor="middle" font-size="12.5" font-weight="700" fill="#16a34a">ĐỦ 500ms</text>
    <text x="785" y="733" text-anchor="middle" font-size="11" font-weight="600" fill="#047857">(KẾT THÚC CÂU)</text>

    <!-- Box Finalize Cutoff Action (Positioned cleanly at x=835) -->
    <g transform="translate(835, 665)" filter="url(#shadow)">
      <rect x="0" y="0" width="310" height="100" rx="8" fill="url(#gradFinish)"/>
      <text x="155" y="28" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff" letter-spacing="0.3">KÍCH HOẠT SILENCE_CUTOFF</text>
      <line x1="20" y1="38" x2="290" y2="38" stroke="#34d399" stroke-width="1"/>
      <text x="25" y="58" font-size="11.5" fill="#d1fae5">• Đóng gói Audio Turn (tệp WAV 16kHz)</text>
      <text x="25" y="76" font-size="11.5" fill="#ecfdf5">• Đẩy vào hàng đợi STT Worker (Whisper)</text>
      <text x="25" y="93" font-size="11" fill="#a7f3d0">• Reset State về IDLE & silence_frames = 0</text>
    </g>

  </svg>
</div>
</body>
</html>"""
    out_png = os.path.join(OUT_DIR, "hinh_4_4_luu_do_thuat_toan_webrtc_vad.png")
    render_html_to_png(html, out_png, width=1260, height=920)
    # Also sync duplicate name if needed
    shutil.copy(out_png, os.path.join(OUT_DIR, "hinh_4_2_luu_do_thuat_toan_webrtc_vad.png"))

# ==============================================================================
# HÌNH 4.5: Cơ chế khóa tương hỗ chống xung đột thoại Dual-Mic Mutex
# ==============================================================================
def generate_hinh_4_5():
    # Width 1240, Height 780
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
    width: 1240px;
    height: 760px;
  }
  .container {
    width: 1200px;
    height: 720px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  }
  svg { width: 100%; height: 100%; }
</style>
</head>
<body>
<div class="container">
  <svg viewBox="0 0 1160 680">
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
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
        <feDropShadow dx="1" dy="2" stdDeviation="2.5" flood-opacity="0.08"/>
      </filter>
      <marker id="arrBlue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#2563eb"/>
      </marker>
      <marker id="arrRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#ef4444"/>
      </marker>
      <marker id="arrGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#10b981"/>
      </marker>
    </defs>

    <!-- LEFT: User A (Vietnamese Speaker) -->
    <g transform="translate(20, 20)" filter="url(#shadow)">
      <rect x="0" y="0" width="280" height="640" rx="10" fill="url(#userABg)" stroke="#3b82f6" stroke-width="2"/>
      <text x="140" y="38" text-anchor="middle" font-size="16" font-weight="700" fill="#1d4ed8">NGƯỜI DÙNG A (MIC A)</text>
      <text x="140" y="60" text-anchor="middle" font-size="12" fill="#2563eb">Kênh ngôn ngữ: Tiếng Việt (vi-VN)</text>

      <rect x="25" y="90" width="230" height="90" rx="8" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5"/>
      <text x="140" y="120" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">1. Nhấn nút Mic A (Nói)</text>
      <text x="140" y="142" text-anchor="middle" font-size="11.5" fill="#475569">Gửi START_SPEAKING(vi)</text>
      <text x="140" y="162" text-anchor="middle" font-size="11.5" fill="#2563eb">Kèm luồng âm thanh PCM 16kHz</text>

      <rect x="25" y="240" width="230" height="95" rx="8" fill="#ecfdf5" stroke="#10b981" stroke-width="1.8"/>
      <text x="140" y="270" text-anchor="middle" font-size="13" font-weight="700" fill="#065f46">3. Nhận LOCK_ACQUIRED</text>
      <text x="140" y="294" text-anchor="middle" font-size="11.5" fill="#047857">UI: Sóng âm hoạt động (Xanh)</text>
      <text x="140" y="314" text-anchor="middle" font-size="11.5" fill="#047857">Toàn quyền truyền giọng nói</text>

      <rect x="25" y="470" width="230" height="95" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5"/>
      <text x="140" y="500" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">6. Dứt câu &gt; 500ms</text>
      <text x="140" y="524" text-anchor="middle" font-size="11.5" fill="#475569">Nhận kết quả dịch tiếng Anh</text>
      <text x="140" y="544" text-anchor="middle" font-size="11.5" fill="#10b981">TTS phát âm thanh câu dịch</text>
    </g>

    <!-- CENTER: SessionActor (Mutex Coordinator) -->
    <g transform="translate(370, 20)" filter="url(#shadow)">
      <rect x="0" y="0" width="420" height="640" rx="10" fill="url(#actorBg)" stroke="#64748b" stroke-width="2"/>
      <text x="210" y="38" text-anchor="middle" font-size="16" font-weight="700" fill="#0f172a">SESSION ACTOR (COORDINATOR)</text>
      <text x="210" y="60" text-anchor="middle" font-size="12" fill="#475569">Bộ điều phối phiên đàm thoại song ngữ thời gian thực</text>

      <!-- Mutex State Box -->
      <rect x="30" y="85" width="360" height="115" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.8"/>
      <text x="210" y="112" text-anchor="middle" font-size="13" font-weight="700" fill="#334155">BỘ ĐIỀU KHIỂN TRẠNG THÁI KHÓA (MUTEX)</text>
      <rect x="50" y="128" width="320" height="55" rx="6" fill="url(#lockGranted)"/>
      <text x="210" y="153" text-anchor="middle" font-size="13.5" font-weight="700" fill="#ffffff">LOCK OWNER: USER_A</text>
      <text x="210" y="171" text-anchor="middle" font-size="11" fill="#ecfdf5">active_channel = 'vi' | locked = True</text>

      <!-- Conflict Resolution Logic -->
      <rect x="30" y="230" width="360" height="180" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.8"/>
      <text x="210" y="258" text-anchor="middle" font-size="13" font-weight="700" fill="#334155">CƠ CHẾ GIẢI QUYẾT XUNG ĐỘT</text>
      <text x="50" y="288" font-size="12" fill="#1e293b">• Kiểm tra: <tspan font-weight="700" fill="#dc2626">is_locked() == True</tspan></text>
      <text x="50" y="312" font-size="12" fill="#1e293b">• Yêu cầu từ B bị từ chối tức thì (Zero-Latency)</text>
      <text x="50" y="336" font-size="12" fill="#1e293b">• Trả về gói tin: <tspan font-weight="700" fill="#dc2626">MUTEX_REJECTED</tspan></text>
      <text x="50" y="360" font-size="12" fill="#1e293b">• Lý do: <tspan font-style="italic">"Kênh đối phương đang phát âm"</tspan></text>
      <text x="50" y="385" font-size="11.5" fill="#64748b">• Chống dội âm phản hồi (Acoustic Echo / Feedback)</text>

      <!-- Release State Box -->
      <rect x="30" y="440" width="360" height="135" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.8"/>
      <text x="210" y="468" text-anchor="middle" font-size="13" font-weight="700" fill="#334155">GIẢI PHÓNG KHÓA (MUTEX_RELEASE)</text>
      <text x="50" y="498" font-size="12" fill="#1e293b">• Kích hoạt sau khi TTS phát loa hoàn tất</text>
      <text x="50" y="522" font-size="12" fill="#1e293b">• active_channel = None | locked = False</text>
      <text x="50" y="546" font-size="12" fill="#10b981" font-weight="700">• Broadcast CHANNEL_AVAILABLE tới 2 Mic</text>
    </g>

    <!-- RIGHT: User B (English Speaker) -->
    <g transform="translate(860, 20)" filter="url(#shadow)">
      <rect x="0" y="0" width="280" height="640" rx="10" fill="url(#userBBg)" stroke="#f43f5e" stroke-width="2"/>
      <text x="140" y="38" text-anchor="middle" font-size="16" font-weight="700" fill="#e11d48">NGƯỜI DÙNG B (MIC B)</text>
      <text x="140" y="60" text-anchor="middle" font-size="12" fill="#f43f5e">Kênh ngôn ngữ: Tiếng Anh (en-US)</text>

      <rect x="25" y="115" width="230" height="90" rx="8" fill="#ffffff" stroke="#fda4af" stroke-width="1.5"/>
      <text x="140" y="145" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">2. Nhấn nói cùng lúc</text>
      <text x="140" y="167" text-anchor="middle" font-size="11.5" fill="#475569">Gửi START_SPEAKING(en)</text>
      <text x="140" y="187" text-anchor="middle" font-size="11.5" fill="#e11d48">Cố gắng tranh chấp kênh thoại</text>

      <rect x="25" y="270" width="230" height="105" rx="8" fill="#fff1f2" stroke="#e11d48" stroke-width="2"/>
      <text x="140" y="298" text-anchor="middle" font-size="13" font-weight="700" fill="#9f1239">4. Nhận MUTEX_REJECTED</text>
      <text x="140" y="322" text-anchor="middle" font-size="11" fill="#e11d48">• Rung cảnh báo (Haptic Warning)</text>
      <text x="140" y="342" text-anchor="middle" font-size="11" fill="#e11d48">• UI: Nút Mic B mờ/vàng (Chờ)</text>
      <text x="140" y="360" text-anchor="middle" font-size="11" fill="#9f1239">• "Người đối diện đang nói..."</text>

      <rect x="25" y="470" width="230" height="95" rx="8" fill="#f0fdf4" stroke="#86efac" stroke-width="1.5"/>
      <text x="140" y="500" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">7. Kênh rảnh trở lại</text>
      <text x="140" y="524" text-anchor="middle" font-size="11.5" fill="#15803d">Nhận CHANNEL_AVAILABLE</text>
      <text x="140" y="544" text-anchor="middle" font-size="11.5" fill="#15803d">Nút Mic B sẵn sàng nhận lệnh nói</text>
    </g>

    <!-- ARROWS CONNECTING (fill="none" explicitly!) -->
    <!-- 1. A request to Actor -->
    <path d="M 300 155 L 400 155" fill="none" stroke="#2563eb" stroke-width="2" marker-end="url(#arrBlue)"/>
    <!-- 2. B request to Actor -->
    <path d="M 860 175 L 760 175" fill="none" stroke="#e11d48" stroke-width="2" marker-end="url(#arrRed)"/>
    <!-- 3. Actor grant A -->
    <path d="M 400 285 L 300 285" fill="none" stroke="#10b981" stroke-width="2" marker-end="url(#arrGreen)"/>
    <!-- 4. Actor reject B -->
    <path d="M 760 325 L 860 325" fill="none" stroke="#ef4444" stroke-width="2.5" marker-end="url(#arrRed)"/>
    <!-- 5. Release to both -->
    <path d="M 400 520 L 300 520" fill="none" stroke="#64748b" stroke-width="1.8" stroke-dasharray="4,4" marker-end="url(#arrBlue)"/>
    <path d="M 760 520 L 860 520" fill="none" stroke="#10b981" stroke-width="1.8" stroke-dasharray="4,4" marker-end="url(#arrGreen)"/>
  </svg>
</div>
</body>
</html>"""
    out_png = os.path.join(OUT_DIR, "hinh_4_5_co_che_khoa_mutex_dual_mic.png")
    render_html_to_png(html, out_png, width=1240, height=760)
    shutil.copy(out_png, os.path.join(OUT_DIR, "hinh_4_3_co_che_khoa_mutex_dual_mic.png"))

# ==============================================================================
# HÌNH 4.6: Quy trình kiểm chuẩn chất lượng dịch thuật MQM Human-in-the-Loop
# ==============================================================================
def generate_hinh_4_6():
    # Width 1220, Height 720
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
    width: 1220px;
    height: 700px;
  }
  .container {
    width: 1180px;
    height: 660px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  }
  svg { width: 100%; height: 100%; }
</style>
</head>
<body>
<div class="container">
  <svg viewBox="0 0 1140 620">
    <defs>
      <linearGradient id="stepGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#f8fafc"/>
        <stop offset="100%" stop-color="#f1f5f9"/>
      </linearGradient>
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
        <feDropShadow dx="1" dy="2" stdDeviation="2.5" flood-opacity="0.08"/>
      </filter>
      <marker id="arr" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#334155"/>
      </marker>
      <marker id="arrGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#16a34a"/>
      </marker>
      <marker id="arrRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#dc2626"/>
      </marker>
    </defs>

    <!-- STEP 1: Tiếp nhận bản ghi -->
    <g transform="translate(20, 30)" filter="url(#shadow)">
      <rect x="0" y="0" width="220" height="230" rx="8" fill="url(#stepGrad)" stroke="#cbd5e1" stroke-width="2"/>
      <rect x="0" y="0" width="220" height="42" rx="8" fill="#2563eb"/>
      <text x="110" y="27" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">1. TIẾP NHẬN BẢN GHI</text>
      <text x="25" y="70" font-size="12.5" font-weight="700" fill="#1e293b">Nguồn dữ liệu:</text>
      <text x="25" y="98" font-size="12" fill="#475569">• Người dùng gắn cờ (Flag)</text>
      <text x="25" y="124" font-size="12" fill="#475569">• STT Confidence &lt; 0.75</text>
      <text x="25" y="150" font-size="12" fill="#475569">• Mẫu ngẫu nhiên Fresh500</text>
      <line x1="20" y1="170" x2="200" y2="170" stroke="#e2e8f0" stroke-width="1"/>
      <text x="110" y="195" text-anchor="middle" font-size="11.5" font-style="italic" fill="#2563eb">Đẩy vào hàng đợi</text>
      <text x="110" y="213" text-anchor="middle" font-size="11.5" font-weight="700" fill="#1d4ed8">QA Ingestion Queue</text>
    </g>

    <!-- Arrow 1 -> 2 (fill="none" explicitly!) -->
    <path d="M 240 145 L 300 145" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr)"/>

    <!-- STEP 2: Phân loại lỗi MQM -->
    <g transform="translate(300, 20)" filter="url(#shadow)">
      <rect x="0" y="0" width="270" height="250" rx="8" fill="url(#stepGrad)" stroke="#0284c7" stroke-width="2"/>
      <rect x="0" y="0" width="270" height="42" rx="8" fill="#0284c7"/>
      <text x="135" y="27" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">2. PHÂN LOẠI LỖI MQM</text>
      <text x="20" y="72" font-size="12.5" font-weight="700" fill="#0369a1">• Accuracy (Độ chính xác):</text>
      <text x="35" y="94" font-size="11.5" fill="#334155">- Mistranslation, Omission, Addition</text>
      <text x="20" y="122" font-size="12.5" font-weight="700" fill="#0369a1">• Fluency (Độ lưu loát):</text>
      <text x="35" y="144" font-size="11.5" fill="#334155">- Grammar, Spelling, Typography</text>
      <text x="20" y="172" font-size="12.5" font-weight="700" fill="#0369a1">• Terminology (Thuật ngữ):</text>
      <text x="35" y="194" font-size="11.5" fill="#334155">- Inconsistent with Glossary</text>
      <text x="20" y="222" font-size="12" font-weight="600" fill="#0284c7">• Style & Locale Convention</text>
    </g>

    <!-- Arrow 2 -> 3 (fill="none" explicitly!) -->
    <path d="M 570 145 L 630 145" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr)"/>

    <!-- STEP 3: Trừ điểm trọng số -->
    <g transform="translate(630, 20)" filter="url(#shadow)">
      <rect x="0" y="0" width="240" height="250" rx="8" fill="url(#stepGrad)" stroke="#d97706" stroke-width="2"/>
      <rect x="0" y="0" width="240" height="42" rx="8" fill="#d97706"/>
      <text x="120" y="27" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">3. TRỪ ĐIỂM TRỌNG SỐ</text>
      <text x="20" y="72" font-size="12" font-weight="700" fill="#b45309">Thang điểm phạt MQM:</text>
      <text x="20" y="100" font-size="12" fill="#1e293b">• <tspan font-weight="700">Minor (-1 điểm):</tspan> Lỗi nhỏ</text>
      <text x="20" y="126" font-size="12" fill="#1e293b">• <tspan font-weight="700">Major (-5 điểm):</tspan> Sai lệch nghĩa</text>
      <text x="20" y="152" font-size="12" fill="#1e293b">• <tspan font-weight="700" fill="#dc2626">Critical (-10):</tspan> Nguy hại/Độc hại</text>
      <rect x="15" y="175" width="210" height="60" rx="6" fill="#fef3c7" stroke="#f59e0b" stroke-width="1"/>
      <text x="120" y="200" text-anchor="middle" font-size="12.5" font-weight="700" fill="#92400e">MQM_Score = 100 - Điểm_Phạt</text>
      <text x="120" y="222" text-anchor="middle" font-size="10.5" fill="#b45309">Ngưỡng đạt tiêu chuẩn: &gt;= 85 điểm</text>
    </g>

    <!-- Arrow 3 -> Decision (fill="none" explicitly!) -->
    <path d="M 870 145 L 940 145" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr)"/>

    <!-- STEP 4: Decision (Score >= 85?) -->
    <g transform="translate(1015, 145)" filter="url(#shadow)">
      <polygon points="0,-48 75,0 0,48 -75,0" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
      <text x="0" y="-8" text-anchor="middle" font-size="13" font-weight="700" fill="#92400e">Điểm &gt;= 85?</text>
      <text x="0" y="14" text-anchor="middle" font-size="11" fill="#b45309">(Đạt chuẩn)</text>
    </g>

    <!-- Branch YES: To Approved Dataset (fill="none" explicitly!) -->
    <path d="M 1015 193 L 1015 340" fill="none" stroke="#16a34a" stroke-width="2.5" marker-end="url(#arrGreen)"/>
    <text x="1030" y="260" font-size="12.5" font-weight="700" fill="#16a34a">ĐẠT (YES)</text>

    <!-- Approved Dataset Box -->
    <g transform="translate(870, 340)" filter="url(#shadow)">
      <rect x="0" y="0" width="250" height="150" rx="8" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
      <rect x="0" y="0" width="250" height="36" rx="8" fill="#059669"/>
      <text x="125" y="24" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">PHÊ DUYỆT (APPROVED)</text>
      <text x="20" y="62" font-size="11.5" fill="#047857">• Nạp vào Gold Standard TM</text>
      <text x="20" y="86" font-size="11.5" fill="#047857">• Đánh dấu Gold Dataset</text>
      <text x="20" y="110" font-size="11.5" fill="#047857">• Cập nhật kho huấn luyện LoRA</text>
      <text x="20" y="134" font-size="11" font-weight="700" fill="#065f46">Trạng thái: READY_FOR_TRAIN</text>
    </g>

    <!-- Branch NO: To Post-Editing (fill="none" explicitly!) -->
    <path d="M 1015 97 L 1015 15 L 435 15 L 435 340" fill="none" stroke="#dc2626" stroke-width="2" stroke-dasharray="5,4" marker-end="url(#arrRed)"/>
    <text x="730" y="12" text-anchor="middle" font-size="11.5" font-weight="700" fill="#dc2626">KHÔNG ĐẠT (&lt; 85 Điểm) -&gt; CHUYỂN HẬU BIÊN TẬP</text>

    <!-- Post-Editing Box -->
    <g transform="translate(300, 340)" filter="url(#shadow)">
      <rect x="0" y="0" width="270" height="150" rx="8" fill="#fff1f2" stroke="#e11d48" stroke-width="2"/>
      <rect x="0" y="0" width="270" height="36" rx="8" fill="#e11d48"/>
      <text x="135" y="24" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">HẬU BIÊN TẬP (POST-EDITING)</text>
      <text x="20" y="62" font-size="11.5" fill="#9f1239">• Chuyên viên chỉnh sửa bản dịch</text>
      <text x="20" y="86" font-size="11.5" fill="#9f1239">• Bổ sung thuật ngữ thiếu vào Glossary</text>
      <text x="20" y="110" font-size="11.5" fill="#9f1239">• Lưu vết: Target_PostEdited</text>
      <text x="20" y="134" font-size="11" font-weight="700" fill="#e11d48">Tái thẩm định MQM sau chỉnh sửa</text>
    </g>

    <!-- Arrow Post-Editing -> Approved (fill="none" explicitly!) -->
    <path d="M 570 415 L 870 415" fill="none" stroke="#16a34a" stroke-width="2.5" marker-end="url(#arrGreen)"/>
    <text x="720" y="405" text-anchor="middle" font-size="12" font-weight="700" fill="#16a34a">Đã sửa đạt chuẩn &gt;= 85</text>

    <!-- Bottom summary banner -->
    <rect x="20" y="525" width="1100" height="60" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="570" y="550" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">VÒNG LẶP ĐÓNG BĂNG VÀ XUẤT BẢN DATASET (FREEZE DATASET VÒNG ĐỜI MLOPS)</text>
    <text x="570" y="570" text-anchor="middle" font-size="11.5" fill="#64748b">Dữ liệu được kiểm duyệt đạt chuẩn MQM sẽ được đóng gói dưới định dạng JSONL/Parquet, tạo bệ phóng tinh chỉnh LoRA Adapter định kỳ</text>
  </svg>
</div>
</body>
</html>"""
    out_png = os.path.join(OUT_DIR, "hinh_4_6_quy_trinh_kiem_chuan_mqm_qa.png")
    render_html_to_png(html, out_png, width=1220, height=700)
    shutil.copy(out_png, os.path.join(OUT_DIR, "hinh_4_4_quy_trinh_kiem_chuan_mqm_qa.png"))

# ==============================================================================
# HÌNH 4.7: Kiến trúc nạp nóng LoRA Adapter và Canary Routing
# ==============================================================================
def generate_hinh_4_7():
    # Width 1220, Height 760
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
    width: 1220px;
    height: 760px;
  }
  .container {
    width: 1180px;
    height: 720px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  }
  svg { width: 100%; height: 100%; }
</style>
</head>
<body>
<div class="container">
  <svg viewBox="0 0 1140 680">
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
        <feDropShadow dx="1" dy="2" stdDeviation="2.5" flood-opacity="0.08"/>
      </filter>
      <marker id="arr" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#334155"/>
      </marker>
      <marker id="arrGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#16a34a"/>
      </marker>
      <marker id="arrAmber" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#d97706"/>
      </marker>
    </defs>

    <!-- Top: Client Traffic -->
    <g transform="translate(440, 15)" filter="url(#shadow)">
      <rect x="0" y="0" width="260" height="55" rx="8" fill="#1e293b"/>
      <text x="130" y="25" text-anchor="middle" font-size="14.5" font-weight="700" fill="#ffffff">LƯU LƯỢNG YÊU CẦU DỊCH</text>
      <text x="130" y="44" text-anchor="middle" font-size="11" fill="#94a3b8">100% Traffic từ Mobile App & REST API</text>
    </g>

    <!-- Arrow Traffic -> Gateway (fill="none" explicitly!) -->
    <path d="M 570 70 L 570 105" fill="none" stroke="#334155" stroke-width="2.5" marker-end="url(#arr)"/>

    <!-- CANARY ROUTER -->
    <g transform="translate(370, 105)" filter="url(#shadow)">
      <rect x="0" y="0" width="400" height="85" rx="10" fill="url(#gradGate)"/>
      <text x="200" y="30" text-anchor="middle" font-size="15.5" font-weight="700" fill="#ffffff">CANARY ROUTER & TRAFFIC SPLITTER</text>
      <text x="200" y="52" text-anchor="middle" font-size="11.5" fill="#bfdbfe">Điều hướng lưu lượng dựa trên trọng số cấu hình động</text>
      <text x="200" y="70" text-anchor="middle" font-size="11" fill="#93c5fd">Trọng số mặc định: 90% Stable | 10% Canary Staging</text>
    </g>

    <!-- Branch Left: Stable 90% (fill="none" explicitly!) -->
    <path d="M 450 190 L 450 250 L 250 250 L 250 285" fill="none" stroke="#16a34a" stroke-width="3" marker-end="url(#arrGreen)"/>
    <text x="320" y="240" font-size="13.5" font-weight="700" fill="#16a34a">90% Lưu lượng (Stable)</text>

    <!-- Branch Right: Canary 10% (fill="none" explicitly!) -->
    <path d="M 690 190 L 690 250 L 880 250 L 880 285" fill="none" stroke="#d97706" stroke-width="3" marker-end="url(#arrAmber)"/>
    <text x="740" y="240" font-size="13.5" font-weight="700" fill="#d97706">10% Lưu lượng (Canary)</text>

    <!-- LEFT: STABLE WORKER POOL -->
    <g transform="translate(50, 285)" filter="url(#shadow)">
      <rect x="0" y="0" width="400" height="230" rx="10" fill="url(#gradStable)" stroke="#10b981" stroke-width="2"/>
      <rect x="0" y="0" width="400" height="40" rx="10" fill="#059669"/>
      <text x="200" y="26" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">STABLE TRANSLATION WORKER (V1.0)</text>

      <rect x="20" y="55" width="360" height="55" rx="6" fill="#ffffff" stroke="#a7f3d0" stroke-width="1.5"/>
      <text x="200" y="80" text-anchor="middle" font-size="13" font-weight="700" fill="#065f46">Mô hình gốc NLLB-200 1.3B Base</text>
      <text x="200" y="98" text-anchor="middle" font-size="11" fill="#047857">CTranslate2 INT8 Caching Engine</text>

      <rect x="20" y="120" width="360" height="55" rx="6" fill="#ffffff" stroke="#a7f3d0" stroke-width="1.5"/>
      <text x="200" y="145" text-anchor="middle" font-size="13" font-weight="700" fill="#065f46">LoRA Adapter v1.0 Production</text>
      <text x="200" y="163" text-anchor="middle" font-size="11" fill="#047857">Trọng số thích ứng hiện hành (Độ trễ trung bình: 584ms)</text>

      <text x="200" y="208" text-anchor="middle" font-size="12" font-weight="600" fill="#047857">Độ ổn định: 99.98% | Error Rate: 0.02%</text>
    </g>

    <!-- RIGHT: CANARY WORKER POOL -->
    <g transform="translate(680, 285)" filter="url(#shadow)">
      <rect x="0" y="0" width="400" height="230" rx="10" fill="url(#gradCanary)" stroke="#f59e0b" stroke-width="2"/>
      <rect x="0" y="0" width="400" height="40" rx="10" fill="#d97706"/>
      <text x="200" y="26" text-anchor="middle" font-size="14" font-weight="700" fill="#ffffff">CANARY STAGING WORKER (V1.1-CANDIDATE)</text>

      <rect x="20" y="55" width="360" height="55" rx="6" fill="#ffffff" stroke="#fde68a" stroke-width="1.5"/>
      <text x="200" y="80" text-anchor="middle" font-size="13" font-weight="700" fill="#92400e">Mô hình gốc NLLB-200 1.3B Base</text>
      <text x="200" y="98" text-anchor="middle" font-size="11" fill="#b45309">Chia sẻ bộ nhớ trọng số cơ sở (Zero Copy)</text>

      <rect x="20" y="120" width="360" height="55" rx="6" fill="#ffffff" stroke="#fde68a" stroke-width="1.5"/>
      <text x="200" y="145" text-anchor="middle" font-size="13" font-weight="700" fill="#92400e">LoRA Adapter v1.1 Hot-Swapped</text>
      <text x="200" y="163" text-anchor="middle" font-size="11" fill="#b45309">Adapter nạp nóng động trong RAM (Safetensors)</text>

      <text x="200" y="208" text-anchor="middle" font-size="12" font-weight="600" fill="#b45309">Thuật toán nạp không gián đoạn (Zero-Downtime Hot Swap)</text>
    </g>

    <!-- BOTTOM: Telemetry & Automated Rollback / Promotion Controller -->
    <g transform="translate(50, 545)" filter="url(#shadow)">
      <rect x="0" y="0" width="1030" height="110" rx="10" fill="#f8fafc" stroke="#64748b" stroke-width="2"/>
      <text x="515" y="30" text-anchor="middle" font-size="14.5" font-weight="700" fill="#0f172a">HỆ THỐNG GIÁM SÁT TELEMETRY & ĐIỀU PHỐI VÒNG ĐỜI MÔ HÌNH TỰ ĐỘNG</text>
      <line x1="30" y1="42" x2="1000" y2="42" stroke="#cbd5e1" stroke-width="1"/>
      <text x="250" y="68" text-anchor="middle" font-size="12" fill="#334155"><tspan font-weight="700">Kịch bản 1: Thành công</tspan> (chrF++ tăng &gt; 1.5 điểm, P95 &lt; 1000ms)</text>
      <text x="250" y="90" text-anchor="middle" font-size="11.5" font-weight="600" fill="#059669">Nâng cấp tự động Canary lên 100% (Promote to Production)</text>
      <line x1="515" y1="50" x2="515" y2="100" stroke="#cbd5e1" stroke-width="1"/>
      <text x="770" y="68" text-anchor="middle" font-size="12" fill="#334155"><tspan font-weight="700">Kịch bản 2: Bất thường</tspan> (Lỗi tăng &gt; 1% hoặc sụt giảm chrF++)</text>
      <text x="770" y="90" text-anchor="middle" font-size="11.5" font-weight="600" fill="#dc2626">Tự động hủy lưu lượng Canary về 0% (Instant Rollback)</text>
    </g>

    <!-- Downward arrows to controller (fill="none" explicitly!) -->
    <path d="M 250 515 L 250 545" fill="none" stroke="#16a34a" stroke-width="2" marker-end="url(#arrGreen)"/>
    <path d="M 880 515 L 880 545" fill="none" stroke="#d97706" stroke-width="2" marker-end="url(#arrAmber)"/>
  </svg>
</div>
</body>
</html>"""
    out_png = os.path.join(OUT_DIR, "hinh_4_7_kien_truc_lora_canary_routing.png")
    render_html_to_png(html, out_png, width=1220, height=760)
    shutil.copy(out_png, os.path.join(OUT_DIR, "hinh_4_5_kien_truc_lora_canary_routing.png"))

# ==============================================================================
# HÌNH 4.8: Biểu đồ so sánh độ trễ đường ống dịch Baseline vs Optimized (Fresh500)
# ==============================================================================
def generate_hinh_4_8():
    # Width 1200, Height 680
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
    width: 1200px;
    height: 680px;
  }
  .container {
    width: 1160px;
    height: 640px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  }
  svg { width: 100%; height: 100%; }
</style>
</head>
<body>
<div class="container">
  <svg viewBox="0 0 1100 580">
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
    <rect x="180" y="345" width="45" height="115" rx="4" fill="#94a3b8"/>
    <text x="202" y="335" text-anchor="middle" font-size="12" font-weight="700" fill="#475569">720 ms</text>
    <rect x="235" y="421" width="45" height="39" rx="4" fill="#3b82f6"/>
    <text x="257" y="413" text-anchor="middle" font-size="12" font-weight="700" fill="#1d4ed8">245 ms</text>
    <text x="230" y="485" text-anchor="middle" font-size="13" font-weight="600" fill="#1e293b">STT (Whisper)</text>
    <text x="230" y="503" text-anchor="middle" font-size="11" font-weight="700" fill="#16a34a">Giảm 66.0%</text>

    <!-- GROUP 2: MT NLLB Latency -->
    <rect x="360" y="378" width="45" height="82" rx="4" fill="#94a3b8"/>
    <text x="382" y="370" text-anchor="middle" font-size="12" font-weight="700" fill="#475569">510 ms</text>
    <rect x="415" y="431" width="45" height="29" rx="4" fill="#3b82f6"/>
    <text x="437" y="423" text-anchor="middle" font-size="12" font-weight="700" fill="#1d4ed8">182 ms</text>
    <text x="410" y="485" text-anchor="middle" font-size="13" font-weight="600" fill="#1e293b">MT (NLLB-200)</text>
    <text x="410" y="503" text-anchor="middle" font-size="11" font-weight="700" fill="#16a34a">Giảm 64.3%</text>

    <!-- GROUP 3: TTS Piper VITS Latency -->
    <rect x="540" y="412" width="45" height="48" rx="4" fill="#94a3b8"/>
    <text x="562" y="404" text-anchor="middle" font-size="12" font-weight="700" fill="#475569">299 ms</text>
    <rect x="595" y="435" width="45" height="25" rx="4" fill="#3b82f6"/>
    <text x="617" y="427" text-anchor="middle" font-size="12" font-weight="700" fill="#1d4ed8">157 ms</text>
    <text x="590" y="485" text-anchor="middle" font-size="13" font-weight="600" fill="#1e293b">TTS (Piper VITS)</text>
    <text x="590" y="503" text-anchor="middle" font-size="11" font-weight="700" fill="#16a34a">Giảm 47.5%</text>

    <!-- GROUP 4: TOTAL MEAN LATENCY -->
    <rect x="720" y="215" width="55" height="245" rx="4" fill="#f87171"/>
    <text x="747" y="205" text-anchor="middle" font-size="13" font-weight="700" fill="#b91c1c">1,530 ms</text>
    <rect x="785" y="367" width="55" height="93" rx="4" fill="#10b981"/>
    <text x="812" y="357" text-anchor="middle" font-size="13" font-weight="700" fill="#047857">584 ms</text>
    <text x="780" y="485" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">Tổng trễ trung bình</text>
    <text x="780" y="503" text-anchor="middle" font-size="12" font-weight="700" fill="#16a34a">Giảm 61.8% (-946ms)</text>

    <!-- GROUP 5: P95 LATENCY -->
    <rect x="910" y="118" width="55" height="342" rx="4" fill="#f87171"/>
    <text x="937" y="108" text-anchor="middle" font-size="13" font-weight="700" fill="#b91c1c">2,140 ms</text>
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
    out_png = os.path.join(OUT_DIR, "hinh_4_8_bieu_do_so_sanh_do_tre_fresh500.png")
    render_html_to_png(html, out_png, width=1200, height=680)
    shutil.copy(out_png, os.path.join(OUT_DIR, "hinh_4_6_bieu_do_so_sanh_do_tre_fresh500.png"))

# ==============================================================================
# HÌNH 4.9: Biểu đồ loss curve LoRA Training
# ==============================================================================
def generate_hinh_4_9():
    # Width 1200, Height 680
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
    width: 1200px;
    height: 680px;
  }
  .container {
    width: 1160px;
    height: 640px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  }
  svg { width: 100%; height: 100%; }
</style>
</head>
<body>
<div class="container">
  <svg viewBox="0 0 1100 580">
    <!-- Grid -->
    <line x1="100" y1="460" x2="1020" y2="460" stroke="#cbd5e1" stroke-width="1.5"/>
    <line x1="100" y1="360" x2="1020" y2="360" stroke="#f1f5f9" stroke-width="1"/>
    <line x1="100" y1="260" x2="1020" y2="260" stroke="#f1f5f9" stroke-width="1"/>
    <line x1="100" y1="160" x2="1020" y2="160" stroke="#f1f5f9" stroke-width="1"/>
    <line x1="100" y1="60" x2="1020" y2="60" stroke="#f1f5f9" stroke-width="1"/>

    <!-- Y-axis Left: Loss (0 to 4.0) -->
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
    <text x="100" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 0</text>
    <text x="253" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 50</text>
    <text x="406" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 100 (Epoch 1)</text>
    <text x="560" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 150</text>
    <text x="713" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 200 (Epoch 2)</text>
    <text x="866" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 250</text>
    <text x="1020" y="485" text-anchor="middle" font-size="12" fill="#64748b">Step 300 (Epoch 3)</text>

    <!-- Training Loss Curve (fill="none" explicitly!) -->
    <path d="M 100 118 Q 253 235 406 298 T 713 366 T 1020 398" fill="none" stroke="#ef4444" stroke-width="3.5"/>
    <circle cx="100" cy="118" r="4" fill="#ef4444"/>
    <circle cx="406" cy="298" r="4" fill="#ef4444"/>
    <circle cx="713" cy="366" r="4" fill="#ef4444"/>
    <circle cx="1020" cy="398" r="5" fill="#dc2626"/>
    <text x="1020" y="385" font-size="12" font-weight="700" fill="#dc2626">Loss = 0.62</text>

    <!-- Validation Loss Curve (fill="none" explicitly!) -->
    <path d="M 100 125 Q 253 245 406 305 T 713 375 T 1020 405" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="6,4"/>
    <circle cx="1020" cy="405" r="4" fill="#d97706"/>
    <text x="1020" y="425" font-size="11" font-weight="600" fill="#d97706">Val Loss = 0.71</text>

    <!-- chrF++ Curve (fill="none" explicitly!) -->
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
    out_png = os.path.join(OUT_DIR, "hinh_4_9_bieu_do_loss_curve_lora_training.png")
    render_html_to_png(html, out_png, width=1200, height=680)
    shutil.copy(out_png, os.path.join(OUT_DIR, "hinh_4_7_bieu_do_loss_curve_lora_training.png"))

# ==============================================================================
# HÌNH 4.10: Biểu đồ kết quả kiểm thử ma trận Deep Chaos 109 Test Cases
# ==============================================================================
def generate_hinh_4_10():
    # Width 1200, Height 640
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
    width: 1200px;
    height: 640px;
  }
  .container {
    width: 1160px;
    height: 600px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  }
  svg { width: 100%; height: 100%; }
</style>
</head>
<body>
<div class="container">
  <svg viewBox="0 0 1100 560">
    <!-- Group 1 -->
    <rect x="50" y="20" width="1000" height="85" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="80" y="50" font-size="14" font-weight="700" fill="#1e293b">Nhóm 1: Mô phỏng phần cứng Mic (Mất quyền, ngắt kết nối đột ngột, jack cắm)</text>
    <text x="80" y="75" font-size="12" fill="#64748b">22 Kịch bản | Trạng thái: SessionActor tự động dọn dẹp tài nguyên & cảnh báo UI</text>
    <rect x="680" y="40" width="250" height="30" rx="6" fill="#10b981"/>
    <text x="805" y="60" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">22 / 22 PASS (100%)</text>
    <circle cx="960" cy="55" r="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
    <text x="960" y="60" text-anchor="middle" font-size="14" font-weight="800" fill="#047857">✓</text>

    <!-- Group 2 -->
    <rect x="50" y="120" width="1000" height="85" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="80" y="150" font-size="14" font-weight="700" fill="#1e293b">Nhóm 2: Chuyển đổi ngôn ngữ & Xung đột trạng thái Dual-Mic Mutex</text>
    <text x="80" y="175" font-size="12" fill="#64748b">25 Kịch bản | Trạng thái: Chặn thành công 100% xung đột tranh chấp kênh, 0 lỗi đè âm</text>
    <rect x="680" y="140" width="250" height="30" rx="6" fill="#10b981"/>
    <text x="805" y="160" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">25 / 25 PASS (100%)</text>
    <circle cx="960" cy="155" r="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
    <text x="960" y="160" text-anchor="middle" font-size="14" font-weight="800" fill="#047857">✓</text>

    <!-- Group 3 -->
    <rect x="50" y="220" width="1000" height="85" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="80" y="250" font-size="14" font-weight="700" fill="#1e293b">Nhóm 3: Đường ống âm thanh, Nhiễu nền cực đoan & Mất gói tin (Packet Loss)</text>
    <text x="80" y="275" font-size="12" fill="#64748b">20 Kịch bản | Trạng thái: WebRTC VAD 500ms cắt câu chuẩn xác, bộ đệm thích ứng bù jitter</text>
    <rect x="680" y="240" width="250" height="30" rx="6" fill="#10b981"/>
    <text x="805" y="260" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">20 / 20 PASS (100%)</text>
    <circle cx="960" cy="255" r="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
    <text x="960" y="260" text-anchor="middle" font-size="14" font-weight="800" fill="#047857">✓</text>

    <!-- Group 4 -->
    <rect x="50" y="320" width="1000" height="85" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="80" y="350" font-size="14" font-weight="700" fill="#1e293b">Nhóm 4: Bão mạng (Network Chaos), Mất mạng giữa chừng & Reconnect WebSocket</text>
    <text x="80" y="375" font-size="12" fill="#64748b">24 Kịch bản | Trạng thái: Tái kết nối tự động có backoff, bảo toàn ngữ cảnh phiên dịch</text>
    <rect x="680" y="340" width="250" height="30" rx="6" fill="#10b981"/>
    <text x="805" y="360" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">24 / 24 PASS (100%)</text>
    <circle cx="960" cy="355" r="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
    <text x="960" y="360" text-anchor="middle" font-size="14" font-weight="800" fill="#047857">✓</text>

    <!-- Group 5 -->
    <rect x="50" y="420" width="1000" height="85" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
    <text x="80" y="450" font-size="14" font-weight="700" fill="#1e293b">Nhóm 5: Tính toàn vẹn dịch thuật, Cách ly dữ liệu người dùng & Xâm thực bộ nhớ</text>
    <text x="80" y="475" font-size="12" fill="#64748b">18 Kịch bản | Trạng thái: Zero Memory Leak, bảo mật RBAC và cô lập phiên triệt để</text>
    <rect x="680" y="440" width="250" height="30" rx="6" fill="#10b981"/>
    <text x="805" y="460" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">18 / 18 PASS (100%)</text>
    <circle cx="960" cy="455" r="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
    <text x="960" y="460" text-anchor="middle" font-size="14" font-weight="800" fill="#047857">✓</text>

    <!-- TOTAL FOOTER -->
    <rect x="50" y="515" width="1000" height="38" rx="6" fill="#0f172a"/>
    <text x="80" y="539" font-size="13.5" font-weight="700" fill="#ffffff">TỔNG HỢP TOÀN BỘ MA TRẬN KIỂM THỬ KHẮC NGHIỆT:</text>
    <text x="950" y="539" text-anchor="end" font-size="13.5" font-weight="700" fill="#34d399">109 / 109 KỊCH BẢN THÀNH CÔNG (100%)</text>
  </svg>
</div>
</body>
</html>"""
    out_png = os.path.join(OUT_DIR, "hinh_4_10_bieu_do_ma_tran_chaos_stress_test.png")
    render_html_to_png(html, out_png, width=1200, height=640)
    shutil.copy(out_png, os.path.join(OUT_DIR, "hinh_4_8_bieu_do_ma_tran_chaos_stress_test.png"))

if __name__ == "__main__":
    print("Regenerating all Chapter 4 diagrams (V2)...")
    generate_hinh_4_4()
    generate_hinh_4_5()
    generate_hinh_4_6()
    generate_hinh_4_7()
    generate_hinh_4_8()
    generate_hinh_4_9()
    generate_hinh_4_10()
    print("All Chapter 4 diagrams regenerated successfully!")

