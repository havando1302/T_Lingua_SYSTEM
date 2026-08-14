FROM python:3.10-slim

# Cài đặt các thư viện hệ thống cần thiết cho xử lý âm thanh
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements trước để tận dụng Docker cache
COPY requirements.txt .

# Cài đặt PyTorch với CUDA 11.8 (GPU support)
# Chúng ta cài riêng Torch để đảm bảo lấy đúng phiên bản CUDA, tránh tải bản CPU
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Cài đặt các thư viện còn lại
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn
COPY . .

# Expose port FastAPI
EXPOSE 8000

# Khởi chạy server
CMD ["python", "run.py"]
