<div align="center">

# 🌐 T-Lingua

**Hệ thống dịch thuật thời gian thực hỗ trợ AI — Speech-to-Speech**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?logo=flutter&logoColor=white)](https://flutter.dev)
[![React](https://img.shields.io/badge/React-Vite-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-Private-red)](#)

</div>

---

## 📖 Tổng quan

**T-Lingua** là hệ thống dịch thuật thời gian thực từ giọng nói sang giọng nói (Speech-to-Speech), được xây dựng hoàn toàn trên nền tảng AI mã nguồn mở. Hệ thống có khả năng nhận âm thanh trực tiếp từ người dùng, nhận diện giọng nói, dịch thuật, và tổng hợp lại thành giọng đọc trong vòng **vài trăm mili-giây**.

### 🎯 Mục tiêu

- Phục vụ giao tiếp đa ngôn ngữ thời gian thực (Việt–Anh, có thể mở rộng)
- Hoạt động hoàn toàn **on-premise** — không phụ thuộc cloud API
- Hiệu suất cao với GPU, nhẹ cho CPU khi cần
- Kiến trúc modular, dễ tích hợp và mở rộng

---

## ✨ Tính năng nổi bật

| Tính năng | Mô tả |
|-----------|-------|
| 🎤 **STT (Speech-to-Text)** | Nhận diện giọng nói bằng Whisper (faster-whisper / openai/whisper-large-v3-turbo) |
| 🔇 **Khử nhiễu âm thanh** | DeepFilterNet — lọc tiếng ồn nền trước khi nhận diện |
| 🌐 **Dịch thuật NLLB** | Facebook NLLB-200 distilled 1.3B — dịch Việt ↔ Anh chất lượng cao |
| 🔊 **TTS (Text-to-Speech)** | VITS MMS — giọng đọc tự nhiên cho tiếng Anh và tiếng Việt |
| ⚡ **Pipeline bất đồng bộ** | STT → Translate → TTS chạy song song qua async worker pool |
| 🗂️ **Translation Memory** | Cache dịch thuật thông minh — tránh dịch lại câu đã biết |
| 📊 **Telemetry pipeline** | Đo độ trễ P50/P90/P99 cho từng giai đoạn: queue, STT, translate, TTS |
| 🔐 **Xác thực JWT + MFA** | Guest token, tài khoản đặc quyền yêu cầu TOTP 2FA |
| 🖥️ **Admin Dashboard** | Giao diện web React để quản trị hệ thống, xem metrics, cấu hình |
| 📱 **Mobile App Flutter** | Ứng dụng di động cross-platform (Android, iOS, Windows, Linux) |
| 🐳 **Docker hóa hoàn toàn** | Triển khai một lệnh với Docker Compose |

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           T-Lingua System                               │
│                                                                         │
│  ┌─────────────┐    WebSocket    ┌──────────────────────────────────┐  │
│  │ Flutter App │◄───────────────►│         FastAPI Backend          │  │
│  │ (Mobile)    │                 │                                  │  │
│  └─────────────┘                 │  ┌──────────────────────────┐   │  │
│                                  │  │    AI Pipeline (async)   │   │  │
│  ┌─────────────┐    HTTP/REST    │  │                          │   │  │
│  │ Admin Web   │◄───────────────►│  │  Audio ──► STT Worker   │   │  │
│  │ (React/Vite)│                 │  │            │             │   │  │
│  └─────────────┘                 │  │            ▼             │   │  │
│                                  │  │     Translate Worker     │   │  │
│                                  │  │            │             │   │  │
│                                  │  │            ▼             │   │  │
│                                  │  │       TTS Worker ──► 🔊 │   │  │
│                                  │  └──────────────────────────┘   │  │
│                                  │                                  │  │
│                                  │  ┌──────────┐  ┌─────────────┐  │  │
│                                  │  │ SQLite   │  │ Translation │  │  │
│                                  │  │ Database │  │ Memory JSON │  │  │
│                                  │  └──────────┘  └─────────────┘  │  │
│                                  └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Cấu trúc thư mục

```
T_Langua_Test/
├── backend/                        # FastAPI backend + AI pipeline
│   ├── app/
│   │   ├── ai/                     # ModelManager — quản lý Whisper, NLLB, VITS
│   │   ├── api/                    # REST & WebSocket routes
│   │   │   ├── routes.py           # API chính (upload, session, v.v.)
│   │   │   ├── admin_routes.py     # Endpoint quản trị
│   │   │   ├── auth_routes.py      # Xác thực JWT
│   │   │   ├── training_routes.py  # Fine-tuning & training control
│   │   │   └── websocket.py        # WebSocket realtime session
│   │   ├── core/                   # Cấu hình, telemetry, GPU manager
│   │   ├── db/                     # SQLAlchemy models & migration
│   │   ├── models/                 # Domain models (Session, Turn)
│   │   ├── services/               # Business logic (STT, TTS, Translation, VAD…)
│   │   ├── workers/                # Async worker pool (stt, translate, tts)
│   │   └── main.py                 # FastAPI app entrypoint
│   ├── training/                   # Script huấn luyện mô hình tùy chỉnh
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                       # Flutter cross-platform mobile app
│   └── lib/
│       ├── controllers/            # State & logic controllers
│       ├── services/               # WebSocket, audio, API services
│       ├── ui/                     # Widgets & screens
│       └── main.dart
│
├── admin_web/                      # React + Vite admin dashboard
│   └── src/
│
├── scripts/                        # Utility scripts
│   ├── backup_restore.py           # Sao lưu / phục hồi DB + TM
│   ├── run_translation_benchmark.py
│   ├── run_speech_benchmark_v2.py
│   ├── run_automated_e2e_qa.py
│   └── run_deep_chaos_100_matrix.py
│
├── docs/                           # Tài liệu dự án & kế hoạch
├── docker-compose.yml              # Orchestration toàn hệ thống
└── README.md
```

---

## 🤖 Các mô hình AI sử dụng

| Thành phần | Mô hình | Mục đích |
|------------|---------|----------|
| **STT** | `openai/whisper-large-v3-turbo` (GPU) / `faster-whisper small` (CPU) | Nhận diện giọng nói đa ngôn ngữ |
| **Dịch thuật** | `facebook/nllb-200-distilled-1.3B` | Dịch thuật chất lượng cao Việt ↔ Anh |
| **TTS Tiếng Anh** | `facebook/mms-tts-eng` | Tổng hợp giọng đọc tiếng Anh |
| **TTS Tiếng Việt** | `facebook/mms-tts-vie` | Tổng hợp giọng đọc tiếng Việt |
| **Khử nhiễu** | `DeepFilterNet` | Lọc nhiễu nền âm thanh đầu vào |

> Tất cả mô hình đều được tải về và chạy **hoàn toàn cục bộ** — không gọi API bên ngoài.

---

## 🔄 Luồng xử lý thời gian thực

```
Người dùng nói
      │
      ▼
 [WebSocket]  ──PCM 16kHz──►  VAD (WebRTC) ──► DeepFilterNet (khử nhiễu)
                                                        │
                                                        ▼
                                              STT Worker (Whisper)
                                                        │
                                              "Xin chào, bạn khỏe không?"
                                                        │
                                                        ▼
                                           Translation Worker (NLLB)
                                           [Translation Memory cache]
                                                        │
                                              "Hello, how are you?"
                                                        │
                                                        ▼
                                             TTS Worker (VITS MMS)
                                                        │
                                                  🔊 Audio WAV
                                                        │
                                                        ▼
                                           [WebSocket] ──► Flutter App
```

**Telemetry** được đo cho từng bước: `queue_wait` → `stt` → `translate` → `tts_first_chunk` → `tts_total` → `end_to_end` với thống kê **P50 / P90 / P99**.

---

## 🚀 Cài đặt & Khởi chạy

### Yêu cầu hệ thống

- **Docker & Docker Compose** (khuyến nghị)
- **GPU NVIDIA** với CUDA 12+ (tùy chọn, tăng tốc đáng kể)
- RAM tối thiểu: 8 GB (16 GB+ khuyến nghị khi dùng GPU)
- Python 3.11+ (nếu chạy thủ công)

---

### ▶️ Cách 1: Docker Compose (Khuyến nghị)

```bash
# 1. Clone repo
git clone <repo-url>
cd T_Langua_Test

# 2. Tạo file cấu hình backend
cp backend/.env.example backend/.env
# Chỉnh sửa backend/.env theo môi trường của bạn

# 3. Khởi chạy toàn bộ hệ thống
docker compose up -d

# Backend API:      http://127.0.0.1:8000
# Admin Dashboard:  http://127.0.0.1:8080
```

---

### ▶️ Cách 2: Chạy thủ công (Development)

#### Backend

```bash
cd backend

# Tạo và kích hoạt môi trường ảo
python -m venv venv
venv\Scripts\activate           # Windows
# source venv/bin/activate      # Linux/Mac

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình môi trường
cp .env.example .env
# Mở .env và điền các giá trị cần thiết

# Khởi chạy server
python run.py
```

#### Admin Dashboard

```bash
cd admin_web
npm install
npm run dev
# Mở http://localhost:5173
```

#### Flutter App

```bash
cd frontend
flutter pub get
flutter run
```

---

## ⚙️ Cấu hình chính (`backend/.env`)

| Biến | Mặc định | Mô tả |
|------|---------|-------|
| `APP_ENV` | `local` | Môi trường: `local` / `colab` / `production` |
| `DEVICE` | `auto` | Thiết bị AI: `auto` / `cuda` / `cpu` |
| `WHISPER_MODEL` | `small` | Model Whisper fallback (CPU) |
| `WHISPER_TORCH_MODEL` | `openai/whisper-large-v3-turbo` | Model Whisper GPU |
| `NLLB_MODEL` | `facebook/nllb-200-distilled-1.3B` | Model dịch thuật |
| `TTS_MODEL_ENG` | `facebook/mms-tts-eng` | TTS tiếng Anh |
| `TTS_MODEL_VIE` | `facebook/mms-tts-vie` | TTS tiếng Việt |
| `ENABLE_DEEPFILTER` | `true` | Bật/tắt khử nhiễu DeepFilterNet |
| `PREWARM_MODELS` | `true` | Chạy warm-up khi khởi động |
| `STT_WORKER_POOL_SIZE` | `2` | Số worker STT song song |
| `TRANSLATION_WORKER_POOL_SIZE` | `2` | Số worker dịch thuật song song |
| `TTS_WORKER_POOL_SIZE` | `1` | Số worker TTS song song |
| `JWT_SECRET_KEY` | *(bắt buộc)* | Khóa bí mật JWT |
| `AUTH_REQUIRE_PRIVILEGED_MFA` | `true` | Yêu cầu TOTP cho admin |
| `MAX_WS_CONNECTIONS` | `8` | Số kết nối WebSocket đồng thời tối đa |
| `RATE_LIMIT_RPM` | `60` | Giới hạn request/phút |

---

## 🔐 Bảo mật

- **JWT Authentication** với access token ngắn hạn (15 phút mặc định)
- **Guest sessions** — giới hạn 500 phiên khách đồng thời
- **TOTP MFA** bắt buộc cho tài khoản có đặc quyền (RFC 6238)
- **Fernet encryption** bảo vệ khóa MFA lưu trữ
- **CORS** kiểm soát nghiêm ngặt theo danh sách trắng
- **TrustedHost middleware** chặn request từ host không hợp lệ
- **Rate limiting**: 60 req/phút, tối đa 8 WebSocket đồng thời
- **Payload limits**: audio 1 MB, text 5.000 ký tự, message 16 KB

---

## 📊 API Endpoints chính

### WebSocket — Realtime Translation

```
ws://localhost:8000/ws/translate
```

### REST API

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/api/v1/health` | Trạng thái hệ thống & models |
| `POST` | `/auth/guest` | Tạo guest token |
| `POST` | `/auth/login` | Đăng nhập tài khoản |
| `GET` | `/admin/system/status` | Trạng thái runtime chi tiết |
| `GET` | `/admin/metrics` | Telemetry P50/P90/P99 toàn pipeline |
| `GET` | `/admin/translation-memory` | Quản lý bộ nhớ dịch thuật |
| `POST` | `/training/start` | Khởi động fine-tuning model |
| `GET` | `/training/status` | Trạng thái quá trình huấn luyện |

---

## 💾 Sao lưu & Phục hồi

```bash
# Tạo backup (DB + Translation Memory)
python scripts/backup_restore.py backup --output-dir ./backups

# Phục hồi từ file backup
python scripts/backup_restore.py restore \
  --archive ./backups/backup_tlingua_YYYYMMDD_HHMMSS.tar.gz
```

> Backup sử dụng checksum **SHA-256** để xác minh tính toàn vẹn và thực hiện ghi đè **nguyên tử** (atomic write). Có bảo vệ chống Directory Traversal (Path Traversal attack).

---

## 🧪 Benchmarking & QA

```bash
# Benchmark dịch thuật
python scripts/run_translation_benchmark.py

# Benchmark toàn pipeline speech
python scripts/run_speech_benchmark_v2.py

# E2E QA tự động
python scripts/run_automated_e2e_qa.py

# Chaos testing (100 ma trận kịch bản)
python scripts/run_deep_chaos_100_matrix.py

# A/B soak test inference
python scripts/run_inference_ab_soak.py
```

---

## 🗺️ Lộ trình phát triển

| Giai đoạn | Mục tiêu | Trạng thái |
|-----------|----------|-----------|
| **Phase 1** | MVP: Pipeline STT → Translate → TTS qua WebSocket | ✅ Hoàn thành |
| **Phase 2** | Tối ưu GPU, Translation Memory, Admin Dashboard | ✅ Hoàn thành |
| **Phase 3** | Xác thực JWT/MFA, bảo mật production-grade | ✅ Hoàn thành |
| **Phase 4** | Training Center, fine-tuning model on-premise | ✅ Hoàn thành |
| **Phase 5** | Telemetry pipeline, P50/P90/P99 metrics | ✅ Hoàn thành |
| **Phase 6** | Operations: backup, monitoring, chaos testing | 🔄 Đang thực hiện |
| **Phase 7** | Scale-out, PostgreSQL, multi-tenant | 📋 Kế hoạch |

---

## 🛠️ Tech Stack

| Lớp | Công nghệ |
|-----|----------|
| **Backend** | Python 3.11, FastAPI, Uvicorn, SQLAlchemy |
| **AI / ML** | PyTorch, HuggingFace Transformers, faster-whisper, DeepFilterNet |
| **Audio Processing** | librosa, soundfile, webrtcvad, scipy |
| **Database** | SQLite (local) → PostgreSQL via asyncpg (production) |
| **Authentication** | python-jose (JWT), passlib/bcrypt, pyotp (TOTP/MFA) |
| **Frontend Mobile** | Flutter / Dart, WebSocket, Hive (local storage) |
| **Admin Web** | React, TypeScript, Vite, TailwindCSS |
| **DevOps** | Docker, Docker Compose, Nginx |

---

## 📁 Dữ liệu Runtime

Dữ liệu được lưu trong `backend/data/` (mount như Docker volume):

| File | Mô tả |
|------|-------|
| `admin.db` | SQLite database (users, sessions, settings, QA logs) |
| `translation_memory.json` | Cache dịch thuật — tái sử dụng kết quả đã biết |

---

## 📝 Giấy phép

Dự án này là **phần mềm độc quyền nội bộ**. Mọi quyền được bảo lưu.

---

<div align="center">

**T-Lingua** — *Phá vỡ rào cản ngôn ngữ bằng AI thời gian thực*

</div>
