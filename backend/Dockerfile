FROM python:3.10-slim@sha256:6ff506466f8b1e981719b468cc0023b8ef000b983cdec0eafe119d01f379e31d

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/tlingua/.cache/huggingface

# Cài đặt các thư viện hệ thống cần thiết cho xử lý âm thanh
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements trước để tận dụng Docker cache
COPY requirements.txt .

# Security-supported GPU runtime. The application does not require torchvision
# or torchaudio, so they are excluded to reduce binary attack surface.
RUN pip install --no-cache-dir \
    torch==2.13.0+cu130 \
    --index-url https://download.pytorch.org/whl/cu130

# Cài đặt các thư viện còn lại
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn
COPY app/ ./app/
COPY training/ ./training/
COPY run.py ./run.py

# Runtime data/cache locations are writable; application code remains owned by root.
RUN groupadd --system --gid 10001 tlingua \
    && useradd --system --uid 10001 --gid tlingua --home-dir /home/tlingua --create-home tlingua \
    && mkdir -p /app/data /app/outputs /app/temp /home/tlingua/.cache/huggingface \
    && chown -R tlingua:tlingua /app/data /app/outputs /app/temp /home/tlingua

USER 10001:10001

# Expose port FastAPI
EXPOSE 8000

# Khởi chạy server
CMD ["python", "run.py"]
