# 6. Thiết kế thí nghiệm tái lập

## 6.1 Một run phải lưu những gì

- mã nguồn/commit hiện tại;
- config đã resolve hoàn toàn;
- dataset name, version, root fingerprint và split manifest;
- category và số lượng mẫu;
- seed;
- phiên bản Python, framework, CUDA/driver và phần cứng;
- checkpoint, memory bank hoặc artifact model;
- prediction thô theo `sample_id`;
- metric từng category và aggregate;
- thời gian chạy và peak memory;
- ảnh minh họa failure cases.

Chỉ lưu con số tổng hợp là chưa đủ: prediction thô cho phép tính lại metric mà
không phải chạy lại model.

## 6.2 Baseline tối thiểu đề xuất

### B0 — sanity baseline

Dùng feature pretrained toàn ảnh hoặc patch đơn giản và nearest-neighbor. Mục tiêu
là xác minh loader, score direction và evaluator, không phải đạt SOTA.

### B1 — PatchCore chuẩn

- một model/category;
- backbone và layer cố định;
- preprocessing cố định;
- coreset ratio được ghi trong config;
- image aggregation và smoothing được ghi rõ;
- đánh giá đủ image AUROC/AP và pixel AUROC/AP/AUPRO.

### B2 — baseline hướng vận hành

Chỉ thêm EfficientAD hoặc model nhẹ khi đã có profile latency/memory và biết B1
không đáp ứng yêu cầu nào.

## 6.3 Ablation có giá trị

Mỗi lần chỉ thay một yếu tố chính:

- input resolution;
- backbone/layer;
- coreset ratio;
- nearest-neighbor index;
- smoothing/post-processing;
- image-score aggregation;
- số lượng ảnh normal dùng để fit.

Báo cả quality và cost. Coreset lớn hơn có thể tăng metric nhưng làm memory và
latency không phù hợp vận hành.

## 6.4 Quy trình tránh leakage

```text
train normal ──► fit model
      │
      └────────► val normal / synthetic / labeled calibration
                            │
                            └─► chọn config + threshold

test normal + anomaly ──► đánh giá đúng một lần cho báo cáo cuối
```

Không nên xem test heatmap rồi chỉnh transform, layer hay threshold lặp đi lặp
lại. Đó là tuning trên test dù không gọi là training.

## 6.5 Definition of Done cho một thí nghiệm

- Chạy lại được từ một lệnh và một config.
- Không cần sửa đường dẫn trong code.
- Loader validation pass.
- Metric có test đơn vị trên dữ liệu nhỏ đã biết kết quả.
- Có báo cáo per-category và macro average.
- Có ít nhất một montage failure-case.
- Có profile tài nguyên trên phần cứng được nêu rõ.
- Không dùng test label trong fit/calibration.

## 6.6 So sánh công bằng

Một bảng so sánh chỉ có ý nghĩa khi thống nhất:

- split và category;
- image resolution/aspect-ratio policy;
- pretrained data;
- quyền sử dụng ảnh lỗi;
- metric implementation và FPR limit;
- cách average;
- số seed;
- phần cứng và batch size cho latency.

Nếu khác protocol, ghi kết quả thành nhóm riêng thay vì xếp chung một cột.
