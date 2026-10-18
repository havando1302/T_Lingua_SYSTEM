# Chính sách lưu trữ dữ liệu runtime

## Nguồn dữ liệu chính

Mọi dữ liệu nghiệp vụ có cấu trúc được lưu trong database cấu hình bởi
`DATABASE_URL`. Với cấu hình SQLite mặc định, file database là
`backend/data/admin.db`.

| Nhóm dữ liệu | Nơi lưu | Tồn tại sau build/restart |
|---|---|---|
| Tài khoản, phiên, API key, phân quyền | Database | Có |
| Cài đặt hệ thống và audit log | Database | Có |
| Lịch sử dịch, QA review và consent | Database | Có |
| Từ điển/Translation Memory đã duyệt và cá nhân | Bảng `translation_memory_entries` | Có |
| Pipeline telemetry và thống kê độ trễ | Database | Có |
| Training job, dataset metadata, model artifact/deployment | Database | Có |
| Audio/dataset/model nhị phân | `backend/data/` hoặc `backend/outputs/`, metadata/checksum trong database | Có nếu volume được giữ |
| Từ điển của phiên guest | RAM, gắn với thời hạn phiên | Không, theo chủ đích riêng tư |
| Translation cache và hàng đợi đang xử lý | RAM | Không, có thể tái tạo |
| File xử lý trung gian | `/tmp` và `backend/temp/` | Không, theo chủ đích |

Không nên đưa model, audio lớn hoặc checkpoint vào SQLite. Các tệp này được lưu
trong thư mục bền vững, còn database quản lý danh tính, quyền sở hữu, checksum và
trạng thái của chúng.

## Migration từ điển cũ

Khi backend khởi động, migration sẽ đọc `backend/data/translation_memory.json`
một lần, kiểm tra định dạng, tạo bản sao có checksum dạng
`translation_memory.json.pre-db-<checksum>.bak`, rồi nhập toàn bộ dữ liệu vào
`translation_memory_entries` trong cùng một transaction. Marker migration nằm
trong `system_settings`, vì vậy lần khởi động sau không nhập trùng.

Sau migration, file JSON không còn được đọc/ghi trong luồng production. Việc
build frontend bằng `npm run build` không liên quan và không được phép thay đổi
database.

## Local và Docker

Cả hai file Compose đều mount thư mục host `backend/data/` vào `/app/data` và
`backend/outputs/` vào `/app/outputs`. Vì vậy chuyển qua lại giữa chạy backend
local và Docker không tạo một database rỗng ở đường dẫn khác.

Không xóa `backend/data/`, `backend/outputs/` hoặc Docker bind mount khi triển
khai. Trước khi nâng cấp, sao lưu database cùng các thư mục file bền vững; với
SQLite đang chạy nên dùng cơ chế SQLite backup hoặc dừng backend sạch trước khi
sao chép file.
