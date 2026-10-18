# Báo cáo benchmark và tối ưu AI — 13/10/2026

## Phạm vi

- GPU: NVIDIA GeForce RTX 3050 Laptop 6 GB
- Python 3.10.11, PyTorch 2.13.0+cu130, Transformers 5.15.1
- Dịch: `facebook/nllb-200-distilled-1.3B`, 500 câu Việt ↔ Anh
- STT: `openai/whisper-large-v3-turbo`, 100 mẫu (50 sạch, 50 Gaussian noise 15 dB)
- Pipeline: 10 lượt warm STT → NLLB → VITS, không gồm network/queue

## Kết quả

### Nhận dạng giọng nói

So sánh A/B trên cùng 100 file audio và cùng model production:

| Cấu hình | WER | Thời gian trung bình | Chênh lệch tốc độ |
|---|---:|---:|---:|
| Tiền xử lý + beam 3 (cũ) | 34,67% | 569,9 ms | mốc so sánh |
| Tiền xử lý + beam 1 (mới) | **34,57%** | **378,1 ms** | **nhanh hơn 33,7%** |

Kết quả mới theo điều kiện:

- Audio sạch: WER 34,01%
- Audio nhiễu 15 dB: WER 35,13%
- P50: 361,0 ms; P95: 522,8 ms
- Realtime factor trung bình: 0,1013

Báo cáo cũ dùng `whisper-small` nên không phản ánh model production. So với số cũ đó (WER 39,68%), `large-v3-turbo` mới giảm WER tuyệt đối 5,11 điểm phần trăm, nhưng chậm hơn vì model lớn hơn.

### Dịch thuật

| Chỉ số | Kết quả hiện tại |
|---|---:|
| Cold-start generation | 2.190,9 ms |
| Mean warm | 953,9 ms |
| P50 / P95 / P99 | 953,8 / 1.165,3 / 1.239,8 ms |
| BLEU (smoothed) | 56,923 |
| chrF trung bình | 74,867 |
| Token-F1 trung bình | 0,7870 |
| Required-term accuracy thô | 74,29% |

Warm-up NLLB mới chuyển khoảng 2,19 giây khởi tạo CUDA sang lúc server startup, để yêu cầu dịch đầu tiên chạy ở trạng thái warm. Chất lượng gần như không đổi so với báo cáo trước (BLEU 56,925; chrF 74,867; token-F1 0,7871).

Độ trễ warm hiện cao hơn báo cáo dùng PyTorch 2.7.1+cu118 (483,1 ms). Đây là hồi quy theo môi trường/runtime cần được A/B lại trong một virtualenv tách biệt trước khi hạ phiên bản production.

`required_term_accuracy` đang đánh giá thấp chất lượng thật: corpus coi các bản dịch hợp lệ như `Wednesday` (thay cho `thứ Tư`), `two` (thay cho `2`) và `Danang` (thay cho `Đà Nẵng`) là lỗi. Không thêm hậu xử lý để ép các nhãn sai này vì sẽ làm câu đích kém tự nhiên.

### Pipeline đầy đủ

| Stage | Mean | P95 |
|---|---:|---:|
| STT | 359,5 ms | 421,2 ms |
| Dịch | 467,5 ms | 732,6 ms |
| TTS | 323,5 ms | 416,5 ms |
| End-to-end | **1.150,5 ms** | **1.436,0 ms** |

- Throughput tuần tự: 0,869 lượt/giây
- VRAM peak: 4.355,9 MB / 6 GB
- Không xảy ra OOM

## Thay đổi đã áp dụng

1. Đổi `WHISPER_BEAM_SIZE` mặc định từ 3 xuống 1 dựa trên A/B đủ 100 mẫu.
2. Giới hạn token decode Whisper theo độ dài audio để chặn noise/hallucination chạy tới trần 224 token.
3. Warm-up NLLB trong `ModelManager`, ngoài Whisper/TTS đã có.
4. Load NLLB và VITS ở FP16 trên CUDA để giảm VRAM và tránh đường suy luận FP32 không cần thiết.
5. Sửa benchmark STT/full-pipeline dùng đúng `large-v3-turbo`, revision cố định và tiền xử lý giống production.
6. Ghi model, revision, GPU, Python, PyTorch và Transformers vào artifact benchmark để lần sau so sánh đúng môi trường.

## Xác minh

- 51 test + 10 subtest: đạt
- Python compile check: đạt
- ModelManager startup thật: cả Whisper/NLLB/VITS ready, FP16, không fallback CPU
- Startup sau thay đổi: 30,94 giây; warm-up 4,4 giây

## Giới hạn và bước tiếp theo

- Audio benchmark là giọng VITS tổng hợp; cần bộ thu thật theo giọng vùng miền, thiết bị và phòng khác nhau.
- Cần sửa reference/required terms của corpus và có ít nhất hai người chấm adequacy/fluency.
- Nên A/B PyTorch 2.7.1+cu118 và 2.13.0+cu130 trong hai môi trường độc lập trước khi khóa runtime GPU.
- Khi có tải đồng thời thực, chạy thêm WebSocket load test để đo queue wait và P99 end-to-end.
