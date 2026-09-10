# Báo cáo triển khai và lộ trình học

Giai đoạn 1 tương ứng **giai đoạn A — Nền tảng và dữ liệu** của kế hoạch đã chốt:
package/CLI, notebook Kaggle và adapter/split manifest. Ngày thực hiện: 2026-09-10.

## Đọc theo thứ tự

1. [Nền tảng package, CLI và môi trường tái lập](01-foundation.md).
2. [Notebook Kaggle, bundle và kiểm chứng môi trường](02-kaggle-preparation.md).
3. [Adapter, schema, fingerprint và protocol chia tập](03-data-adapter-and-splits.md).
4. [Kết quả nghiệm thu giai đoạn 1](phase-01-acceptance.md).
5. [Kiểm tra kết quả MVTec AD thật từ Kaggle](04-kaggle-mvtec-result.md).
6. [Evaluator và calibration dùng chung](05-evaluator-and-calibration.md).

Mỗi báo cáo có mục tiêu, kiến thức, thiết kế, chi tiết code, lý do lựa chọn, cách
chạy, bằng chứng, giới hạn, câu hỏi tự kiểm tra và đầu vào cho bước sau.
Đọc báo cáo cùng file code được dẫn; không cần hiểu toàn bộ repository một lần.

## Trạng thái thực tế

- Đã triển khai và kiểm thử phần nền tảng/dữ liệu trên local.
- Đã chạy notebook trong kernel Jupyter riêng với **450 ảnh tổng hợp, 15 category**.
- Đã build wheel, cài trong môi trường sạch và chạy CLI từ ngoài repository.
- Đã kiểm tra artifact từ lần chạy Kaggle: 5.354 ảnh, đủ 15 category, checksum hợp lệ.
- Chưa có weights, metric mô hình hoặc phương pháp thắng; evaluator/calibration
  của giai đoạn tiếp theo đã bắt đầu được triển khai.

450 ảnh là fixture sinh bằng NumPy để kiểm tra phần mềm, không phải dữ liệu
MVTec và không dùng làm bằng chứng chất lượng anomaly detection.

## Phân biệt báo cáo triển khai và báo cáo thực nghiệm

Các file trong thư mục này là báo cáo giải thích thiết kế và kiểm chứng phần mềm.
Khi chạy `vad data prepare`, hệ thống tạo `data-report.md`, `data-report.json`,
CSV thống kê và montage trong output directory. Đó là báo cáo từ dữ liệu thực sự
được truyền vào lệnh, có fingerprint và môi trường đi kèm.

Nguồn code được định danh bằng SHA-256 của các file Python trong package. Test,
notebook và tài liệu không nằm trong source fingerprint này; Git version và các
file evidence bổ sung ngữ cảnh khi bàn giao. Không coi một fingerprint là chữ ký
xác thực hoặc chứng minh hoàn toàn tính tái lập.

## Quy tắc cho các giai đoạn sau

Sau mỗi phần việc có đầu ra kiểm chứng được, thêm báo cáo có số thứ tự. Nếu chỉ
hoàn tất code mà chưa có môi trường/dữ liệu để chạy, ghi rõ phần chưa kiểm chứng.
Mọi thay đổi protocol phải có giải thích và phiên bản mới; không viết lại kết quả
cũ như thể thí nghiệm đã chạy dưới quyết định mới.
