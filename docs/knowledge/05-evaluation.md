# 5. Đánh giá mô hình

## 5.1 Hai tầng đánh giá

### Image level

Mỗi ảnh có một `image_score` và nhãn normal/anomaly.

- **AUROC**: xác suất một ảnh anomaly được xếp hạng cao hơn một ảnh normal.
  Không cần chọn threshold, nhưng có thể trông tốt trong dữ liệu mất cân bằng.
- **Average Precision (AP/AUPR)**: nhấn mạnh chất lượng precision–recall và nhạy
  hơn với tỷ lệ anomaly. Phải báo rõ lớp dương là anomaly.
- **F1/precision/recall**: phản ánh một operating point cụ thể, do đó luôn đi
  kèm threshold và cách chọn threshold.

### Pixel level

So sánh `anomaly_map` với ground-truth mask.

- **Pixel AUROC**: dễ tính nhưng background thường chiếm đa số, có thể che giấu
  chất lượng biên hoặc defect nhỏ.
- **Pixel AP**: phản ánh mất cân bằng pixel tốt hơn AUROC.
- **AUPRO**: đo overlap theo từng vùng lỗi trên một miền false-positive rate;
  giúp các vùng nhỏ không bị lấn át hoàn toàn bởi vùng lớn.
- **IoU/Dice/F1 pixel**: cần threshold và hữu ích khi mask nhị phân là output vận hành.

Không gọi “AUROC” chung chung; phải ghi `image_AUROC` hoặc `pixel_AUROC`.

## 5.2 Từ anomaly map tới image score

Các phép gộp phổ biến:

- `max`: nhạy với defect nhỏ nhưng dễ bị một pixel nhiễu chi phối;
- `top-k mean`: ổn định hơn, nhưng `k` là hyperparameter;
- percentile cao: tương tự top-k và dễ chuẩn hóa theo kích thước ảnh;
- score có trọng số như trong phương pháp gốc.

Phải lưu phép gộp trong config. Thay đổi cách gộp có thể thay đổi image metric dù
anomaly map không đổi.

## 5.3 Chọn threshold không gây leakage

Threshold không được chọn bằng cách tối đa F1 trên test rồi trình bày như kết quả
triển khai. Các lựa chọn hợp lệ gồm:

- quantile của score trên validation normal để kiểm soát false-positive rate;
- validation có nhãn, độc lập với test;
- anomaly tổng hợp chỉ dùng để calibration, với giới hạn được công bố rõ;
- threshold theo yêu cầu vận hành, ví dụ recall tối thiểu hoặc false rejects tối đa.

Threshold mức ảnh và mức pixel là hai tham số khác nhau. Có thể cần threshold theo
category/camera nếu phân bố score khác nhau; điều này phải được version hóa.

## 5.4 Macro, micro và độ biến thiên

- Báo metric từng category để thấy failure mode.
- **Macro average**: trung bình metric của các category, mỗi category có trọng số bằng nhau.
- **Micro/global**: gộp mọi sample/pixel; category lớn có ảnh hưởng nhiều hơn.
- Nếu thuật toán có tính ngẫu nhiên, chạy nhiều seed và báo mean ± standard deviation.

Khi so với paper, phải dùng cùng cách resize, backbone, layer, sampling, metric
implementation và aggregation. Cùng tên metric không đảm bảo cùng implementation,
đặc biệt với AUPRO và giới hạn FPR.

## 5.5 Chỉ số vận hành

Benchmark model chưa hoàn chỉnh nếu thiếu:

- latency p50/p95/p99 với batch size thực tế;
- throughput;
- VRAM/RAM và kích thước artifact;
- thời gian fit/index;
- false positive theo giờ/ca/lô;
- false negative theo loại lỗi và kích thước lỗi;
- tỷ lệ ảnh bị chuyển sang kiểm tra thủ công;
- độ ổn định theo camera, ca làm, vật liệu và ánh sáng.

Đo latency sau warm-up, đồng bộ GPU đúng cách và tách thời gian decode/preprocess,
model, postprocess khi cần tối ưu.

## 5.6 Sanity checks

- Score của train normal và test normal có phân bố hợp lý.
- Anomaly map được resize đúng về ảnh gốc.
- Mask normal toàn 0 không bị bỏ qua sai cách.
- Đảo score (`-score`) phải làm AUROC xấu đi rõ rệt.
- Shuffle nhãn phải đưa metric về gần mức ngẫu nhiên.
- Visualize cả true positive, false positive, false negative và true negative.
