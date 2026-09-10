# 10. Thuật ngữ

**Anomaly score** — Điểm liên tục; trong repo quy ước điểm cao hơn nghĩa là bất
thường hơn.

**Anomaly map** — Bản đồ score theo pixel/patch trước khi threshold.

**AUPRO** — Diện tích dưới đường cong Per-Region Overlap trong một miền false
positive rate; metric localization cân bằng ảnh hưởng giữa các vùng lỗi.

**AUROC** — Diện tích dưới ROC; đo khả năng xếp hạng positive cao hơn negative
trên mọi threshold.

**Average Precision (AP)** — Tóm tắt đường precision–recall; hữu ích khi lớp
dương hiếm.

**Backbone** — Mạng trích xuất feature, thường pretrained trên nguồn dữ liệu lớn.

**Calibration** — Chuyển raw score thành operating point, threshold hoặc xác suất
có ý nghĩa trong một bối cảnh cụ thể.

**Canonical sample/prediction** — Schema nội bộ thống nhất giữa mọi dataset/model.

**Category** — Một loại object/texture được xem như một bài toán con trong MVTec AD.

**Coreset** — Tập con đại diện của memory bank nhằm giảm bộ nhớ và thời gian tìm kiếm.

**Data leakage** — Thông tin từ validation/test vô tình ảnh hưởng quá trình fit,
tuning hoặc chọn threshold, làm metric lạc quan giả.

**Defect type** — Kiểu lỗi cụ thể bên trong một category, ví dụ scratch hoặc contamination.

**Detection** — Phát hiện anomaly ở mức toàn ảnh.

**Distribution shift** — Phân bố dữ liệu vận hành khác dữ liệu dùng để phát triển model.

**Drift** — Phân bố hoặc hiệu năng thay đổi theo thời gian.

**Embedding/feature** — Biểu diễn vector của ảnh hoặc patch.

**False negative (FN)** — Ảnh lỗi bị hệ thống cho là normal.

**False positive (FP)** — Ảnh normal bị hệ thống gắn cờ anomaly.

**Few-shot** — Chỉ có một số rất ít mẫu tham chiếu hoặc có nhãn.

**Image score** — Anomaly score sau khi gộp thông tin toàn ảnh/anomaly map.

**Localization** — Xác định vùng bất thường, thường ở mức pixel.

**Logical anomaly** — Vi phạm số lượng, vị trí, thứ tự hoặc quan hệ của thành phần
dù từng thành phần có thể trông bình thường.

**Memory bank** — Kho feature normal dùng để so khoảng cách lúc inference.

**Normal-only / one-class training** — Fit model chỉ bằng dữ liệu thuộc miền normal.

**Operating point** — Một threshold cụ thể cùng precision/recall/FPR tương ứng.

**Patch** — Vùng cục bộ của ảnh hoặc một vị trí trên feature map; không nhất thiết
là crop pixel được lưu riêng.

**Predicted mask** — Mask nhị phân thu được sau threshold và hậu xử lý anomaly map.

**Structural anomaly** — Sai khác cục bộ về bề mặt/hình học như xước, nứt, móp, bẩn.

**Threshold** — Ngưỡng biến score liên tục thành quyết định nhị phân.

**Zero-shot** — Suy luận không fit bằng mẫu từ category đích; có thể dựa vào
pretraining và prompt.
