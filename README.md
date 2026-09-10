# Visual Anomaly Detection

Dự án xây dựng hệ thống phát hiện và định vị bất thường trên ảnh, khởi đầu
với benchmark **MVTec AD** và được thiết kế để có thể thay thế hoặc bổ sung
nguồn dữ liệu trong tương lai.

Repo đã triển khai **giai đoạn 1: nền tảng và chuẩn bị dữ liệu**. Trước khi đọc
code, hãy bắt đầu tại [Lộ trình đọc tài liệu](docs/knowledge/README.md), rồi đọc
[báo cáo triển khai giai đoạn 1](docs/reports/README.md).

## Mục tiêu dự kiến

- Huấn luyện chủ yếu từ ảnh bình thường (normal-only training).
- Trả về cả điểm bất thường ở mức ảnh và bản đồ bất thường ở mức pixel.
- Có baseline tái lập được trên MVTec AD.
- Tách lớp dữ liệu khỏi mô hình để dễ nâng cấp sang VisA, MVTec LOCO AD,
  MVTec AD 2 hoặc dữ liệu nội bộ.
- Đánh giá cả chất lượng mô hình lẫn chi phí vận hành.

## Trạng thái

Đã có package Python, CLI kiểm tra/chia dữ liệu, schema sample, fingerprint,
notebook chuẩn bị Kaggle và báo cáo dữ liệu tự sinh. Đã kiểm thử local trên
fixture tổng hợp; **chưa chạy trên MVTec AD thật ở Kaggle, chưa huấn luyện model**.
Các phần model, benchmark, API và frontend thuộc giai đoạn tiếp theo.

## Chạy giai đoạn 1 trên local

Yêu cầu Python 3.11 hoặc 3.12 và [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev --frozen
uv run --frozen vad environment
uv run --frozen vad data prepare --config configs/data.yaml --root /path/to/mvtec-ad --output outputs/mvtec-prepared
uv run --extra dev --frozen pytest -q
```

`data prepare` kiểm tra đủ 15 category mặc định. Các lệnh riêng `data validate`
và `data split --inventory <file>` phục vụ học từng bước; xem `vad data --help`.
`--allow-partial` chỉ dùng với fixture local hoặc kiểm tra phạm vi nhỏ.

## Chạy trên Kaggle

1. Tạo bundle: `uv run --extra dev --frozen python scripts/build_kaggle_bundle.py`.
2. Upload `dist/kaggle-bundle.zip` thành Kaggle Dataset private và gắn làm input.
3. Import [notebook chuẩn bị v2](notebooks/01_prepare_mvtec_kaggle_v2.ipynb). Bản v2
   chạy package trong process mới và tránh lỗi trộn phiên bản Pillow trên Kaggle.
4. Gắn MVTec AD tại `/kaggle/input/datasets/ipythonx/mvtec-ad`.
5. Sửa `BUNDLE_ROOT` trong notebook theo mount thực tế của bundle, bật Internet
   để cài dependency rồi chạy từ đầu. Giai đoạn 1 không cần GPU.
6. Kiểm tra report, chạy cell cuối và tải `visual-ad-phase1-<split-hash>.zip`.
7. Lưu Notebook Version có output tại `/kaggle/working/visual-ad` để dùng ở bước sau.

Bundle gồm wheel, config, dependency lock và checksum manifest. Nó không chứa
dataset hoặc pretrained weights. Xem [hướng dẫn Kaggle chi tiết](docs/reports/02-kaggle-preparation.md).

Trong workspace hiện tại, dùng [bundle đã nghiệm thu bản cuối](dist/kaggle-bundle-v4.zip).

## Tài liệu

- [Bản đồ kiến thức và thứ tự đọc](docs/knowledge/README.md)
- [Phạm vi bài toán](docs/knowledge/01-problem-formulation.md)
- [MVTec AD](docs/knowledge/02-mvtec-ad.md)
- [Hợp đồng dữ liệu](docs/knowledge/03-data-contract.md)
- [Các họ phương pháp](docs/knowledge/04-method-families.md)
- [Đánh giá mô hình](docs/knowledge/05-evaluation.md)
- [Thiết kế thí nghiệm](docs/knowledge/06-experimentation.md)
- [Kiến trúc hệ thống dự kiến](docs/knowledge/07-system-design.md)
- [Đưa mô hình vào vận hành](docs/knowledge/08-production.md)
- [Chiến lược nâng cấp dữ liệu](docs/knowledge/09-dataset-evolution.md)
- [Thuật ngữ](docs/knowledge/10-glossary.md)
- [Nguồn tham khảo](docs/knowledge/references.md)
