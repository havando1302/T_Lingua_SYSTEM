# BÁO CÁO KIỂM TRA TIẾN ĐỘ CẢI THIỆN AI BẰNG LoRA

**Ngày kiểm tra:** 26/10/2026  
**Phạm vi:** model NLLB LoRA đã huấn luyện, dữ liệu đầu vào, kết quả huấn luyện, trạng thái đánh giá và triển khai

## 1. Kết luận ngắn

Đã tìm thấy một bản NLLB LoRA huấn luyện thành công về mặt kỹ thuật. Job `5aa2f3a6-e6f1-4731-8b77-e3ea75f80bd6` hoàn thành 100%, tạo hai checkpoint LoRA và một model đã merge với NLLB 1.3B. File `model.safetensors` có thể đọc cấu trúc, gồm 1.013 tensor.

Tuy nhiên, model này **chưa được đánh giá chất lượng trên test set và chưa đủ điều kiện triển khai**. Dataset dùng để huấn luyện chỉ có 2 cặp câu: 1 câu train, 1 câu validation và 0 câu test. Vì không có test split, file `evaluation_metrics.json` chỉ chứa `{}`; hệ thống không có `test_bleu` và `test_chrf`, nên artifact đang mang trạng thái `invalid`, chưa được canary, promote hoặc đưa vào inference.

Trạng thái chính xác cần ghi trong báo cáo tiến độ là:

> Đã hoàn thành một lần huấn luyện thử nghiệm NLLB bằng LoRA và tạo được candidate model đã merge. Lần chạy này chứng minh luồng dataset → train → checkpoint → merge → register hoạt động. Tuy nhiên dữ liệu chỉ có 1 mẫu train, 1 mẫu validation và không có test set, nên chưa thể kết luận model cải thiện chất lượng. Candidate hiện chưa được validate hoặc triển khai.

## 2. Model đã huấn luyện nằm ở đâu

Thư mục artifact:

`backend/data/training_control/artifacts/nllb_v1.0_retry-5aa2f3a6-e6f1-4731-8b77-e3ea75f80bd6`

| Thành phần | Bằng chứng |
|---|---:|
| Số file trong artifact | 31 file |
| Tổng kích thước artifact | 5.693.288.097 byte |
| Model đã merge | `model.safetensors`, 5.482.673.832 byte |
| LoRA checkpoint 2 | `checkpoint-2/adapter_model.safetensors`, 18.915.424 byte |
| LoRA checkpoint 3 | `checkpoint-3/adapter_model.safetensors`, 18.915.424 byte |
| Kiểm tra cấu trúc model | Mở được header safetensors, có 1.013 tensor |
| Base model | `facebook/nllb-200-distilled-1.3B` |
| Phương pháp | LoRA, sau đó merge vào base model |

Model đã tạo xong về mặt file, không phải job đang dở. Cơ sở dữ liệu ghi job `completed`, tiến độ 100% và đã đăng ký artifact `2c4495e4-b4c9-4b86-baca-32b503569ef0`.

## 3. Dữ liệu đầu vào đã dùng

### 3.1. Nguồn dữ liệu

Dataset được tạo từ các bản dịch đã qua luồng QA của hệ thống (`source_type = qa`), sau đó được validate và freeze với:

- Dataset ID: `3c211dc7-51f9-47ae-b39b-0158dfac16a5`.
- Tên/version: `nllb-v1.0` / `v1.0`.
- SHA-256: `a8fa5186d1a3d7a96bba69126514e2a827bf7da476c35d28001c0478d7860486`.
- Kích thước: 303 byte.
- Tổng số mẫu: 2.
- Ngôn ngữ/chiều dịch: chỉ có Việt → Anh.
- Lĩnh vực: `general`.
- Chia tập: 1 train, 1 validation, 0 test.
- Hai bản ghi đều có đồng ý dùng cho huấn luyện và trạng thái PII sạch.

File dữ liệu thực tế:

`backend/data/training_control/datasets/3c211dc7-51f9-47ae-b39b-0158dfac16a5/nllb-training.jsonl`

### 3.2. Hai mẫu đã đưa vào model

| Split | Nguồn tiếng Việt | Nhãn tiếng Anh | Ghi chú QA |
|---|---|---|---|
| Train | `Sở thú` | `Zoo` | QA sửa câu nguồn ban đầu `Sở thủ.` và bản dịch sai `The goalie.` |
| Validation | `Tôi xin lỗi.` | `I'm sorry about that.` | Bản dịch được QA đánh dấu đúng |

