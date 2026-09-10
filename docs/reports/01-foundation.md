# Bước 01 — Nền tảng package, CLI và môi trường tái lập

**Trạng thái:** đã triển khai và kiểm thử local. Chưa xác nhận môi trường Kaggle.

## 1. Mục tiêu và bối cảnh

Trước khi train, cần một chương trình có thể chạy giống nhau từ terminal local
và notebook Kaggle. Nếu logic đọc dữ liệu được chép vào nhiều cell, chỉ một lần
sửa thiếu cũng có thể khiến các model chạy trên split khác nhau.

Đầu ra bước này là package `visual-ad-lab`, module import `visual_ad`, CLI `vad`,
cấu hình có validation và dependency lock. Tên distribution, module và CLI khác
nhau là quy ước Python bình thường; chúng cùng trỏ về một package.

## 2. Kiến thức cần hiểu

- **Package** gom code thành các module có thể import và tái sử dụng.
- **Wheel** là gói cài đặt chứa code Python, metadata và entry point. Nó không chứa
  Python interpreter, toàn bộ dependency hoặc dataset.
- **Virtual environment** cô lập dependency của project khỏi Python hệ thống.
- **Lockfile** ghi phiên bản đã resolve, bao gồm dependency gián tiếp. Khoảng phiên
  bản trong `pyproject.toml` tự nó chưa đủ để tái tạo môi trường.
- **CLI** là giao diện có thể tự động hóa; notebook gọi cùng CLI để giữ hành vi nhất quán.

Xem thêm [kiến trúc dự kiến](../knowledge/07-system-design.md). Báo cáo này mô tả
implementation hiện tại; các module model/API trong tài liệu dự kiến chưa tồn tại.

## 3. Thiết kế và luồng thực thi

```text
terminal / Kaggle notebook
          ↓
       cli.main
          ↓
config validation → data inspection/split → reporting
          ↓                    ↓                ↓
resolved-config.json     manifest/hash      JSON/CSV/Markdown/PNG
```

Thư mục `src/visual_ad` tránh việc vô tình import code chỉ vì đang đứng ở repo root.
Test wheel từ `/tmp` kiểm chứng package thực sự được cài đúng, không được hỗ trợ
bởi một đường dẫn import tình cờ.

## 4. Chi tiết triển khai

- [pyproject.toml](../../pyproject.toml): metadata, dependency, entry point và cấu hình test/lint.
- [config.py](../../src/visual_ad/config.py): `DataConfig` dùng Pydantic, từ chối khóa lạ;
  `load_config` đọc YAML rồi áp dụng các override CLI có giá trị.
- [cli.py](../../src/visual_ad/cli.py): các lệnh `environment`, `data validate`,
  `data split`, `data prepare`; trả exit code 0 khi thành công và 2 cho lỗi dữ liệu/cấu hình.
- [common.py](../../src/visual_ad/common.py): JSON atomic, hash file, hash cấu trúc,
  thông tin môi trường và kiểm tra đường dẫn tương đối.

Ví dụ ý nghĩa override:

```python
config = load_config("configs/data.yaml", data_root="/local/mvtec")
```

Chỉ data root thay đổi; seed và các giá trị còn lại đến từ YAML. Khóa không được
khai báo bị từ chối để lỗi gõ nhầm như `image_szie` không âm thầm dùng default.
Tỷ lệ chia tập cố định trong protocol, không có nút tùy ý đổi tỷ lệ giữa các run.

JSON ghi vào file tạm cùng thư mục rồi `os.replace` để người đọc không thấy nửa
file đang ghi. Đây là atomic ở cấp một file, chưa phải transaction cho toàn bộ
output directory. Người chạy cần đọc `last-status.json` để biết lần chạy cuối đã
hoàn thành hay chưa. Giai đoạn 1 giả định một process ghi mỗi output directory.

## 5. Lý do lựa chọn và trade-off

Giai đoạn này dùng NumPy, Pillow, Pydantic và PyYAML. Không cần GPU/PyTorch để kiểm
tra ảnh và split; bộ cài nhẹ giúp lặp vòng kiểm thử nhanh và giảm rủi ro xung đột
môi trường notebook. Dependency ML sẽ được resolve và kiểm chứng ở giai đoạn model.

`argparse` đủ cho bốn lệnh hiện tại nên không cần thêm framework CLI. JSON dễ
inspect trong notebook và diff; CSV dành cho đọc thống kê bằng công cụ khác.

Python hỗ trợ 3.11–3.12. Môi trường được kiểm chứng hiện tại là Python 3.12.13;
lockfile có marker NumPy khác nhau theo phiên bản Python. Chưa tuyên bố đã chạy
test thực tế trên Python 3.11.

## 6. Cách chạy và tái lập

```bash
uv sync --extra dev --frozen
uv run --frozen vad environment
uv run --frozen vad data prepare --config configs/data.yaml --root /path/to/mvtec --output outputs/prepared
uv run --frozen pytest -q
```

`uv.lock` khóa cả môi trường phát triển. `requirements-kaggle.lock` chỉ khóa
runtime tối thiểu và không chứa đường dẫn editable tới repo local. Khi thay đổi
dependency, cập nhật cả hai file rồi kiểm thử lại; không tự nâng version trên Kaggle.

## 7. Kiểm chứng thực tế

Toàn bộ suite giai đoạn 1: **28 tests pass**. Có test gọi executable `vad` thật,
kiểm tra config sai, pipeline prepare, report output và từ chối đổi seed trong
output directory đã dùng. Kết quả chi tiết tại [nghiệm thu](phase-01-acceptance.md).

Wheel đã build thành công, được cài trong virtual environment sạch ngoài repo
và CLI chạy thành công trên 450 ảnh fixture. Đây là kiểm chứng packaging và luồng
dữ liệu, không phải benchmark mô hình.

## 8. Vấn đề và bài học

Trong bước khởi tạo trước khi thu hẹp phạm vi, bộ cài ML thử nghiệm bị xung đột
yêu cầu Lightning với Anomalib. Quá trình cài lớn đã dừng khi bạn yêu cầu chỉ làm
giai đoạn 1; dependency ML và bản nháp evaluator/config training đã được rút khỏi
phạm vi giao hàng. Chưa khóa hay kiểm chứng bộ dependency huấn luyện.

Bài học: cài thành công không đồng nghĩa model hoạt động; cần smoke test riêng
cho từng framework và chỉ đưa dependency vào bước thật sự dùng đến nó.

## 9. Tự kiểm tra

1. **Vì sao wheel không chứa dataset?** Dataset có lifecycle và kích thước riêng;
   wheel chỉ phân phối code, cần cấu hình root khi chạy.
2. **Cùng code có đủ để tái lập không?** Không; còn dependency, config, dữ liệu,
   protocol và seed.
3. **Atomic JSON có bảo đảm toàn bộ run hoàn tất không?** Không; phải kiểm tra trạng thái và các artifact liên quan.
4. **Vì sao test CLI từ ngoài repo?** Để phát hiện lỗi đóng gói/import bị repo root che khuất.

## 10. Bước tiếp theo

Đưa wheel, config và lockfile vào bundle Kaggle. Notebook bước 02 sẽ cài package,
gọi CLI này và lưu bằng chứng từ chính môi trường đang chạy.
