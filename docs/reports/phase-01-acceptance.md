# Nghiệm thu giai đoạn 1 — Nền tảng và dữ liệu

Ngày: **2026-09-10**. Phạm vi: bước 01–03, theo yêu cầu làm giai đoạn 1 trước.

## Kết quả đã có bằng chứng

- **28 tests pass**, 0 failure, gồm kiểm tra nội dung/checksum ZIP và từ chối archive chưa hoàn tất.
- Ruff lint và formatting đã áp dụng cho package, tests và scripts.
- Notebook hợp lệ theo nbformat và tất cả code cell chạy qua test tự động.
- Notebook thực thi thành công từ đầu đến cuối trong kernel Jupyter riêng.
- Build thành công `visual_ad_lab-0.1.0-py3-none-any.whl`.
- Cài wheel cùng `requirements-kaggle.lock` trong virtual environment sạch.
- Chạy executable `vad data prepare` của môi trường sạch từ `/tmp` thành công.
- Fixture dùng cho kiểm thử xuyên suốt: **450 ảnh tổng hợp, 15 category**, không
  phải dữ liệu MVTec và không có ý nghĩa đo hiệu năng anomaly detection.

Môi trường đã đo: Python **3.12.13**, NumPy **2.5.3**, Pillow **12.3.0**,
Pydantic **2.13.5**, PyYAML **6.0.3**. Không cài PyTorch/Anomalib trong môi trường
nghiệm thu giai đoạn 1. Python 3.11 có dependency marker nhưng chưa được chạy test.

## Bằng chứng có thể mở trên workspace

- [JUnit kết quả test](../../outputs/phase1-verification/pytest.xml).
- [Notebook đã chạy](../../outputs/phase1-verification/01_prepare.executed.ipynb).
- [Báo cáo dữ liệu từ notebook local](../../outputs/phase1-verification/notebook-output/data-report.md).
- [Báo cáo JSON từ wheel trong môi trường sạch](../../outputs/phase1-verification/wheel-output/data-report.json).
- [ZIP kết quả giai đoạn 1 từ notebook local](../../outputs/phase1-verification/visual-ad-phase1-c12ea0f47f66.zip).
- [Bundle Kaggle bản cuối đã build](../../dist/kaggle-bundle-v4.zip).
- [Checksum bundle](../../dist/kaggle-bundle-v4/bundle-manifest.json).

Các artifact trong `outputs/` và `dist/` được gitignore; không tự xuất hiện khi
clone repo. Có thể tái tạo bằng test/script bên dưới. Tài liệu và mã nguồn được
giữ trong Git, không commit hàng trăm ảnh fixture hoặc output notebook lớn.

Fixture có dataset fingerprint:

`367413aed8b66037c9207f45ad5329d69f2db9f890ee2d073577f61cca6c77fa`

Split fingerprint:

`c12ea0f47f66bda5636e535c874b5fc60c3f94d87afceb867484ab1898e499f8`

Fingerprint này định danh fixture của lần nghiệm thu; **không dùng làm fingerprint
mong đợi của MVTec AD thật**. Xem source fingerprint của lần chạy trong JSON report
và bundle manifest thay vì suy đoán từ tên package `0.1.0`.

Bundle `kaggle-bundle-v4` là bản cuối có CLI archive và bản sửa chạy process mới.
Các bundle cũ còn lưu local từ vòng kiểm thử trước; khi upload, dùng bản v4.

## Cách tái kiểm chứng

```bash
uv sync --extra dev --frozen
uv run --extra dev --frozen ruff check src tests scripts
uv run --extra dev --frozen ruff format --check src tests scripts
uv run --extra dev --frozen pytest -q --junitxml=outputs/phase1-verification/pytest.xml
uv run --extra dev --frozen python scripts/verify_notebook.py
uv run --extra dev --frozen python scripts/build_kaggle_bundle.py --output dist/kaggle-bundle-next
```

Kernel test cần quyền mở socket local. Nó chỉ dùng dữ liệu tổng hợp được tạo tại
`outputs/phase1-verification/synthetic-mvtec`; không cần tải dataset thật.

## Chưa có bằng chứng nghiệm thu

- Đường dẫn `/kaggle/input/datasets/ipythonx/mvtec-ad` không tồn tại trên máy đang
  triển khai, nên **chưa xác nhận 15 category và chất lượng mask của dataset Kaggle**.
- Chưa chạy bước cài dependency trong kernel Kaggle, chưa lưu Notebook Version
  hoặc kiểm tra việc gắn output sang phiên Kaggle khác.
- Chưa train bốn model, chưa có score/AUROC/AUPRO, chưa chọn model demo.
- API/frontend và smoke test ML thuộc giai đoạn sau.

Phần trên ghi trạng thái tại thời điểm nghiệm thu local ban đầu. Artifact Kaggle
sau đó đã được cung cấp và kiểm tra tại [báo cáo bổ sung](04-kaggle-mvtec-result.md):
giai đoạn 1 hiện đã nghiệm thu cả local và dữ liệu Kaggle. Toàn bộ dự án chưa hoàn thành.

## Việc tiếp theo trên Kaggle

Upload bundle và import notebook theo [hướng dẫn bước 02](02-kaggle-preparation.md).
Sau khi chạy, kiểm tra `last-status.json`, `data-report.json`, cảnh báo, số category
và gallery; lưu output của phiên. Chính output đó là đầu vào và bằng chứng để tiếp
tục giai đoạn 2.