### 3.3. Đánh giá chất lượng dữ liệu

Dataset hợp lệ theo quy tắc kỹ thuật hiện tại vì có cả train và validation, không có bản ghi trùng hoặc xung đột. Tuy nhiên, quy mô này không đủ cho mục tiêu cải thiện model:

- Chỉ 1 mẫu dùng cập nhật trọng số.
- Chỉ 1 mẫu dùng tính validation loss.
- Không có mẫu test độc lập.
- Chỉ có một chiều Việt → Anh.
- Chỉ có lĩnh vực `general`.
- Không đủ dữ liệu để đánh giá khả năng khái quát, thuật ngữ, số/mã, câu dài hoặc các lĩnh vực nghiệp vụ.

Do đó đây là dataset phù hợp để **smoke test quy trình training**, không phù hợp để huấn luyện model chất lượng production.

## 4. Cấu hình LoRA đã chạy

| Tham số | Giá trị |
|---|---:|
| Base model | `facebook/nllb-200-distilled-1.3B` |
| Số epoch | 3 |
| Batch size | 2 |
| Gradient accumulation | 8 |
| Learning rate | 0,0002 |
| Max source length | 256 token |
| Max target length | 256 token |
| Seed | 42 |
| LoRA rank `r` | 16 |
| LoRA alpha | 32 |
| LoRA dropout | 0,05 |
| Target modules | `q_proj`, `v_proj` |
| Task type | `SEQ_2_SEQ_LM` |

Job thực hiện 3 global step, tương ứng 3 epoch trên đúng 1 mẫu train. Log ghi thời gian train khoảng 31,92 giây; sau đó hệ thống merge LoRA, ghi model và đăng ký artifact.

## 5. Kết quả hiện có

Validation loss trên một mẫu duy nhất:

| Epoch | Validation loss |
|---:|---:|
| 1 | 0,8863661 |
| 2 | 0,8851318 |
| 3 | 0,8846571 |

Train loss được log là 1,834. Validation loss giảm nhẹ qua ba epoch, nhưng vì chỉ đo trên một câu nên không thể dùng để khẳng định model tốt hơn. Hiện không có các chỉ số bắt buộc như BLEU, chrF, Token F1 hoặc đánh giá con người trên test độc lập.

## 6. Vì sao model chưa đánh giá được

Nguyên nhân đã được xác định từ mã nguồn và artifact:

1. Dataset validator hiện chỉ bắt buộc `train` và `validation` có dữ liệu; `test` có thể bằng 0.
2. Dataset này được freeze với `test_count = 0`.
3. Hàm đánh giá trong `train_nllb.py` trả về `{}` khi không có test rows.
4. Vì vậy trainer tạo `evaluation_metrics.json` chỉ chứa `{}`.
5. Bước validate model lại bắt buộc NLLB phải có `test_bleu` và `test_chrf`.
6. Artifact không đáp ứng quality gate nên cơ sở dữ liệu ghi trạng thái `invalid` và `validated_at` để trống.

Đây là sự không đồng bộ giữa hai chốt kiểm soát: hệ thống cho phép bắt đầu training khi chưa có test split, nhưng không cho phép validate model nếu thiếu chỉ số test.

## 7. Trạng thái triển khai

| Bước | Trạng thái |
|---|---|
| Dataset được validate | Đã hoàn thành |
| Dataset được freeze/checksum | Đã hoàn thành |
| Job LoRA | Đã hoàn thành 100% |
| Tạo checkpoint adapter | Đã hoàn thành |
| Merge LoRA vào base model | Đã hoàn thành |
| Đăng ký candidate artifact | Đã hoàn thành |
| Đánh giá locked test | Chưa thực hiện; dataset không có test |
| Validate artifact | Không đạt; thiếu `test_bleu` và `test_chrf` |
| Canary | Chưa thực hiện |
| Promote/production | Chưa thực hiện |

Model active hiện tại vẫn là `facebook/nllb-200-distilled-1.3B`; candidate LoRA không nằm trong canary và chưa nhận lưu lượng.

## 8. Dữ liệu QA hiện có sau lần huấn luyện

Cơ sở dữ liệu hiện có 4 mẫu đủ điều kiện xuất cho NLLB:

- 2 mẫu train.
- 1 mẫu validation.
- 1 mẫu test.

Mẫu test được bổ sung sau khi dataset `nllb-v1.0` đã freeze và sau lần training trên, nên không thuộc lineage của artifact hiện tại. Dù tạo dataset version mới thì tổng cộng 4 mẫu vẫn quá ít để đánh giá đáng tin cậy. Một test set chỉ có một câu cũng không đủ để kết luận BLEU/chrF.

