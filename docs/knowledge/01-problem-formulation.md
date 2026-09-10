# 1. Phạm vi bài toán

## 1.1 Bài toán cần giải

Với một ảnh sản phẩm (x), hệ thống cần tạo ra:

- `image_score`: số thực biểu thị mức độ bất thường của toàn ảnh;
- `anomaly_map`: ma trận cùng hệ tọa độ với ảnh, mỗi vị trí có một anomaly score;
- `pred_label`: quyết định OK/NG sau khi áp dụng threshold;
- `pred_mask`: vùng lỗi nhị phân sau threshold và hậu xử lý.

Đây là hai tác vụ liên quan nhưng không đồng nhất:

1. **Image-level detection** trả lời “ảnh này có bất thường không?”.
2. **Pixel-level localization** trả lời “bất thường nằm ở đâu?”.

Một model có thể phân loại ảnh đúng nhưng heatmap rất tệ, hoặc ngược lại.
Vì vậy repo phải đánh giá cả hai cấp độ.

## 1.2 Thiết lập normal-only

Ta có tập train:

\[
\mathcal{D}_{train}=\{x_i \mid y_i=0\}
\]

trong đó (y=0) là normal. Model học một biểu diễn hoặc miền phân bố của dữ
liệu bình thường. Khi inference, một mẫu càng xa miền này thì anomaly score càng
cao.

Thiết lập này phù hợp sản xuất vì:

- lỗi hiếm hơn hàng tốt;
- không thể liệt kê trước mọi loại lỗi;
- nhãn pixel đắt và phụ thuộc chuyên gia;
- loại lỗi có thể thay đổi sau khi quy trình sản xuất thay đổi.

Nhưng “khác normal” không đồng nghĩa chắc chắn với “sản phẩm hỏng”. Ánh sáng,
camera, vị trí vật thể hoặc lô nguyên liệu mới đều có thể tạo distribution shift
và bị model gắn cờ.

## 1.3 Phân biệt với các bài toán gần kề

### Binary classification

Classification có giám sát cần ví dụ đại diện của cả normal và defect, thường
chỉ trả về nhãn/score mức ảnh. Nó phù hợp khi các lớp lỗi ổn định và có đủ nhãn,
nhưng khó bao phủ lỗi chưa từng thấy.

### Semantic segmentation

Segmentation có giám sát học trực tiếp mask lỗi. Cách này có thể chính xác cao
cho lỗi đã biết nhưng cần annotation pixel và thường giảm khả năng phát hiện lỗi
mới.

### Out-of-distribution detection

OOD thường hỏi một mẫu có nằm ngoài phân bố dữ liệu huấn luyện hay không ở mức
ảnh/lớp. Visual anomaly detection công nghiệp quan tâm cả sai khác rất nhỏ, cục
bộ, giữa các ảnh có nội dung gần giống nhau.

### Novelty detection và one-class learning

Hai thuật ngữ này gần với thiết lập của repo nhất: model chỉ quan sát miền normal
rồi phát hiện mẫu mới không phù hợp.

## 1.4 Structural và logical anomaly

- **Structural anomaly**: xước, nứt, móp, bẩn, thiếu vật liệu; thường thể hiện
  bằng texture hoặc hình học cục bộ khác thường.
- **Logical anomaly**: các thành phần riêng lẻ đều hợp lệ nhưng số lượng, vị trí,
  thứ tự hoặc tổ hợp của chúng sai.

MVTec AD chủ yếu kiểm tra bất thường cấu trúc. Một model mạnh trên benchmark này
chưa chắc hiểu ràng buộc logic; MVTec LOCO AD là bước đánh giá bổ sung phù hợp.

## 1.5 Giả định ban đầu của dự án

- Input trước mắt là ảnh RGB 2D của một sản phẩm hoặc texture.
- Train không dùng ảnh defect thật.
- Test có nhãn mức ảnh và mask để đánh giá offline.
- Phiên bản đầu ưu tiên một model cho từng category; multi-category là phần mở rộng.
- Model đầu tiên cần tạo được cả image score và anomaly map.
- Mục tiêu benchmark và mục tiêu vận hành phải được báo cáo tách biệt.

## 1.6 Ngoài phạm vi phiên bản đầu

- Phân loại chính xác tên loại lỗi.
- Video anomaly detection và khai thác quan hệ thời gian.
- Dữ liệu 3D/depth.
- Active learning và human-in-the-loop hoàn chỉnh.
- Cam kết an toàn chất lượng cho dây chuyền thực tế.

Các mục này không bị loại khỏi kiến trúc; chúng chỉ không nên làm phức tạp
baseline đầu tiên.
