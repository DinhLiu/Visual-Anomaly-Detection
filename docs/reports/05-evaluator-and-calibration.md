# Bước 05 — Evaluator và calibration dùng chung

**Trạng thái:** đã triển khai lõi và kiểm thử local; chưa nhận prediction từ model Kaggle.

## Mục tiêu

Tạo một cách tính metric và threshold duy nhất cho PatchCore, PaDiM, FastFlow và
EfficientAD. Nếu mỗi adapter tự tính metric, khác biệt implementation có thể bị
nhầm thành khác biệt chất lượng model.

## Kiến thức và thiết kế

[evaluation.py](../../src/visual_ad/evaluation.py) nhận score liên tục; score cao
luôn có nghĩa bất thường hơn. `rank_metrics` tính image/pixel AUROC và AP. Khi
chỉ có một lớp, AUROC/AP trả `None` thay vì tạo con số giả.

`calibrate` chỉ nhận prediction từ `calibration_normal`:

- Image threshold: quantile 0,99 của image score normal.
- Pixel threshold: quantile 0,995 của tất cả pixel score normal.
- Quantile 0,01 và 0,999 của map làm thang heatmap cố định.

NumPy dùng nội suy tuyến tính mặc định. Ví dụ `[1,2,3,4]` ở quantile 0,75 cho
3,25; kết quả có thể không trùng một phần tử quan sát. Quy tắc này phải được giữ
cố định giữa các model/run.

`aupro` gán tổng trọng số 1 cho mỗi connected component anomaly, nên vùng nhỏ và
vùng lớn đóng góp ngang nhau vào mean per-region overlap. Pixel normal giữ trọng
số 1 để tính FPR. Đường cong được cắt/nội suy tại FPR 0,3 rồi chuẩn hóa diện tích
về `[0,1]`.

`evaluate` trả image AUROC/AP/F1/precision/recall/confusion matrix, pixel
AUROC/AP/F1, AUPRO, threshold và FPR limit. Threshold dùng toán tử `>`; score đúng
bằng threshold được xem là normal. Chi tiết nhỏ này được cố định để tránh hai
model runner xử lý khác nhau.

## Lý do lựa chọn

AUROC/AP dùng raw score nên không phụ thuộc threshold. F1 phản ánh operating point
cụ thể. Pixel AUROC dễ bị background chi phối; AUPRO bổ sung góc nhìn theo vùng
lỗi. Heatmap normalization không được dùng ngược để tính metric.

SciPy và scikit-learn nằm trong extra `evaluation`, tách khỏi dependency phase 1
nhẹ. Mỗi category sẽ được đánh giá riêng trước khi macro average, giúp bộ nhớ có
giới hạn và tránh category nhiều ảnh lấn át category nhỏ.

## Kiểm chứng

Test bao phủ ranking hoàn hảo, single-class, quantile nội suy, map/mask hoàn hảo,
confusion matrix, NaN, label không nhị phân, dữ liệu rỗng, quantile/FPR sai và
shape không hợp lệ. Suite đầy đủ hiện được chạy lại cùng các test phase 1.
Sau khi thêm evaluator và notebook v2, suite đầy đủ có **38 tests pass**.

Chưa đối chiếu AUPRO với prediction từ evaluation code chính thức MVTec. Trước
benchmark chính, cần chạy cùng một tập map/mask qua hai implementation và đặt sai
số cho phép rõ ràng. Vì vậy evaluator hiện đủ cho phát triển, chưa đủ để công bố
kết quả benchmark cuối.

## Cách chạy

```bash
uv sync --extra dev --extra evaluation --frozen
uv run --extra dev --extra evaluation --frozen pytest -q tests/test_evaluation.py
```

## Tự kiểm tra

1. Vì sao threshold không lấy từ selection? Vì selection có nhãn lỗi và dùng chọn model.
2. Pixel AUROC cao có đủ kết luận localization tốt không? Không; background lớn có thể che lỗi vùng nhỏ.
3. Vì sao AUPRO cân vùng bằng trọng số nghịch đảo diện tích? Để mỗi connected component có tổng trọng số bằng nhau.

## Bước tiếp theo

Định nghĩa prediction artifact có fingerprint, tích hợp PatchCore với manifest và
chạy smoke test ba category trên Kaggle. Evaluator sẽ chỉ nhận run hoàn tất và
khớp dataset/split fingerprint.
