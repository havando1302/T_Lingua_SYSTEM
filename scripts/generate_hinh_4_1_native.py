# -*- coding: utf-8 -*-
"""
High-resolution diagram generator for T-Lingua Figure 4.1: System Architecture Diagram
Designed strictly following the visual style of the reference diagram (media_1793319243322_503dae78.jpg):
- Numbered circular badges (1, 2, 3, 4, 5, 6a, 6b, 7, 8, 9a, 9b, 10, 11)
- Color-coded components (blue load balancer, green app servers, orange database cylinder, yellow cache, red queue/job workers, purple services, cloud CDN)
- Native host deployment architecture (No Docker)
- Output to docs/img/hinh_4_1_kien_truc_trien_khai_he_thong.png
"""

import os
import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT_PNG = r"C:\Du_an\T_Langua_Test\docs\img\hinh_4_1_kien_truc_trien_khai_he_thong.png"

def generate_hinh_4_1():
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
    width: 1300px;
    height: 920px;
  }
  .container {
    width: 1260px;
    height: 880px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 20px 24px 16px 24px;
    box-shadow: 0 4px 25px rgba(0,0,0,0.06);
    position: relative;
  }
  .header-title {
    text-align: center;
    font-size: 19px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  svg {
    width: 100%;
    height: 810px;
  }
  /* Badge styling */
  .badge-circle {
    fill: #ede9fe;
    stroke: #8b5cf6;
    stroke-width: 1.5;
  }
  .badge-text {
    font-size: 11px;
    font-weight: 700;
    fill: #6d28d9;
    text-anchor: middle;
    dominant-baseline: central;
    font-family: inherit;
  }
</style>
</head>
<body>
<div class="container">
  <div class="header-title">SƠ ĐỒ KIẾN TRÚC TRIỂN KHAI TỔNG THỂ HỆ THỐNG T-LINGUA</div>
  <svg viewBox="0 0 1200 780">
    <defs>
      <!-- Shadow filter -->
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
        <feDropShadow dx="1" dy="2" stdDeviation="2.5" flood-opacity="0.08"/>
      </filter>
      <!-- Arrow markers -->
      <marker id="arr" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#334155"/>
      </marker>
      <marker id="arrBlue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#2563eb"/>
      </marker>
      <marker id="arrPurple" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#7c3aed"/>
      </marker>

      <!-- Gradients -->
      <linearGradient id="gradDns" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#f8fafc"/>
        <stop offset="100%" stop-color="#f1f5f9"/>
      </linearGradient>
      <linearGradient id="gradClients" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#ffffff"/>
        <stop offset="100%" stop-color="#f8fafc"/>
      </linearGradient>
      <linearGradient id="gradLB" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#e0f2fe"/>
        <stop offset="100%" stop-color="#bae6fd"/>
      </linearGradient>
      <linearGradient id="gradApp" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#ecfdf5"/>
        <stop offset="100%" stop-color="#d1fae5"/>
      </linearGradient>
      <linearGradient id="gradDb" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#ffedd5"/>
        <stop offset="100%" stop-color="#fed7aa"/>
      </linearGradient>
      <linearGradient id="gradCache" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#fef9c3"/>
        <stop offset="100%" stop-color="#fef08a"/>
      </linearGradient>
      <linearGradient id="gradQueue" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#ffe4e6"/>
        <stop offset="100%" stop-color="#fecdd3"/>
      </linearGradient>
      <linearGradient id="gradWorker" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#ffe4e6"/>
        <stop offset="100%" stop-color="#fecdd3"/>
      </linearGradient>
      <linearGradient id="gradPurple" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#f3e8ff"/>
        <stop offset="100%" stop-color="#e9d5ff"/>
      </linearGradient>
      <linearGradient id="gradStorage" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#e0e7ff"/>
        <stop offset="100%" stop-color="#c7d2fe"/>
      </linearGradient>
      <linearGradient id="gradWarehouse" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#e2e8f0"/>
        <stop offset="100%" stop-color="#cbd5e1"/>
      </linearGradient>
    </defs>

    <!-- ======================================================== -->
    <!-- 1. TOP SECTION: CLIENTS, DNS, CDN (ABOVE DASHED LINE)     -->
    <!-- ======================================================== -->

    <!-- (1) DNS -->
    <g transform="translate(60, 25)" filter="url(#shadow)">
      <rect x="0" y="0" width="180" height="55" rx="6" fill="url(#gradDns)" stroke="#94a3b8" stroke-width="1.5"/>
      <text x="90" y="26" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">DNS / Route 53</text>
      <text x="90" y="43" text-anchor="middle" font-size="10.5" fill="#64748b">Phân giải tên miền</text>
      <!-- Badge 1 -->
      <circle cx="-6" cy="27" r="13" class="badge-circle"/>
      <text x="-6" y="27" class="badge-text">1</text>
    </g>

    <!-- Arrow DNS <-> Users -->
    <path d="M 240 52 L 340 52" stroke="#334155" stroke-width="1.5" marker-end="url(#arr)" marker-start="url(#arr)"/>

    <!-- (2) User Clients: Mobile App & Web Browser -->
    <g transform="translate(340, 15)" filter="url(#shadow)">
      <rect x="0" y="0" width="310" height="75" rx="8" fill="url(#gradClients)" stroke="#475569" stroke-width="2"/>
      <text x="155" y="24" text-anchor="middle" font-size="13.5" font-weight="700" fill="#0f172a">Người dùng & Thiết bị đầu cuối</text>
      <rect x="12" y="36" width="138" height="30" rx="4" fill="#eff6ff" stroke="#93c5fd"/>
      <text x="81" y="55" text-anchor="middle" font-size="11" font-weight="600" fill="#1d4ed8">Flutter Mobile App</text>
      <rect x="158" y="36" width="138" height="30" rx="4" fill="#f0fdf4" stroke="#86efac"/>
      <text x="227" y="55" text-anchor="middle" font-size="11" font-weight="600" fill="#166534">React 18 Web Admin</text>
      <!-- Badge 2 -->
      <circle cx="-8" cy="37" r="13" class="badge-circle"/>
      <text x="-8" y="37" class="badge-text">2</text>
    </g>

    <!-- (11) CDN (Cloud shape) -->
    <g transform="translate(770, 15)" filter="url(#shadow)">
      <path d="M 40,48 
               a 24,24 0 0,1 20,-36 
               a 32,32 0 0,1 55,-10 
               a 30,30 0 0,1 45,18 
               a 26,26 0 0,1 25,28 
               a 22,22 0 0,1 -15,22 
               l -115,0 
               a 22,22 0 0,1 -15,-22 z" 
            fill="#ffffff" stroke="#94a3b8" stroke-width="1.8"/>
      <text x="115" y="44" text-anchor="middle" font-size="13" font-weight="700" fill="#1e293b">Static CDN</text>
      <text x="115" y="58" text-anchor="middle" font-size="10" fill="#64748b">Web Assets & Audio Caching</text>
      <!-- Badge 11 -->
      <circle cx="20" cy="30" r="13" class="badge-circle"/>
      <text x="20" y="30" class="badge-text">11</text>
    </g>

    <!-- Arrow Clients <-> CDN -->
    <path d="M 650 52 L 770 52" stroke="#334155" stroke-width="1.5" marker-end="url(#arr)" marker-start="url(#arr)"/>

    <!-- ======================================================== -->
    <!-- DASHED BOUNDARY LINE (INTERNET vs HOST RUNTIME)          -->
    <!-- ======================================================== -->
    <line x1="40" y1="110" x2="1160" y2="110" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="6,5"/>
    <text x="60" y="104" font-size="11" font-weight="600" fill="#64748b" letter-spacing="0.5">INTERNET / MẠNG CÔNG CỘNG (PUBLIC ZONE)</text>
    <text x="1140" y="125" text-anchor="end" font-size="11" font-weight="600" fill="#475569" letter-spacing="0.5">HẠ TẦNG MÁY CHỦ BẢN ĐỊA (NATIVE HOST RUNTIME)</text>

    <!-- ======================================================== -->
    <!-- 2. REVERSE PROXY & LOAD BALANCER                          -->
    <!-- ======================================================== -->
    <!-- Arrow User -> Load Balancer -->
    <path d="M 495 90 L 495 145" stroke="#334155" stroke-width="2" marker-end="url(#arr)"/>

    <!-- Arrow CDN -> Load Balancer -->
    <path d="M 800 75 L 800 130 L 610 160" stroke="#64748b" stroke-width="1.2" stroke-dasharray="4,4" fill="none" marker-end="url(#arr)"/>

    <!-- (3) Reverse Proxy / Load Balancer -->
    <g transform="translate(385, 145)" filter="url(#shadow)">
      <rect x="0" y="0" width="220" height="55" rx="8" fill="url(#gradLB)" stroke="#0284c7" stroke-width="1.8"/>
      <text x="110" y="24" text-anchor="middle" font-size="13.5" font-weight="700" fill="#0369a1">Nginx Reverse Proxy</text>
      <text x="110" y="42" text-anchor="middle" font-size="10.5" fill="#0284c7">WSS & HTTPS SSL Termination</text>
      <!-- Badge 3 -->
      <circle cx="-8" cy="27" r="13" class="badge-circle"/>
      <text x="-8" y="27" class="badge-text">3</text>
    </g>

    <!-- Arrow LB <-> Web App Servers -->
    <path d="M 495 200 L 495 250" stroke="#334155" stroke-width="2" marker-end="url(#arr)" marker-start="url(#arr)"/>

    <!-- ======================================================== -->
    <!-- 3. CENTRAL WEB APP SERVERS (FASTAPI)                     -->
    <!-- ======================================================== -->
    <!-- Dashed Container for Web App Servers -->
    <rect x="345" y="240" width="300" height="175" rx="10" fill="none" stroke="#059669" stroke-width="1.5" stroke-dasharray="5,4"/>

    <!-- Stacked Server Cards -->
    <!-- Card 3 (back) -->
    <rect x="385" y="255" width="240" height="145" rx="8" fill="#d1fae5" stroke="#10b981" stroke-width="1.5" opacity="0.6"/>
    <!-- Card 2 (middle) -->
    <rect x="375" y="263" width="240" height="145" rx="8" fill="#a7f3d0" stroke="#059669" stroke-width="1.5" opacity="0.8"/>
    <!-- Card 1 (front) -->
    <g transform="translate(365, 270)" filter="url(#shadow)">
      <rect x="0" y="0" width="240" height="135" rx="8" fill="url(#gradApp)" stroke="#047857" stroke-width="2"/>
      <text x="120" y="26" text-anchor="middle" font-size="14" font-weight="700" fill="#064e3b">FastAPI Backend Server</text>
      <text x="120" y="44" text-anchor="middle" font-size="11" font-weight="600" fill="#047857">Python 3.10+ / Uvicorn ASGI</text>
      <line x1="15" y1="52" x2="225" y2="52" stroke="#6ee7b7" stroke-width="1"/>
      <text x="25" y="70" font-size="10.5" fill="#065f46">• SessionActor (Quản lý phiên đàm thoại)</text>
      <text x="25" y="87" font-size="10.5" fill="#065f46">• WebRTC VAD (Ngắt câu tự động 500ms)</text>
      <text x="25" y="104" font-size="10.5" fill="#065f46">• Khóa tương hỗ Dual-Mic Mutex Lock</text>
      <text x="25" y="121" font-size="10.5" fill="#065f46">• REST API: Auth, RBAC, QA & Telemetry</text>
    </g>

    <!-- Badge 4 for Web App Server -->
    <circle cx="340" cy="255" r="13" class="badge-circle"/>
    <text x="340" y="255" class="badge-text">4</text>

    <!-- ======================================================== -->
    <!-- 4. LEFT SIDE: DATABASE & CACHING                         -->
    <!-- ======================================================== -->
    <!-- (5) Database (Cylinder) -->
    <g transform="translate(70, 245)" filter="url(#shadow)">
      <!-- Cylinder Body -->
      <path d="M 0,22 
               L 0,65 
               a 95,22 0 0,0 190,0 
               L 190,22 
               z" fill="url(#gradDb)" stroke="#ea580c" stroke-width="1.8"/>
      <!-- Cylinder Top Oval -->
      <ellipse cx="95" cy="22" rx="95" ry="22" fill="#ffedd5" stroke="#ea580c" stroke-width="1.8"/>
      <text x="95" y="32" text-anchor="middle" font-size="13.5" font-weight="700" fill="#9a3412">Relational Database</text>
      <text x="95" y="58" text-anchor="middle" font-size="11" font-weight="600" fill="#c2410c">PostgreSQL 16 / SQLite</text>
      <text x="95" y="75" text-anchor="middle" font-size="9.5" fill="#9a3412">Users, RBAC, Logs, QA Reviews</text>
      <!-- Badge 5 -->
      <circle cx="-8" cy="22" r="13" class="badge-circle"/>
      <text x="-8" y="22" class="badge-text">5</text>
    </g>

    <!-- Arrow App Server <-> Database -->
    <path d="M 345 315 L 260 315" stroke="#334155" stroke-width="1.8" marker-end="url(#arr)" marker-start="url(#arr)"/>

    <!-- (6) In-Memory Caching & TM -->
    <g transform="translate(70, 365)" filter="url(#shadow)">
      <rect x="0" y="0" width="190" height="60" rx="8" fill="url(#gradCache)" stroke="#ca8a04" stroke-width="1.8"/>
      <text x="95" y="25" text-anchor="middle" font-size="13" font-weight="700" fill="#854d0e">Caching & Translation Memory</text>
      <text x="95" y="44" text-anchor="middle" font-size="10.5" fill="#a16207">Redis 7.2 / Bộ nhớ đệm RAM</text>
      <text x="95" y="56" text-anchor="middle" font-size="9" fill="#713f12">Khóa Mutex, TM Hash SHA-256 (&lt;5ms)</text>
      <!-- Badge 6 -->
      <circle cx="-8" cy="30" r="13" class="badge-circle"/>
      <text x="-8" y="30" class="badge-text">6</text>
    </g>

    <!-- Arrow App Server <-> Caching -->
    <path d="M 365 375 L 310 375 L 310 395 L 260 395" stroke="#334155" stroke-width="1.8" fill="none" marker-end="url(#arr)" marker-start="url(#arr)"/>

    <!-- ======================================================== -->
    <!-- 5. BOTTOM SECTION: JOB QUEUE & AI WORKERS, GLOSSARY      -->
    <!-- ======================================================== -->
    <!-- (7a) Job Queue (Audio & Pipeline Queue) -->
    <g transform="translate(385, 450)" filter="url(#shadow)">
      <!-- Vertical cylinder shape -->
      <path d="M 0,15 
               L 0,55 
               a 35,12 0 0,0 70,0 
               L 70,15 
               z" fill="url(#gradQueue)" stroke="#e11d48" stroke-width="1.8"/>
      <ellipse cx="35" cy="15" rx="35" ry="12" fill="#ffe4e6" stroke="#e11d48" stroke-width="1.8"/>
      <text x="35" y="38" text-anchor="middle" font-size="11" font-weight="700" fill="#9f1239">Audio</text>
      <text x="35" y="52" text-anchor="middle" font-size="10" font-weight="700" fill="#9f1239">Queue</text>
      <!-- Badge 7a -->
      <circle cx="-6" cy="15" r="13" class="badge-circle"/>
      <text x="-6" y="15" class="badge-text" font-size="9.5">7a</text>
    </g>

    <!-- Arrow App Server <-> Queue -->
    <path d="M 420 415 L 420 450" stroke="#334155" stroke-width="1.8" marker-end="url(#arr)" marker-start="url(#arr)"/>

    <!-- (7b) AI Pipeline Workers -->
    <!-- Dashed Container -->
    <rect x="235" y="560" width="370" height="185" rx="10" fill="none" stroke="#e11d48" stroke-width="1.5" stroke-dasharray="5,4"/>

    <!-- Stacked Worker Cards -->
    <rect x="265" y="575" width="320" height="155" rx="8" fill="#fecdd3" stroke="#f43f5e" stroke-width="1.5" opacity="0.6"/>
    <rect x="255" y="583" width="320" height="155" rx="8" fill="#fda4af" stroke="#e11d48" stroke-width="1.5" opacity="0.8"/>
    <!-- Front Card -->
    <g transform="translate(245, 590)" filter="url(#shadow)">
      <rect x="0" y="0" width="320" height="145" rx="8" fill="url(#gradWorker)" stroke="#be123c" stroke-width="2"/>
      <text x="160" y="24" text-anchor="middle" font-size="13.5" font-weight="700" fill="#881337">AI Inference Engine Workers</text>
      <text x="160" y="40" text-anchor="middle" font-size="10.5" font-weight="600" fill="#9f1239">GPU CUDA 12.2 / Native Process Pool</text>
      <line x1="15" y1="48" x2="305" y2="48" stroke="#f43f5e" stroke-width="1"/>
      <text x="20" y="66" font-size="11" font-weight="700" fill="#9f1239">• STT Worker: <tspan font-weight="400" fill="#1e293b">faster-whisper (CTranslate2 INT8)</tspan></text>
      <text x="20" y="86" font-size="11" font-weight="700" fill="#9f1239">• MT Worker: <tspan font-weight="400" fill="#1e293b">NLLB-200 1.3B (LoRA Adapter PEFT)</tspan></text>
      <text x="20" y="106" font-size="11" font-weight="700" fill="#9f1239">• TTS Worker: <tspan font-weight="400" fill="#1e293b">Piper VITS (ONNX Runtime 16kHz)</tspan></text>
      <text x="20" y="126" font-size="10" font-style="italic" fill="#881337">Độ trễ trung bình đường ống toàn trình: 584 ms (&lt; 1s)</text>
    </g>

    <!-- Badge 7b -->
    <circle cx="230" cy="570" r="13" class="badge-circle"/>
    <text x="230" y="570" class="badge-text" font-size="9.5">7b</text>

    <!-- Arrow Queue <-> Workers -->
    <path d="M 420 520 L 420 560" stroke="#334155" stroke-width="1.8" marker-end="url(#arr)" marker-start="url(#arr)"/>

    <!-- (8) Glossary & Full-Text Search Service -->
    <g transform="translate(640, 590)" filter="url(#shadow)">
      <rect x="0" y="0" width="220" height="85" rx="8" fill="url(#gradPurple)" stroke="#7c3aed" stroke-width="1.8"/>
      <text x="110" y="24" text-anchor="middle" font-size="13" font-weight="700" fill="#5b21b6">Glossary & Search Service</text>
      <text x="110" y="42" text-anchor="middle" font-size="10.5" fill="#6d28d9">Đối sánh từ điển chuyên ngành</text>
      <line x1="15" y1="50" x2="205" y2="50" stroke="#c4b5fd" stroke-width="1"/>
      <text x="110" y="66" text-anchor="middle" font-size="10" fill="#4c1d95">Aho-Corasick Multi-Pattern Search</text>
      <text x="110" y="79" text-anchor="middle" font-size="9" fill="#5b21b6">Ràng buộc dịch chuẩn thuật ngữ (100% số)</text>
      <!-- Badge 8 -->
      <circle cx="-8" cy="25" r="13" class="badge-circle"/>
      <text x="-8" y="25" class="badge-text">8</text>
    </g>

    <!-- Arrow App Server <-> Glossary -->
    <path d="M 540 415 L 540 500 L 710 500 L 710 590" stroke="#334155" stroke-width="1.8" fill="none" marker-end="url(#arr)" marker-start="url(#arr)"/>

    <!-- ======================================================== -->
    <!-- 6. RIGHT SIDE: TELEMETRY, STORAGE, DATA WAREHOUSE & MLOPS -->
    <!-- ======================================================== -->
    <!-- (9a) Telemetry "Firehose" Stream (Stacked horizontal cylinders) -->
    <g transform="translate(730, 260)" filter="url(#shadow)">
      <!-- Cylinder 3 (back) -->
      <g transform="translate(16, 0)">
        <path d="M 0,8 L 45,8 a 8,14 0 0,0 0,28 L 0,36 z" fill="#f1f5f9" stroke="#64748b" stroke-width="1.2"/>
        <ellipse cx="0" cy="22" rx="8" ry="14" fill="#e2e8f0" stroke="#64748b" stroke-width="1.2"/>
      </g>
      <!-- Cylinder 2 (middle) -->
      <g transform="translate(8, 12)">
        <path d="M 0,8 L 45,8 a 8,14 0 0,0 0,28 L 0,36 z" fill="#f1f5f9" stroke="#64748b" stroke-width="1.2"/>
        <ellipse cx="0" cy="22" rx="8" ry="14" fill="#e2e8f0" stroke="#64748b" stroke-width="1.2"/>
      </g>
      <!-- Cylinder 1 (front) -->
      <g transform="translate(0, 24)">
        <path d="M 0,8 L 45,8 a 8,14 0 0,0 0,28 L 0,36 z" fill="#f8fafc" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="0" cy="22" rx="8" ry="14" fill="#ffffff" stroke="#334155" stroke-width="1.5"/>
      </g>
      <text x="65" y="32" font-size="12" font-weight="700" fill="#1e293b">Telemetry &</text>
      <text x="65" y="47" font-size="12" font-weight="700" fill="#1e293b">Audit Logs</text>
      <text x="65" y="61" font-size="9.5" fill="#64748b">Event Stream</text>
      <!-- Badge 9a -->
      <circle cx="-10" cy="35" r="13" class="badge-circle"/>
      <text x="-10" y="35" class="badge-text" font-size="9.5">9a</text>
    </g>

    <!-- Arrow App Server -> Telemetry Stream -->
    <path d="M 645 315 L 720 315" stroke="#334155" stroke-width="1.8" marker-end="url(#arr)"/>

    <!-- (9b) Storage (Stacked Disks) -->
    <g transform="translate(930, 150)" filter="url(#shadow)">
      <!-- Disk 3 (bottom) -->
      <ellipse cx="100" cy="55" rx="100" ry="18" fill="#c7d2fe" stroke="#4338ca" stroke-width="1.5"/>
      <path d="M 0,38 L 0,55 a 100,18 0 0,0 200,0 L 200,38 z" fill="#e0e7ff" stroke="#4338ca" stroke-width="1.5"/>
      <!-- Disk 2 (middle) -->
      <ellipse cx="100" cy="38" rx="100" ry="18" fill="#c7d2fe" stroke="#4338ca" stroke-width="1.5"/>
      <path d="M 0,20 L 0,38 a 100,18 0 0,0 200,0 L 200,20 z" fill="#e0e7ff" stroke="#4338ca" stroke-width="1.5"/>
      <!-- Disk 1 (top) -->
      <ellipse cx="100" cy="20" rx="100" ry="18" fill="#e0e7ff" stroke="#4338ca" stroke-width="1.8"/>
      <text x="100" y="25" text-anchor="middle" font-size="13" font-weight="700" fill="#312e81">Audio Asset & Model Storage</text>
      <text x="100" y="48" text-anchor="middle" font-size="10.5" fill="#3730a3">Lưu trữ Tệp Âm thanh WAV & Trọng số LoRA</text>
      <text x="100" y="66" text-anchor="middle" font-size="9" fill="#4338ca">Hệ thống tệp cục bộ NVMe / Object Storage</text>
      <!-- Badge 9b -->
      <circle cx="-10" cy="20" r="13" class="badge-circle"/>
      <text x="-10" y="20" class="badge-text" font-size="9.5">9b</text>
    </g>

    <!-- Arrow Telemetry -> Storage (Copy of audio/models) -->
    <path d="M 865 290 L 980 290 L 980 230" stroke="#334155" stroke-width="1.5" fill="none" marker-end="url(#arr)"/>
    <text x="915" y="280" font-size="10" font-weight="600" fill="#475569">Lưu trữ tệp</text>

    <!-- Arrow Storage <-> CDN -->
    <path d="M 980 150 L 980 75 L 890 55" stroke="#334155" stroke-width="1.5" fill="none" marker-end="url(#arr)" marker-start="url(#arr)"/>

    <!-- (10) Data Warehouse & MLOps Training (Stacked Large Cylinders) -->
    <g transform="translate(900, 340)" filter="url(#shadow)">
      <!-- Cylinder 3 (back) -->
      <g transform="translate(40, 0)">
        <path d="M 0,20 L 0,80 a 85,20 0 0,0 170,0 L 170,20 z" fill="#cbd5e1" stroke="#475569" stroke-width="1.2"/>
        <ellipse cx="85" cy="20" rx="85" ry="20" fill="#e2e8f0" stroke="#475569" stroke-width="1.2"/>
      </g>
      <!-- Cylinder 2 (middle) -->
      <g transform="translate(20, 15)">
        <path d="M 0,20 L 0,80 a 85,20 0 0,0 170,0 L 170,20 z" fill="#cbd5e1" stroke="#475569" stroke-width="1.2"/>
        <ellipse cx="85" cy="20" rx="85" ry="20" fill="#e2e8f0" stroke="#475569" stroke-width="1.2"/>
      </g>
      <!-- Cylinder 1 (front) -->
      <g transform="translate(0, 30)">
        <path d="M 0,20 L 0,80 a 85,20 0 0,0 170,0 L 170,20 z" fill="url(#gradWarehouse)" stroke="#1e293b" stroke-width="1.8"/>
        <ellipse cx="85" cy="20" rx="85" ry="20" fill="#f8fafc" stroke="#1e293b" stroke-width="1.8"/>
        <text x="85" y="32" text-anchor="middle" font-size="13" font-weight="700" fill="#0f172a">MLOps Training & QA Data</text>
        <text x="85" y="55" text-anchor="middle" font-size="10.5" font-weight="600" fill="#1e293b">Kho Dữ liệu Vàng MQM</text>
        <text x="85" y="70" text-anchor="middle" font-size="9.5" fill="#475569">Trung tâm Huấn luyện Tinh chỉnh LoRA</text>
        <text x="85" y="85" text-anchor="middle" font-size="9" fill="#0f172a">Freeze Dataset & Canary Rollout</text>
      </g>
      <!-- Badge 10 -->
      <circle cx="-10" cy="50" r="13" class="badge-circle"/>
      <text x="-10" y="50" class="badge-text">10</text>
    </g>

    <!-- Arrow Telemetry -> Data Warehouse -->
    <path d="M 865 330 L 900 370" stroke="#334155" stroke-width="1.8" marker-end="url(#arr)"/>

    <!-- Arrow Data Warehouse (LoRA weights) -> Workers (Canary Hot-swapping) -->
    <path d="M 900 450 L 820 450 L 820 540 L 580 540 L 580 590" stroke="#7c3aed" stroke-width="1.8" stroke-dasharray="5,4" fill="none" marker-end="url(#arrPurple)"/>
    <text x="800" y="532" text-anchor="middle" font-size="10" font-weight="700" fill="#6d28d9">Nạp nóng LoRA Adapter (Canary Deploy)</text>

    <!-- ======================================================== -->
    <!-- FOOTER LEGEND / NOTE                                     -->
    <!-- ======================================================== -->
    <rect x="50" y="745" width="1100" height="28" rx="6" fill="#f8fafc" stroke="#e2e8f0"/>
    <text x="70" y="763" font-size="10.5" fill="#475569"><tspan font-weight="700">Chú thích kiến trúc:</tspan> Toàn bộ hệ thống chạy trực tiếp trên môi trường máy chủ bản địa (Native Host Runtime: Linux/Windows, Python 3.10+, NVIDIA CUDA 12.2), tối ưu hóa truyền thông inter-process và GPU Direct Access không thông qua lớp ảo hóa container.</text>
  </svg>
</div>
</body>
</html>"""

    tmp_html = OUT_PNG.replace(".png", "_temp.html")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html)
    
    cmd = [
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        f"--window-size=1300,920",
        f"--screenshot={OUT_PNG}",
        tmp_html
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if os.path.exists(tmp_html):
        os.remove(tmp_html)
    print(f"Rendered new native architecture diagram: {OUT_PNG}")

if __name__ == "__main__":
    generate_hinh_4_1()

