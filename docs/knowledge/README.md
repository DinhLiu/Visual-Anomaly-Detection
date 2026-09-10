# Bản đồ kiến thức

Bộ tài liệu này dành cho người đã biết các khái niệm AI/ML cơ bản như train,
validation, test, CNN, loss và overfitting. Mục tiêu là giúp người đọc hiểu
được các quyết định quan trọng của repo trước khi đi vào mã nguồn.

Giai đoạn 1 đã có implementation cho package/CLI, adapter dữ liệu và notebook
chuẩn bị Kaggle. Đọc [báo cáo triển khai](../reports/README.md) để nối kiến thức
ở đây với code và kết quả kiểm thử thực tế; các mô tả mô hình/API vẫn là định hướng.

## Sau khi đọc, bạn cần trả lời được

1. Visual anomaly detection khác classification và segmentation có giám sát ở đâu?
2. Vì sao chỉ dùng ảnh `good` để train vẫn có thể phát hiện lỗi chưa từng thấy?
3. MVTec AD tổ chức dữ liệu và quy định protocol đánh giá như thế nào?
4. Một model phải trả về những đầu ra nào?
5. AUROC, AP, AUPRO và F1 đo những khía cạnh khác nhau ra sao?
6. Làm thế nào tránh data leakage khi chọn threshold và hyperparameter?
7. Vì sao cần một data contract độc lập với MVTec AD?
8. Khi nào kết quả benchmark chưa đủ để triển khai trong thực tế?

## Thứ tự đọc đề xuất

### Tuyến bắt buộc

1. [Phạm vi bài toán](01-problem-formulation.md)
2. [MVTec AD](02-mvtec-ad.md)
3. [Hợp đồng dữ liệu](03-data-contract.md)
4. [Các họ phương pháp](04-method-families.md)
5. [Đánh giá mô hình](05-evaluation.md)
6. [Thiết kế thí nghiệm](06-experimentation.md)
7. [Kiến trúc hệ thống dự kiến](07-system-design.md)

### Tuyến dành cho triển khai thực tế

8. [Đưa mô hình vào vận hành](08-production.md)
9. [Chiến lược nâng cấp dữ liệu](09-dataset-evolution.md)

Tra cứu nhanh tại [Thuật ngữ](10-glossary.md) và kiểm tra nguồn gốc các nhận
định tại [Nguồn tham khảo](references.md).

## Mô hình tinh thần của toàn hệ thống

```text
ảnh đầu vào
    │
    ▼
tiền xử lý ──► bộ trích xuất đặc trưng ──► mô hình phân bố "bình thường"
                                              │
                                              ▼
                              anomaly map + image score
                                              │
                         calibration/threshold/post-processing
                                              │
                                              ▼
                                  OK / NG + vùng nghi lỗi
```

`NG` (no good) ở đây có nghĩa là ảnh cần bị chặn hoặc chuyển sang kiểm tra thủ
công. Nó không nhất thiết khẳng định loại lỗi cụ thể.

## Quy ước tài liệu

- **Normal/good**: mẫu không có bất thường theo tiêu chuẩn kiểm tra hiện tại.
- **Anomaly/defect**: mẫu hoặc vùng lệch khỏi phân bố normal.
- **Detection**: quyết định ở mức ảnh.
- **Localization**: tìm vùng bất thường ở mức pixel/patch.
- “Unsupervised” trong literature MVTec thường chỉ bối cảnh không dùng ảnh lỗi
  để train; chính xác hơn, nhiều phương pháp là one-class hoặc self-supervised.

## Checklist sẵn sàng đọc code

- [x] Phân biệt `image_score`, `anomaly_map` và `pred_mask`.
- [x] Hiểu train split của MVTec AD chỉ có ảnh tốt.
- [x] Biết test label không được dùng để chọn model hoặc threshold.
- [x] Biết vì sao pixel AUROC một mình có thể gây hiểu nhầm.
- [x] Hiểu adapter dataset phải trả về cùng một schema chuẩn.
- [x] Biết baseline đầu tiên ưu tiên tính tái lập hơn độ phức tạp.
