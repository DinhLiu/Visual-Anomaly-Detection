# 7. Kiến trúc hệ thống dự kiến

Tài liệu này là định hướng trước khi có implementation; tên module có thể thay
đổi nhưng ranh giới trách nhiệm nên được giữ.

## 7.1 Luồng phụ thuộc

```text
configs
  │
  ├─► data adapters ─► transforms ─► dataloaders
  │                              │
  └─► model factory ─────────────┘
             │
             ├─► fit/train ─► model artifact
             │
             └─► predict ─► canonical predictions
                                      │
                        ┌─────────────┴─────────────┐
                        ▼                           ▼
                    evaluator                  visualizer
                        │                           │
                        └────────► run report ◄─────┘
```

## 7.2 Cấu trúc thư mục mục tiêu

```text
configs/
  data/              # đường dẫn logic, resize, split
  model/             # backbone, layer, coreset...
  experiment/        # ghép data + model + evaluator
data/
  README.md           # hướng dẫn đặt dữ liệu, không chứa dataset
docs/knowledge/
src/
  data/               # schema, adapter, validation, transforms
  models/             # interface và từng implementation
  engine/             # fit/predict orchestration
  evaluation/         # metrics, aggregation, calibration
  visualization/      # heatmap, overlay, failure analysis
  utils/              # logging, seed, environment capture
tests/
  unit/
  integration/
```

## 7.3 Model interface

Mọi model nên tuân theo các thao tác khái niệm:

- `fit(normal_loader)`: học hoặc index hóa miền normal;
- `predict(batch)`: trả score map và image score chưa threshold;
- `save(path)` / `load(path)`: lưu toàn bộ state cần cho inference;
- `metadata()`: mô tả preprocessing, version và khả năng của artifact.

Evaluator không biết model là PatchCore hay EfficientAD. Model cũng không biết
dataset là MVTec hay VisA.

## 7.4 Cấu hình thay vì hằng số

Các tham số sau không nên hard-code:

- dataset root/name/category;
- image size, crop và normalization;
- backbone, feature layers;
- coreset ratio/index settings;
- batch size, device, seed;
- smoothing và score aggregation;
- metric list, AUPRO FPR limit;
- calibration strategy và threshold.

Config đã resolve phải được copy vào output của mỗi run.

## 7.5 Artifact model

Một artifact đủ dùng cần gồm:

- weights/memory bank/index;
- preprocessing specification;
- category hoặc phạm vi category;
- image/pixel threshold nếu đã calibration;
- training dataset fingerprint;
- code/model version;
- output score convention;
- metric và hardware profile liên quan.

Chỉ một file weights không đủ để tái tạo hành vi inference.

## 7.6 Biên kiểm thử quan trọng

- adapter: ghép ảnh–mask và schema;
- transform: ảnh/mask đồng bộ;
- model: output shape, dtype, score direction;
- metric: đối chiếu ví dụ nhỏ tính tay;
- serialization: prediction trước/sau save-load gần như nhau;
- end-to-end: chạy một category nhỏ từ config tới report.

## 7.7 Nguyên tắc mở rộng

Thêm dataset bằng adapter mới, không thêm `if dataset == ...` trong model. Thêm
model bằng model class/factory mới, không thay evaluator. Đây là điều kiện kỹ
thuật giúp lời hứa “nâng cấp nguồn dữ liệu” trở thành khả thi.
