# -*- coding: utf-8 -*-
"""
High-Resolution Architecture Diagram Generator for T-Lingua Figure 4.1:
Sơ đồ kiến trúc triển khai hệ thống T-Lingua.
Designed strictly following the visual style of the reference diagram:
- 3 Blue Client boxes at the top with downward arrows
- 2 Main Middle Containers:
    + Left (Green): FastAPI Backend Gateway (12 module boxes + bottom ORM bar)
    + Right (Orange/Amber): AI Inference Engine Workers (4 pipeline worker boxes + bottom weights bar)
- 2 Pink intermediary services: Redis 7.2 Cache & Audio Assets
- Bottom Full-width Container (Warm Gray): SQLite (13 tables in 5 domain cards + bottom WAL note)
- Output to docs/img/hinh_4_1_kien_truc_trien_khai_he_thong.png
"""

import os
import subprocess
from pathlib import Path

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DOCS_IMG_DIR = Path(r"C:\Du_an\T_Langua_Test\docs\img")
OUT_PNG = DOCS_IMG_DIR / "hinh_4_1_kien_truc_trien_khai_he_thong.png"

def generate_hinh_4_1_diagram():
    html_content = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 1240px;
    height: 800px;
  }
  .canvas {
    width: 1220px;
    height: 780px;
    background: #ffffff;
    position: relative;
    padding: 10px;
  }
  svg {
    width: 100%;
    height: 100%;
    overflow: visible;
  }

  /* Typography */
  .title-bold { font-weight: 700; fill: #0f172a; }
  .text-desc { font-size: 8.5px; fill: #475569; }
  .text-label { font-size: 9px; fill: #334155; font-weight: 500; }
  .arrow-label { font-size: 8px; fill: #475569; font-weight: 600; text-anchor: middle; }

  /* Client Box Style (Top) */
  .client-rect {
    fill: #ebf5ff;
    stroke: #93c5fd;
    stroke-width: 1.2;
    rx: 6;
  }
  .client-title {
    font-size: 11px;
    font-weight: 700;
    fill: #1e3a8a;
    text-anchor: middle;
  }
  .client-sub {
    font-size: 9px;
    fill: #475569;
    text-anchor: middle;
  }

  /* Left Main Container (Green) */
  .container-green {
    fill: #f4fbf4;
    stroke: #86efac;
    stroke-width: 1.4;
    rx: 10;
  }
  .container-title-green {
    font-size: 11.5px;
    font-weight: 700;
    fill: #14532d;
  }
  .mod-green {
    fill: #ffffff;
    stroke: #86efac;
    stroke-width: 1;
    rx: 4;
  }
  .mod-title {
    font-size: 9.5px;
    font-weight: 700;
    fill: #0f172a;
    text-anchor: middle;
  }
  .mod-sub {
    font-size: 8px;
    fill: #475569;
    text-anchor: middle;
  }
  .bottom-bar-green {
    fill: #dcfce7;
    stroke: #86efac;
    stroke-width: 1.2;
    rx: 4;
  }
  .bar-text-green {
    font-size: 10px;
    font-weight: 700;
    fill: #14532d;
    text-anchor: middle;
  }

  /* Right Main Container (Orange/Amber) */
  .container-orange {
    fill: #fffdf5;
    stroke: #fcd34d;
    stroke-width: 1.4;
    rx: 10;
  }
  .container-title-orange {
    font-size: 11.5px;
    font-weight: 700;
    fill: #92400e;
  }
  .mod-orange {
    fill: #fffbeb;
    stroke: #fde68a;
    stroke-width: 1;
    rx: 4;
  }
  .bottom-bar-orange {
    fill: #fed7aa;
    stroke: #fba24f;
    stroke-width: 1.2;
    rx: 4;
  }
  .bar-text-orange {
    font-size: 10px;
    font-weight: 700;
    fill: #7c2d12;
    text-anchor: middle;
  }

  /* Pink Middle Services */
  .pink-rect {
    fill: #fff1f2;
    stroke: #fda4af;
    stroke-width: 1.2;
    rx: 6;
  }
  .pink-title {
    font-size: 10px;
    font-weight: 700;
    fill: #9f1239;
    text-anchor: middle;
  }
  .pink-sub {
    font-size: 8.5px;
    fill: #881337;
    text-anchor: middle;
  }

  /* Bottom Container (Database) */
  .container-db {
    fill: #fbf9f7;
    stroke: #d6d3d1;
    stroke-width: 1.4;
    rx: 10;
  }
  .container-title-db {
    font-size: 11.5px;
    font-weight: 700;
    fill: #292524;
  }
  .db-card {
    fill: #ffffff;
    stroke: #e2e8f0;
    stroke-width: 1;
    rx: 5;
  }
  .db-card-title {
    font-size: 9.5px;
    font-weight: 700;
    fill: #0f172a;
  }
  .db-card-table {
    font-size: 8.5px;
    font-family: "Courier New", Courier, monospace;
    fill: #334155;
  }
  .db-footer-note {
    font-size: 8px;
    fill: #78716c;
    font-style: italic;
  }
</style>
</head>
<body>
<div class="canvas">
  <svg viewBox="0 0 1200 760">
    <defs>
      <!-- Arrow Marker Standard -->
      <marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
        <path d="M 0 0 L 6 3 L 0 6 z" fill="#475569"/>
      </marker>
      <!-- Arrow Marker Double-ended Start -->
      <marker id="arrStart" markerWidth="6" markerHeight="6" refX="1" refY="3" orient="auto">
        <path d="M 6 0 L 0 3 L 6 6 z" fill="#475569"/>
      </marker>
    </defs>

    <!-- ========================================================================= -->
    <!-- LAYER 1: TOP CLIENTS (3 Blue Boxes)                                       -->
    <!-- ========================================================================= -->

    <!-- Client 1: Mobile App -->
    <rect class="client-rect" x="70" y="2" width="200" height="52"/>
    <text class="client-title" x="170" y="22">Người dùng di động</text>
    <text class="client-sub" x="170" y="38">Ứng dụng Flutter (Android · iOS)</text>

    <!-- Client 2: Admin Portal -->
    <rect class="client-rect" x="390" y="2" width="200" height="52"/>
    <text class="client-title" x="490" y="22">Quản trị viên & Chuyên viên QA</text>
    <text class="client-sub" x="490" y="38">Trình duyệt Web (Admin Portal React/Vite)</text>

    <!-- Client 3: Third-Party Client -->
    <rect class="client-rect" x="910" y="2" width="200" height="52"/>
    <text class="client-title" x="1010" y="22">Hệ thống tích hợp đối tác</text>
    <text class="client-sub" x="1010" y="38">API Consumer / Third-party Client</text>

    <!-- Arrows from Clients to Main Server -->
    <!-- From Client 1 -->
    <line x1="170" y1="54" x2="170" y2="88" stroke="#475569" stroke-width="1.2" marker-end="url(#arr)"/>
    <!-- From Client 2 -->
    <line x1="490" y1="54" x2="490" y2="88" stroke="#475569" stroke-width="1.2" marker-end="url(#arr)"/>
    <!-- From Client 3 -->
    <line x1="1010" y1="54" x2="1010" y2="88" stroke="#475569" stroke-width="1.2" marker-end="url(#arr)"/>

    <!-- ========================================================================= -->
    <!-- LAYER 2: MIDDLE APPLICATION SERVERS                                       -->
    <!-- ========================================================================= -->

    <!-- ------------------------------------------------------------------------- -->
    <!-- CONTAINER 1: FastAPI Backend Server & Gateway (Green)                     -->
    <!-- Width: 760, Height: 260, x: 10, y: 90                                     -->
    <!-- ------------------------------------------------------------------------- -->
    <rect class="container-green" x="10" y="90" width="760" height="260"/>
    <text class="container-title-green" x="24" y="112">FastAPI Backend Server & Gateway (Uvicorn ASGI · Asyncio Router · REST Controllers · Actor Model)</text>

    <!-- Grid of 12 Functional Modules: 4 Columns x 3 Rows -->
    <!-- Row 1: y=126, height=44 -->
    <!-- Box 1.1 -->
    <rect class="mod-green" x="25" y="126" width="170" height="44"/>
    <text class="mod-title" x="110" y="143">Xác thực & Phân quyền</text>
    <text class="mod-sub" x="110" y="157">Argon2id · MFA TOTP · JWT · RBAC 4 cấp</text>

    <!-- Box 1.2 -->
    <rect class="mod-green" x="205" y="126" width="170" height="44"/>
    <text class="mod-title" x="290" y="143">Điều phối phiên SessionActor</text>
    <text class="mod-sub" x="290" y="157">WebSocket song công · Audio RingBuffer</text>

    <!-- Box 1.3 -->
    <rect class="mod-green" x="385" y="126" width="180" height="44"/>
    <text class="mod-title" x="475" y="143">Tách âm WebRTC VAD</text>
    <text class="mod-sub" x="475" y="157">Khung 20ms · Ngắt câu 500ms Cutoff</text>

    <!-- Box 1.4 -->
    <rect class="mod-green" x="575" y="126" width="180" height="44"/>
    <text class="mod-title" x="665" y="143">Khóa thoại Dual-Mic Mutex</text>
    <text class="mod-sub" x="665" y="157">Chống tranh chấp thoại · BLoC State · Rung</text>

    <!-- Row 2: y=178, height=44 -->
    <!-- Box 2.1 -->
    <rect class="mod-green" x="25" y="178" width="170" height="44"/>
    <text class="mod-title" x="110" y="195">Bộ nhớ dịch (TM Engine)</text>
    <text class="mod-sub" x="110" y="209">Tra cứu SHA-256 &lt; 5ms · Phê duyệt MQM</text>

    <!-- Box 2.2 -->
    <rect class="mod-green" x="205" y="178" width="170" height="44"/>
    <text class="mod-title" x="290" y="195">Từ điển thuật ngữ (Glossary)</text>
    <text class="mod-sub" x="290" y="209">Aho-Corasick · Bảo toàn số liệu 100%</text>

    <!-- Box 2.3 -->
    <rect class="mod-green" x="385" y="178" width="180" height="44"/>
    <text class="mod-title" x="475" y="195">Quản lý Users & API Keys</text>
    <text class="mod-sub" x="475" y="209">CRUD người dùng · Scope · Hash API Key</text>

    <!-- Box 2.4 -->
    <rect class="mod-green" x="575" y="178" width="180" height="44"/>
    <text class="mod-title" x="665" y="195">Kiểm chuẩn MQM Reviewer</text>
    <text class="mod-sub" x="665" y="209">Thẩm định Accuracy/Fluency/Term</text>

    <!-- Row 3: y=230, height=44 -->
    <!-- Box 3.1 -->
    <rect class="mod-green" x="25" y="230" width="170" height="44"/>
    <text class="mod-title" x="110" y="247">Giám sát viễn trắc Telemetry</text>
    <text class="mod-sub" x="110" y="261">Đo P50/P90/P99 chặng · Alert rule</text>

    <!-- Box 3.2 -->
    <rect class="mod-green" x="205" y="230" width="170" height="44"/>
    <text class="mod-title" x="290" y="247">Điều hướng Canary Routing</text>
    <text class="mod-sub" x="290" y="261">Phân luồng 90/10 · Instant Rollback &lt; 1s</text>

    <!-- Box 3.3 -->
    <rect class="mod-green" x="385" y="230" width="180" height="44"/>
    <text class="mod-title" x="475" y="247">Quản lý Dataset & Huấn luyện</text>
    <text class="mod-sub" x="475" y="261">Lọc tập dữ liệu vàng · Training job queue</text>

    <!-- Box 3.4 -->
    <rect class="mod-green" x="575" y="230" width="180" height="44"/>
    <text class="mod-title" x="665" y="247">Nhật ký kiểm toán Audit Log</text>
    <text class="mod-sub" x="665" y="261">Ghi vết sự kiện bất biến · Bảo vệ PII</text>

    <!-- Bottom Wide Bar (Green) -->
    <rect class="bottom-bar-green" x="25" y="286" width="730" height="48"/>
    <text class="bar-text-green" x="390" y="315">ORM / Cơ sở dữ liệu: SQLAlchemy 2.0 Models (backend/app/db/models.py) — SQLite (data/app.db)</text>


    <!-- ------------------------------------------------------------------------- -->
    <!-- CONTAINER 2: AI Inference Engine Workers (Orange/Amber)                   -->
    <!-- Width: 395, Height: 260, x: 795, y: 90                                    -->
    <!-- ------------------------------------------------------------------------- -->
    <rect class="container-orange" x="795" y="90" width="395" height="260"/>
    <text class="container-title-orange" x="810" y="112">AI Inference Engine Workers (CUDA Native · PyTorch · CTranslate2 · ONNX)</text>

    <!-- 4 Worker Boxes in Vertical Stack -->
    <!-- Box AI 1 -->
    <rect class="mod-orange" x="810" y="126" width="365" height="34"/>
    <text class="mod-title" x="992" y="141">Khử nhiễu DeepFilterNet</text>
    <text class="mod-sub" x="992" y="152">Lọc nhiễu nền · Tiền xử lý âm thanh PCM 16kHz</text>

    <!-- Box AI 2 -->
    <rect class="mod-orange" x="810" y="165" width="365" height="34"/>
    <text class="mod-title" x="992" y="180">ASR Worker (faster-whisper)</text>
    <text class="mod-sub" x="992" y="191">Whisper Turbo INT8 · Tách âm STT · RTF &lt; 0.12</text>

    <!-- Box AI 3 -->
    <rect class="mod-orange" x="810" y="204" width="365" height="34"/>
    <text class="mod-title" x="992" y="219">NMT Worker (Meta NLLB-200)</text>
    <text class="mod-sub" x="992" y="230">NLLB 1.3B · LoRA Adapter PEFT · Nạp nóng SafeTensors</text>

    <!-- Box AI 4 -->
    <rect class="mod-orange" x="810" y="243" width="365" height="34"/>
    <text class="mod-title" x="992" y="258">TTS Worker (Piper VITS)</text>
    <text class="mod-sub" x="992" y="269">Tổng hợp tiếng nói ONNX WAV 16kHz · RTF &lt; 0.15</text>

    <!-- Bottom Wide Bar (Orange) -->
    <rect class="bottom-bar-orange" x="810" y="286" width="365" height="48"/>
    <text class="bar-text-orange" x="992" y="315">Model Storage & Weights (NVMe / RAM: CTranslate2 INT8 · LoRA · ONNX)</text>


    <!-- ========================================================================= -->
    <!-- INTERMEDIATE LAYER: SHARED IN-MEMORY & FILE SERVICES (2 Pink Boxes)       -->
    <!-- Under left container, before database                                     -->
    <!-- ========================================================================= -->

    <!-- Pink Box 1: Redis 7.2 -->
    <rect class="pink-rect" x="80" y="375" width="210" height="48"/>
    <text class="pink-title" x="185" y="395">Redis 7.2 Cache</text>
    <text class="pink-sub" x="185" y="410">In-Memory: TM Cache · Mutex Lock · Session</text>

    <!-- Pink Box 2: Audio Storage -->
    <rect class="pink-rect" x="340" y="375" width="210" height="48"/>
    <text class="pink-title" x="445" y="395">Kho Audio Assets</text>
    <text class="pink-sub" x="445" y="410">data/audio: File WAV có Consent (QA/Train)</text>

    <!-- Arrows from FastAPI to Pink Services -->
    <!-- To Redis -->
    <line x1="185" y1="334" x2="185" y2="375" stroke="#475569" stroke-width="1.2" marker-start="url(#arrStart)" marker-end="url(#arr)"/>
    <text class="arrow-label" x="145" y="358">TCP / RESP</text>

    <!-- To Audio Storage -->
    <line x1="445" y1="334" x2="445" y2="375" stroke="#475569" stroke-width="1.2" marker-start="url(#arrStart)" marker-end="url(#arr)"/>
    <text class="arrow-label" x="410" y="358">File I/O</text>

    <!-- Arrow between Left and Right Container (IPC / asyncio.Queue) -->
    <line x1="770" y1="210" x2="795" y2="210" stroke="#475569" stroke-width="1.4" marker-start="url(#arrStart)" marker-end="url(#arr)"/>

    <!-- Arrow from AI Workers down to Database (Datasets & Deployments) -->
    <line x1="992" y1="334" x2="992" y2="450" stroke="#475569" stroke-width="1.2" marker-start="url(#arrStart)" marker-end="url(#arr)"/>
    <text class="arrow-label" x="1055" y="395">Weights &amp; Dataset I/O</text>


    <!-- Arrow from FastAPI ORM Bar directly down to Database Container -->
    <line x1="670" y1="334" x2="670" y2="450" stroke="#475569" stroke-width="1.4" marker-start="url(#arrStart)" marker-end="url(#arr)"/>
    <text class="arrow-label" x="725" y="395">SQLAlchemy · SQLite</text>


    <!-- ========================================================================= -->
    <!-- LAYER 3: BOTTOM DATABASE CONTAINER (SQLite - data/app.db)                 -->
    <!-- Width: 1180, Height: 285, x: 10, y: 450                                   -->
    <!-- ========================================================================= -->
    <rect class="container-db" x="10" y="450" width="1180" height="285"/>
    <text class="container-title-db" x="24" y="474">SQLite – data/app.db (13 bảng dữ liệu quản lý qua SQLAlchemy ORM 2.0)</text>

    <!-- 5 Cards for Table Domains -->
    <!-- Card 1: Người dùng & Phiên (3) -->
    <rect class="db-card" x="25" y="488" width="215" height="205"/>
    <text class="db-card-title" x="38" y="508">Người dùng &amp; Phiên (3)</text>
    <text class="db-card-table" x="38" y="528">users</text>
    <text class="db-card-table" x="38" y="546">auth_sessions</text>
    <text class="db-card-table" x="38" y="564">api_keys</text>

    <!-- Card 2: Nhật ký & Đo kiểm (2) -->
    <rect class="db-card" x="260" y="488" width="215" height="205"/>
    <text class="db-card-title" x="273" y="508">Nhật ký &amp; Viễn trắc (2)</text>
    <text class="db-card-table" x="273" y="528">translation_logs</text>
    <text class="db-card-table" x="273" y="546">pipeline_metrics</text>

    <!-- Card 3: Kiểm chuẩn & Audio (2) -->
    <rect class="db-card" x="495" y="488" width="215" height="205"/>
    <text class="db-card-title" x="508" y="508">Kiểm chuẩn &amp; Ngữ liệu (2)</text>
    <text class="db-card-table" x="508" y="528">quality_reviews</text>
    <text class="db-card-table" x="508" y="546">training_audio_assets</text>

    <!-- Card 4: MLOps & Huấn luyện (3) -->
    <rect class="db-card" x="730" y="488" width="215" height="205"/>
    <text class="db-card-title" x="743" y="508">MLOps &amp; Huấn luyện (3)</text>
    <text class="db-card-table" x="743" y="528">training_datasets</text>
    <text class="db-card-table" x="743" y="546">training_jobs</text>
    <text class="db-card-table" x="743" y="564">model_deployments</text>

    <!-- Card 5: Từ điển & Cấu hình (3) -->
    <rect class="db-card" x="965" y="488" width="210" height="205"/>
    <text class="db-card-title" x="978" y="508">Từ điển &amp; Cấu hình (3)</text>
    <text class="db-card-table" x="978" y="528">translation_memory_entries</text>
    <text class="db-card-table" x="978" y="546">system_settings</text>
    <text class="db-card-table" x="978" y="564">audit_logs</text>

    <!-- Footer Note inside Database Container -->
    <text class="db-footer-note" x="25" y="720">Hệ thống &amp; Tối ưu: WAL mode (Write-Ahead Logging), tuân thủ nghiêm ngặt tính toàn vẹn ACID, Single-file Zero-Config, lưu trữ cục bộ data/app.db không phụ thuộc cloud.</text>

  </svg>
</div>
</body>
</html>
"""

    tmp_html = OUT_PNG.parent / "temp_hinh_4_1.html"
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    cmd = [
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        "--window-size=1240,800",
        f"--screenshot={OUT_PNG}",
        str(tmp_html)
    ]
    subprocess.run(cmd, check=True)
    if tmp_html.exists():
        tmp_html.unlink()

    print(f"Successfully generated new architecture diagram at: {OUT_PNG}")

if __name__ == "__main__":
    generate_hinh_4_1_diagram()

