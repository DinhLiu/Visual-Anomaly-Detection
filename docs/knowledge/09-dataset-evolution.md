# 9. Chiến lược nâng cấp dữ liệu

## 9.1 “Chất lượng hơn” nghĩa là gì

Dataset lớn hơn chưa chắc tốt hơn. Với visual anomaly detection, chất lượng nên
được đánh giá theo:

- độ giống môi trường triển khai;
- độ đa dạng của normal hợp lệ;
- độ phủ loại lỗi, kích thước và mức nghiêm trọng;
- chất lượng nhãn image/mask;
- tính độc lập giữa train/val/test;
- metadata về camera, thời gian, lô và product variant;
- license và quyền lưu trữ/sử dụng;
- khả năng version hóa, audit và tái lập.

## 9.2 Lộ trình dataset

### Giai đoạn 1 — MVTec AD

Mục tiêu: hoàn thiện adapter, baseline, evaluator và experiment tracking. Không
dùng kết quả này để khẳng định khả năng vận hành.

### Giai đoạn 2 — benchmark đa dạng hơn

- **VisA**: 10.821 ảnh, 12 object subset, có cấu trúc phức tạp và nhiều instance.
- **MVTec LOCO AD**: 3.644 ảnh, 5 category, gồm structural và logical anomaly.
- **MVTec AD 2**: hơn 8.000 ảnh, 8 scenario, có biến thiên ánh sáng và test private
  qua evaluation server.
- **MVTec 3D-AD**: phù hợp nếu defect nằm ở hình học và hệ thống có depth/3D.

Chọn dataset theo failure mode cần kiểm tra, không chỉ vì leaderboard phổ biến.

### Giai đoạn 3 — dữ liệu nội bộ

Thu thập normal theo nhiều ca/lô/camera trước; đây là dữ liệu quan trọng nhất cho
normal-only learning. Thu thập defect thật và mask ở mức đủ để calibration,
acceptance test và failure analysis, ngay cả khi chúng không được dùng để fit.

## 9.3 Quy tắc chia dữ liệu nội bộ

- Chia theo vật thể vật lý/lô/thời gian, không random ảnh gần nhau vào nhiều split.
- Giữ một test set “đóng băng” chưa dùng để lựa chọn model.
- Có một test slice cho từng camera/product variant quan trọng.
- Deduplicate bằng hash và kiểm tra near-duplicate.
- Không để frame liền kề của cùng video rơi vào train và test.

Split theo thời gian thường phản ánh triển khai tốt hơn random split.

## 9.4 Version và manifest

Mỗi dataset version nên có:

```yaml
dataset_name: factory_product_x
version: 1.0.0
created_at: YYYY-MM-DD
license_or_usage_policy: internal-reference
schema_version: 1
splits:
  train: manifests/train.csv
  val: manifests/val.csv
  test: manifests/test.csv
label_policy_version: 1
```

Manifest từng sample chứa tối thiểu `sample_id`, URI/path, split, label,
mask URI, category, defect type và group/time metadata dùng để chống leakage.

## 9.5 Kiểm soát chất lượng nhãn

- Viết guideline thế nào là normal/defect và cách vẽ biên mask.
- Double-label một phần dữ liệu để đo độ đồng thuận.
- Lưu nhãn “uncertain/ignore” thay vì ép mọi trường hợp thành 0/1.
- Review riêng các defect rất nhỏ và mask chạm biên.
- Version label độc lập với file ảnh.

## 9.6 Điều kiện chấp nhận dataset mới

Adapter mới chỉ được coi là hoàn thành khi:

- ánh xạ được sang canonical sample;
- validation schema pass;
- có thống kê và montage mẫu;
- có license/usage policy rõ ràng;
- có chiến lược split chống leakage;
- evaluator chạy mà không cần sửa model;
- kết quả được báo tách khỏi MVTec nếu protocol khác.
