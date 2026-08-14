import os
import asyncio
import wave
import json
import websockets

# Cấu hình hệ thống
WS_URL = "ws://127.0.0.1:8000/ws/realtime"
CHUNK_MS = 60

# Sự kiện theo dõi kết quả trả về
audio_received_event = asyncio.Event()

def get_wav_metadata(file_path: str) -> tuple[int, int, int]:
    """Return (sample_rate, channels, sample_width) for a WAV file."""
    with wave.open(file_path, "rb") as wf:
        return wf.getframerate(), wf.getnchannels(), wf.getsampwidth()

async def listen_to_server(ws):
    """Luồng lắng nghe phản hồi Real-time từ Server"""
    try:
        async for message in ws:
            data = json.loads(message)
            print("[Server]:", json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get("type") == "audio":
                print("ĐÃ NHẬN ĐƯỢC BẢN DỊCH VÀ ÂM THANH! Đang đóng kết nối...")
                audio_received_event.set()
                
    except Exception as e:
        print("Ngắt kết nối nhận:", e)

async def simulate_user_speaking(ws, filename: str):
    """Dumb client: doc WAV va gui raw bytes len WebSocket."""
    try:
        wf = wave.open(filename, "rb")
        
        file_sample_rate = wf.getframerate()
        file_channels = wf.getnchannels()
        file_sampwidth = wf.getsampwidth() # Thường là 2 bytes (16-bit)

        print("--------------------------------------------------")
        print(f"Audio đang Stream: {file_sample_rate}Hz | {file_channels} kênh | {file_sampwidth} bytes/mẫu")
        
        # Tính số lượng frame cho mỗi 500ms
        frames_to_read = int(file_sample_rate * (CHUNK_MS / 1000))
        
        print(f"Bắt đầu phát luồng âm thanh (Cắt mỗi {CHUNK_MS}ms)...")
        print("--------------------------------------------------")

        while True:
            chunk = wf.readframes(frames_to_read)
            
            if not chunk:
                print("Đã đọc hết file audio.")
                break
            
            # Gui raw bytes, backend se xu ly DSP va STT.
            await ws.send(chunk)
            await asyncio.sleep(CHUNK_MS / 1000)
            
        print("Đang gửi thêm 2 giây khoảng lặng (Silence) để ép Server chốt câu...")
        
        # Tính toán gói dữ liệu im lặng (byte 0x00)
        silence_bytes_per_chunk = int(
            file_sample_rate * (CHUNK_MS / 1000) * file_sampwidth * file_channels
        )
        silence_chunk = b'\x00' * silence_bytes_per_chunk
        
        silence_chunks = max(1, int(2000 / CHUNK_MS))
        for _ in range(silence_chunks): 
            await ws.send(silence_chunk)
            await asyncio.sleep(CHUNK_MS / 1000)
            
    except wave.Error as e:
        print(f"Lỗi định dạng Audio Wave: {e}")
    except Exception as e:
        print(f"Lỗi khi stream: {e}")

async def main():
    # 1. Khai báo file cần test (Có thể là tiếng ồn, mp3, wav chất lượng cao...)
    input_audio_file = "test_16k.wav"
    
    # 2. Mở luồng WebSocket và thực hiện truyền tải
    async with websockets.connect(WS_URL, max_size=10_000_000) as ws:
        print("Đã kết nối tới Server thành công!")

        # Gửi config JSON ngay sau khi kết nối (theo yêu cầu Server)
        sample_rate, channels, sample_width = get_wav_metadata(input_audio_file)
        config_payload = {
            "type": "config",
            "sample_rate": sample_rate,
            "channels": channels,
            "sample_width": sample_width
        }
        await ws.send(json.dumps(config_payload))
        
        # Khởi chạy luồng nghe
        listen_task = asyncio.create_task(listen_to_server(ws))
        
        # Khởi chạy luồng nói
        await simulate_user_speaking(ws, input_audio_file)
        
        print("Đang chờ hệ thống AI xử lý (STT -> Dịch -> TTS)...")
        
        try:
            # Hẹn giờ tối đa 120s
            await asyncio.wait_for(audio_received_event.wait(), timeout=120.0)
        except asyncio.TimeoutError:
            print("Hết thời gian chờ (120s). Quá trình xử lý của Server quá lâu.")
        
        listen_task.cancel()
        print("Kết thúc phiên Test.")

if __name__ == "__main__":
    # Đảm bảo tương thích tốt nhất trên Windows
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())