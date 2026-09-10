# Bước 04 — Kiểm tra kết quả MVTec AD thật từ Kaggle

**Trạng thái:** đạt yêu cầu dữ liệu giai đoạn 1. Kiểm tra ngày 2026-09-10.

## Mục tiêu và đầu vào

Kiểm tra thư mục [visual-ad-phase1-result](../../data/visual-ad-phase1-result/)
được tải về từ notebook Kaggle. Mục tiêu là xác nhận file không hỏng, manifest
nhất quán và split sẵn sàng làm đầu vào duy nhất cho giai đoạn model.

## Kết quả đo được

- Trạng thái run: `completed`, action `prepare`.
- Môi trường ghi nhận: Kaggle, Python 3.12.13.
- Tổng ảnh: **5.354**, đủ **15 category** MVTec AD.
- `fit`: 2.551 normal.
- `validation_normal`: 539 normal.
- `calibration_normal`: 539 normal.
- `selection`: 655 ảnh, gồm 181 normal và 474 anomaly.
- `final_test`: 1.070 ảnh, gồm 286 normal và 784 anomaly.
- Cảnh báo từ pipeline: không có.
- Cả 9 checksum trong `checksums.json` khớp file đã tải.
- Dataset fingerprint: `061f3c21830a4d837464311b4dd06f2538174fd46dd7f1efd7ed431f3bcd73a1`.
- Split fingerprint: `c3e88882c2e2df4283373ecaa9c7f4cc3ec7eb99e9201cf493f3e1f0902e6ff9`.

`validate_manifest` của code hiện tại chấp nhận manifest. Sample ID không trùng;
fit/validation/calibration chỉ lấy train normal; selection/final_test chỉ lấy test gốc.

## Kiểm tra trực quan

Ảnh preview cho thấy mỗi category có một hàng normal và một hàng anomaly; ba cột
là ảnh, mask và overlay. Mask trắng nằm đúng vùng khuyết tật và overlay đỏ khớp
mask ở các mẫu đã quan sát. Không thấy lỗi ghép tên mask hoặc đảo trục trong montage.

Đây là kiểm tra đại diện, không phải review thủ công từng mask trong 5.354 ảnh.
Validation tự động đã decode toàn bộ ảnh và kiểm tra mask nhị phân/cùng kích thước.

## Diễn giải đúng câu “dữ liệu bình thường”

Dữ liệu **hợp lệ và không có cảnh báo**. Dataset không phải toàn ảnh bình thường:
train dùng cho fit/calibration là normal-only, còn selection và final_test chứa
cả normal lẫn anomaly. Đây chính là cấu trúc cần thiết để train one-class và đo
khả năng phát hiện lỗi.

## Lý do đủ điều kiện chuyển bước

Bốn model sẽ dùng cùng `split-manifest.json`, nên không cần chia lại. Fingerprint
cho phép từ chối kết quả model được tạo từ dataset/split khác. Final test vẫn chưa
được dùng để chọn model; chỉ metadata/nhãn được validator đọc để kiểm tra cấu trúc.

## Giới hạn

- Checksum chứng minh file tải về khớp ZIP, không phải chữ ký nguồn dữ liệu.
- Duplicate exact đã kiểm tra; near-duplicate/cùng vật thể chưa được xác minh.
- `dataset_version` hiện là nhãn mô tả; định danh mạnh nằm ở content fingerprint.
- Bản notebook dùng để tạo artifact gặp lỗi Pillow sau bước prepare, nhưng các
  artifact phase 1 đã được tạo hoàn chỉnh trước lỗi và checksum khớp. Notebook v2
  sửa đường chạy process mới cho lần chạy tiếp theo.

## Tự kiểm tra

1. Vì sao selection có anomaly mà fit không có? Fit học normal-only; selection cần nhãn để so sánh model.
2. Vì sao không gộp 1.070 ảnh final test vào selection? Để còn dữ liệu kiểm chứng sau khi chốt model.
3. Vì sao cần cả dataset và split fingerprint? Cùng ảnh có thể được chia vai trò khác nhau.

## Bước tiếp theo

Xây evaluator/calibration dùng chung, sau đó tích hợp PatchCore đầu tiên. Mọi run
phải ghi đúng hai fingerprint trên trước khi được đưa vào bảng so sánh.
