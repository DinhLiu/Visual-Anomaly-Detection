# 4. Các họ phương pháp

## 4.1 Reconstruction-based

Autoencoder/GAN học tái tạo ảnh normal. Giả định là model tái tạo vùng normal tốt
nhưng tái tạo anomaly kém; sai số tái tạo trở thành anomaly map.

Ưu điểm: trực quan, tạo được bản đồ pixel. Nhược điểm: model có thể tái tạo cả
anomaly, ảnh tái tạo bị mờ và pixel error nhạy với lệch vị trí/ánh sáng.

Nên dùng như baseline giáo dục, không mặc định là baseline mạnh nhất.

## 4.2 Feature-distribution based

Dùng backbone pretrained để lấy embedding theo patch, sau đó ước lượng phân bố
feature normal. PaDiM là ví dụ: mô hình hóa feature tại mỗi vị trí bằng phân bố
Gaussian và dùng khoảng cách Mahalanobis khi inference.

Ưu điểm: tận dụng biểu diễn mạnh; thường tốt hơn so sánh pixel thô. Nhược điểm:
tốn bộ nhớ/thống kê và phụ thuộc mức căn chỉnh của ảnh.

## 4.3 Memory-bank / nearest-neighbor

PatchCore lưu một tập đại diện các patch feature normal. Với patch test (z),
anomaly score cơ bản là khoảng cách tới patch normal gần nhất:

\[
s(z)=\min_{m\in\mathcal{M}} d(z,m)
\]

Trong đó \(\mathcal{M}\) là memory bank. Coreset sampling giảm kích thước memory
bank trong khi cố giữ độ phủ feature space.

Ưu điểm: baseline mạnh, không cần train end-to-end, có localization tự nhiên.
Nhược điểm: memory và latency tăng theo coreset; kết quả phụ thuộc backbone,
layer, preprocessing và thuật toán tìm láng giềng.

**Khuyến nghị cho baseline đầu tiên:** PatchCore trên từng category, dùng backbone
pretrained cố định và cấu hình có thể tái lập.

## 4.4 Student–teacher / distillation

Teacher sinh feature mục tiêu; student học bắt chước teacher trên ảnh normal.
Khi gặp vùng khác normal, sai khác teacher–student được dùng làm anomaly score.
EfficientAD kết hợp nhánh local student–teacher với autoencoder xử lý thông tin
toàn cục và tập trung mạnh vào latency thấp.

Ưu điểm: inference nhanh và có đường nâng cấp thực tế. Nhược điểm: cần training,
calibration và quản lý checkpoint phức tạp hơn PatchCore.

## 4.5 Flow-based và density estimation

Normalizing flow biến feature normal về một phân bố có likelihood dễ tính.
Điểm likelihood thấp có thể là anomaly. Likelihood không phải lúc nào cũng khớp
với ngữ nghĩa “bất thường”, nên cần kiểm tra trực quan và định lượng cẩn thận.

## 4.6 Synthetic-anomaly / discriminative

Tạo defect giả trên ảnh normal rồi train segmentation/classification. Cách này
có thể học decision boundary tốt mà không cần defect thật, nhưng hiệu quả phụ
thuộc mức độ defect giả đại diện cho tín hiệu thực. Nếu generator tạo shortcut,
model sẽ học artifact thay vì khái niệm lỗi.

## 4.7 Foundation model, few-shot và zero-shot

Embedding từ vision-language/foundation model có thể hỗ trợ zero-shot, prompt
hoặc few-shot. Chúng hữu ích khi cần tổng quát qua category hoặc mô tả lỗi, nhưng
không tự động giải quyết localization chi tiết, domain shift hay latency.

Không nên chọn hướng này chỉ vì model lớn hơn; phải so với baseline cùng protocol.

## 4.8 Ma trận lựa chọn thực dụng

| Nhu cầu | Điểm khởi đầu |
|---|---|
| Baseline mạnh, dễ tái lập | PatchCore |
| Giải thích nguyên lý reconstruction | Autoencoder |
| Inference rất nhanh | EfficientAD |
| Ảnh căn chỉnh tốt, muốn thống kê rõ ràng | PaDiM |
| Có nhiều normal nhưng ít defect và muốn học boundary | Synthetic anomaly |
| Cần suy luận đa category/ngôn ngữ | Foundation/VLM, sau baseline |

Trình tự hợp lý cho repo: **PatchCore → đo và phân tích lỗi → EfficientAD hoặc
phương pháp khác theo yêu cầu latency/dữ liệu**, không chạy theo leaderboard trước
khi protocol ổn định.
