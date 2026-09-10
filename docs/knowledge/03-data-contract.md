# 3. Hợp đồng dữ liệu độc lập với dataset

## 3.1 Vì sao cần data contract

Nếu code model biết trực tiếp các đường dẫn như `train/good` hoặc hậu tố
`_mask.png`, việc chuyển từ MVTec AD sang dataset khác sẽ lan thay đổi khắp repo.
Giải pháp là mỗi dataset có một **adapter**, còn model chỉ nhận một schema chuẩn.

```text
MVTec AD ─┐
VisA ─────┼─► Dataset Adapter ─► Canonical Sample ─► Model/Evaluator
Nội bộ ───┘
```

## 3.2 Canonical sample

Schema logic đề xuất:

```python
sample = {
    "image": Tensor,           # float32, shape [C, H, W]
    "mask": Tensor | None,     # bool/uint8, shape [H, W]
    "label": int | None,       # 0 normal, 1 anomaly
    "category": str,
    "defect_type": str,        # "good" nếu normal
    "split": str,              # train | val | test
    "image_path": str,
    "sample_id": str,
    "original_size": tuple[int, int],
    "metadata": dict,
}
```

Các nguyên tắc:

- `sample_id` ổn định, duy nhất trong một dataset version.
- `mask=None` nghĩa là không có nhãn; không đồng nghĩa mask toàn 0.
- Normal sample có nhãn mask thì mask phải toàn 0.
- Tất cả shape, dtype và miền giá trị được kiểm tra ở biên adapter.
- Metadata không được là điều kiện bắt buộc để model chạy.

## 3.3 Canonical prediction

```python
prediction = {
    "sample_id": str,
    "image_score": float,
    "anomaly_map": Tensor,     # float32 [H, W], score cao = bất thường hơn
    "pred_label": int | None,
    "pred_mask": Tensor | None,
    "thresholds": {
        "image": float | None,
        "pixel": float | None,
    },
    "timing_ms": dict,
    "model_version": str,
}
```

Evaluator nên dùng score liên tục cho AUROC/AP và chỉ dùng output đã threshold
cho F1, precision, recall hoặc chỉ số vận hành.

## 3.4 Dataset interface tối thiểu

Một adapter cần cung cấp:

- danh sách category;
- iterator/sample access theo split;
- mapping ảnh–mask;
- validation schema;
- dataset manifest và license metadata;
- thống kê số mẫu theo category/split/defect type.

Model không được tự quét filesystem. Data module chịu trách nhiệm đường dẫn,
decode, transform và batching.

## 3.5 Transform và khả năng truy vết

Tách transform thành ba nhóm:

1. `decode`: đọc file, chuẩn hóa orientation và color space;
2. `geometric`: resize/crop/flip, áp dụng đồng bộ lên ảnh và mask;
3. `photometric`: normalize, color jitter; thường chỉ áp dụng lên ảnh.

Mỗi prediction cần có đủ metadata để ánh xạ anomaly map về kích thước ảnh gốc.
Nếu dùng padding hoặc crop, phải lưu tham số biến đổi ngược.

## 3.6 Kiểm tra dữ liệu bắt buộc

- Không trùng `sample_id` giữa split.
- Train normal-only không chứa `label=1`.
- Ảnh lỗi có mask tồn tại, đúng kích thước và có ít nhất một pixel dương.
- Ảnh normal có mask rỗng nếu mask được tạo.
- Không có file hỏng, NaN hoặc tensor sai số kênh.
- Thống kê trước/sau transform hợp lý.
- Hash hoặc group ID không xuất hiện ở nhiều split khi các ảnh đến từ cùng một vật thể/lô.

## 3.7 Chuẩn bị cho dữ liệu nội bộ

Schema `metadata` có thể chứa `camera_id`, `line_id`, `batch_id`, `timestamp`,
`product_variant`, `operator` hoặc điều kiện ánh sáng. Những trường này rất quan
trọng để chia dữ liệu theo nhóm/thời gian và phân tích drift, nhưng không nên
biến thành feature mặc định nếu chưa đánh giá nguy cơ shortcut learning.