## 9. Việc cần làm tiếp theo

### 9.1. Sửa quality gate dữ liệu

- Không cho freeze hoặc tạo training job nếu thiếu một trong ba split: train, validation, test.
- Đặt số mẫu tối thiểu cho từng split và từng chiều dịch.
- Khóa dataset bằng checksum; test set không được thay đổi sau khi training bắt đầu.

### 9.2. Tạo dataset đủ dùng

- Bổ sung cả Việt → Anh và Anh → Việt.
- Bao phủ các lĩnh vực đang yếu trong benchmark, số/mã, tên riêng, câu ngắn và câu dài.
- Chỉ dùng dữ liệu đã có consent, đã kiểm soát PII và có bản dịch chuẩn được review.
- Không dùng lại các câu benchmark làm dữ liệu train.

### 9.3. Đánh giá candidate hiện tại

Candidate hiện tại có thể được chạy đối chứng trên bộ 500 câu độc lập ngày 25/10 để đo khả năng dịch, nhưng kết quả phải được ghi là đánh giá hậu kiểm của một model smoke-test, không phải locked test gắn với dataset training ban đầu.

Cần so sánh cùng điều kiện giữa base và candidate:

- Token F1, chrF và BLEU tổng thể.
- Kết quả theo chiều Việt → Anh và Anh → Việt.
- Numeric fidelity, tên riêng và thuật ngữ.
- Latency trung bình, P95 và bộ nhớ GPU.
- Danh sách regression theo từng câu.

### 9.4. Huấn luyện candidate tiếp theo

Sau khi có dataset version mới đủ ba split, cần chạy lại LoRA và chỉ công nhận cải thiện khi candidate vượt base model trên cùng locked test, không giảm các nhóm trọng yếu và vượt qua canary/rollback.

## 10. Nguồn bằng chứng

1. Dataset manifest: `backend/data/training_control/datasets/3c211dc7-51f9-47ae-b39b-0158dfac16a5/dataset-manifest.json`.
2. Dữ liệu JSONL: `backend/data/training_control/datasets/3c211dc7-51f9-47ae-b39b-0158dfac16a5/nllb-training.jsonl`.
3. Training manifest: `backend/data/training_control/artifacts/nllb_v1.0_retry-5aa2f3a6-e6f1-4731-8b77-e3ea75f80bd6/training_manifest.json`.
4. Kết quả đánh giá trống: `backend/data/training_control/artifacts/nllb_v1.0_retry-5aa2f3a6-e6f1-4731-8b77-e3ea75f80bd6/evaluation_metrics.json`.
5. Cấu hình phát hành: `backend/data/training_control/artifacts/nllb_v1.0_retry-5aa2f3a6-e6f1-4731-8b77-e3ea75f80bd6/release_manifest.json`.
6. Log epoch: `backend/data/training_control/artifacts/nllb_v1.0_retry-5aa2f3a6-e6f1-4731-8b77-e3ea75f80bd6/checkpoint-3/trainer_state.json`.
7. Cấu hình adapter: `backend/data/training_control/artifacts/nllb_v1.0_retry-5aa2f3a6-e6f1-4731-8b77-e3ea75f80bd6/checkpoint-3/adapter_config.json`.
8. Candidate đã merge: `backend/data/training_control/artifacts/nllb_v1.0_retry-5aa2f3a6-e6f1-4731-8b77-e3ea75f80bd6/model.safetensors`.
9. Trạng thái job/artifact/deployment: các bảng `training_jobs`, `model_artifacts`, `model_deployments` trong `backend/data/admin.db`.
10. Logic đánh giá: `backend/training/train_nllb.py`.
11. Quality gate artifact: `backend/app/api/training_routes.py`.

## 11. Kết luận báo cáo

Phần cải thiện AI bằng LoRA đã đi tới mức **huấn luyện thử nghiệm thành công và tạo được candidate model hoàn chỉnh về mặt file**. Đây là tiến độ thực tế đáng ghi nhận của pipeline kỹ thuật. Tuy nhiên, dữ liệu đầu vào quá nhỏ và không có test split, nên chưa có bằng chứng rằng chất lượng dịch được cải thiện. Candidate đang ở trạng thái không hợp lệ để triển khai, model production chưa thay đổi. Ưu tiên tiếp theo là hoàn thiện dataset và quality gate, sau đó đánh giá đối chứng base/candidate trên bộ dữ liệu độc lập trước khi quyết định huấn luyện lại hoặc canary.
