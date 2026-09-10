# 2. Hiểu đúng MVTec AD

## 2.1 Tổng quan

MVTec AD là benchmark cho anomaly detection trong kiểm tra công nghiệp. Dataset
có 5.354 ảnh màu độ phân giải cao, gồm 15 category: 5 texture và 10 object. Train
chỉ chứa ảnh không lỗi; test có cả ảnh không lỗi và ảnh lỗi. Các ảnh lỗi có mask
pixel chính xác. Paper gốc mô tả 73 loại bất thường và 1.888 vùng được gán nhãn.

Các category:

- Texture: `carpet`, `grid`, `leather`, `tile`, `wood`.
- Object: `bottle`, `cable`, `capsule`, `hazelnut`, `metal_nut`, `pill`, `screw`,
  `toothbrush`, `transistor`, `zipper`.

Số liệu và tên category cần được xem như metadata của adapter, không hard-code
vào model.

## 2.2 Cấu trúc thư mục

```text
<root>/<category>/
├── train/
│   └── good/*.png
├── test/
│   ├── good/*.png
│   └── <defect_type>/*.png
└── ground_truth/
    └── <defect_type>/*_mask.png
```

Ảnh `test/good` không có mask tương ứng; loader phải tạo mask toàn số 0 trong
bộ nhớ. Tên mask của ảnh lỗi thường thêm hậu tố `_mask`, vì vậy việc ghép ảnh và
mask phải được kiểm tra bằng test thay vì dựa vào thứ tự liệt kê file.

## 2.3 Protocol chuẩn

1. Fit model bằng `train/good` của một category.
2. Không dùng ảnh lỗi trong test để học feature, chọn hyperparameter hay threshold.
3. Chạy inference trên toàn bộ `test/good` và `test/<defect_type>`.
4. Đánh giá detection từ image score.
5. Đánh giá localization từ anomaly map và ground-truth mask.
6. Báo cáo từng category và macro average qua các category.

Nếu cần validation mà dataset không cung cấp, phải công bố rõ cách tạo validation,
ví dụ giữ lại một phần ảnh normal hoặc tạo anomaly tổng hợp. Không được âm thầm
dùng test set để tuning.

## 2.4 Vai trò của mask

Mask là **ground truth dùng cho đánh giá**, không phải đầu vào model trong thiết
lập normal-only. Quy ước chuẩn nội bộ nên là:

- `0`: background/normal;
- `1`: anomaly;
- shape `(H, W)` và khớp tọa độ với ảnh sau mọi phép biến đổi hình học.

Resize ảnh bằng bilinear/bicubic là hợp lý, nhưng resize mask phải dùng nearest
neighbor để không tạo nhãn mềm giả. Nếu crop/flip ảnh thì mask phải nhận đúng
cùng phép biến đổi.

## 2.5 Hạn chế cần nhớ

- Ảnh benchmark sạch và bối cảnh thu nhận tương đối kiểm soát.
- Số category và biến thiên theo từng category còn hạn chế.
- Kết quả trên MVTec AD đã gần bão hòa với nhiều phương pháp hiện đại.
- Dataset không đại diện đầy đủ cho thay đổi ánh sáng, camera, rung, bụi, drift
  theo thời gian và lỗi logic ngoài thực tế.
- License hiện hành là **CC BY-NC-SA 4.0**; không được mặc định rằng có thể dùng
  dataset cho sản phẩm thương mại.

Vì vậy MVTec AD là điểm khởi đầu để xác minh pipeline, không phải bằng chứng cuối
cùng về độ tin cậy trong nhà máy.

## 2.6 Quy tắc lưu dữ liệu trong repo

- Không commit ảnh MVTec AD, checkpoint lớn hoặc file sinh ra từ dataset.
- `data/` chỉ chứa README, manifest nhỏ hoặc symlink cục bộ đã được ignore.
- Dataset root được truyền qua config hoặc biến môi trường dành riêng cho dự án.
- Ghi lại checksum/version/ngày tải trong manifest thí nghiệm.
- Đọc và chấp nhận license tại trang chính thức trước khi tải hoặc phân phối lại.

Xem nguồn chính thức trong [references.md](references.md).
