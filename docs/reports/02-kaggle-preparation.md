# Bước 02 — Notebook Kaggle và bundle có thể kiểm tra

**Trạng thái:** notebook chạy hết trong Jupyter local trên fixture. **Chưa chạy trên Kaggle.**

## 1. Mục tiêu và bối cảnh

Bạn đã chọn input `/kaggle/input/datasets/ipythonx/mvtec-ad`. Notebook phải chạy
được với đường dẫn đó, cho biết dữ liệu có đúng cấu trúc không và tạo output có
thể gắn sang phiên huấn luyện sau. Giai đoạn 1 chỉ cần accelerator CPU.

## 2. Kiến thức cần hiểu

Kaggle mount input riêng với output. Package không sửa ảnh trong input. Output
dự án là `/kaggle/working/visual-ad`; cần lưu phiên có output trước khi tái sử dụng.
Notebook Version còn ghi bối cảnh notebook/môi trường chạy. Cơ chế lưu và nối
output các notebook được mô tả trong [Kaggle Notebooks](https://www.kaggle.com/docs/notebooks).

Một notebook có thể chạy cell lộn thứ tự trong phiên tương tác, nhưng chỉ đáng tin
khi chạy được từ đầu với kernel sạch. Vì vậy notebook giao hàng không lưu execution
count hoặc output local dễ bị hiểu nhầm thành kết quả Kaggle.

## 3. Thiết kế

[01_prepare_mvtec_kaggle_v2.ipynb](../../notebooks/01_prepare_mvtec_kaggle_v2.ipynb) gồm:

1. Xác thực checksum bundle, cài runtime đã khóa và wheel.
2. Đọc config, xác nhận data root và output root.
3. Gọi `vad data prepare` qua `cli.main`.
4. Hiện báo cáo số lượng/fingerprint/cảnh báo và montage ảnh–mask.
5. Đọc một canonical sample để kiểm tra shape/dtype.
6. Hướng dẫn lưu output và câu hỏi tự kiểm tra.
7. Đóng gói các kết quả cần thiết thành một ZIP có checksum và tạo link tải.

Không có cell huấn luyện hoặc gallery ảnh final_test. Việc kiểm tra tự động đọc
mask/metadata toàn dataset để xác thực cấu trúc không đồng nghĩa dùng holdout để
tuning model; gallery phục vụ con người chỉ dùng fit/selection.

## 4. Chi tiết triển khai

[build_kaggle_bundle.py](../../scripts/build_kaggle_bundle.py) build wheel từ source,
copy `configs/data.yaml`, `uv.lock`, `requirements-kaggle.lock`, rồi tạo manifest
SHA-256 và ZIP. Script không upload hay gọi tài khoản Kaggle.

```python
subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(lockfile)], check=True)
```

Notebook dùng `sys.executable` để cài vào Python của kernel, tránh `pip` trên PATH
thuộc interpreter khác. Wheel được cài `--no-deps` sau runtime đã khóa; điều này
không bỏ dependency, mà ngăn pip tự resolve bộ khác với lockfile vừa cài.

Sau install, source fingerprint của module đang import phải trùng bundle. Nếu
kernel giữ module cũ trong RAM, notebook yêu cầu restart thay vì giả định import
đã cập nhật.

## 5. Lý do lựa chọn

Wheel + input bundle tránh cần GitHub token trong notebook. Source fingerprint
giúp nối report về code; checksum phát hiện file hỏng hoặc thay đổi ngoài ý muốn.
Không coi checksum là cơ chế chống bên thứ ba cố tình thay cả file và manifest.

Notebook dùng text cell giải thích trước code cell để có thể học theo từng bước.
Không tự tải dataset hoặc pretrained weights vì giai đoạn này dữ liệu đã được
gắn làm input và chưa có model.

## 6. Cách đưa lên Kaggle

Từ root repo:

```bash
uv sync --extra dev --frozen
uv run --extra dev --frozen python scripts/build_kaggle_bundle.py
```

Đầu ra: `dist/kaggle-bundle.zip`. Nếu đã có bundle cũ, script từ chối ghi đè;
chọn `--output dist/kaggle-bundle-v2` cho phiên bản mới.

Trên Kaggle:

1. Tạo Dataset private chứa nội dung ZIP, gắn vào notebook.
2. Gắn MVTec AD với đường dẫn bạn đã cung cấp.
3. Import notebook `01_prepare_mvtec_kaggle.ipynb`.
4. Đặt `BUNDLE_ROOT` đúng thư mục chứa `bundle-manifest.json` và wheel. Không giả
   định slug mount của Kaggle luôn giống tên ZIP.
5. Bật Internet để cài runtime; nếu offline cần chuẩn bị wheelhouse trước.
6. Run All, đọc cảnh báo và đối chiếu gallery.
7. Chạy cell cuối, tải ZIP kết quả, lưu phiên notebook có output rồi gắn output
   đó vào notebook giai đoạn sau.

Cell cuối tạo `visual-ad-phase1-<split-hash-12>.zip` ngay dưới `/kaggle/working`.
Link `Tải ZIP kết quả` cho phép tải trực tiếp từ notebook. ZIP chứa config,
inventory, split manifest, status, report Markdown/JSON, CSV, preview và
`checksums.json`; không chứa ảnh nguồn MVTec. Tải ZIP để lưu về máy, đồng thời
vẫn lưu Notebook Version để dùng trực tiếp làm input cho giai đoạn sau.

Biến `VAD_USE_INSTALLED_PACKAGE=1` chỉ dùng cho kiểm thử local khi package đã cài.
Notebook trên Kaggle mặc định không bỏ bước cài/xác minh bundle.

## 7. Kiểm chứng

- `nbformat.validate` xác nhận định dạng notebook.
- Test tự động thực thi mọi code cell trong namespace sạch với package đã cài.
- `scripts/verify_notebook.py` thực thi notebook bằng **kernel Jupyter riêng**.
- Dữ liệu kiểm thử: 450 ảnh RGB tổng hợp, 15 category, mỗi category 20 train normal,
  5 test normal và 5 test anomaly có mask.
- Notebook sinh đầy đủ manifest, report, CSV và montage; không có exception cell.
- Notebook đóng gói kết quả cần thiết thành ZIP, kèm checksum từng file.
- Bản notebook đã chạy được lưu ở `outputs/phase1-verification/01_prepare.executed.ipynb`.

Cài wheel trong môi trường sạch và chạy CLI cũng thành công. Bước install trong
kernel Kaggle và nội dung dataset Kaggle chưa được thực thi ở đây.

## 8. Vấn đề và giới hạn

Kernel Jupyter cần mở socket local. Lần chạy trong sandbox bị từ chối quyền socket;
sau khi chạy kiểm thử với quyền phù hợp, notebook hoàn tất. Đây là giới hạn môi
trường local, không phải lỗi dữ liệu hay lỗi cell.

Không pin một loại GPU/quota phiên vì bước này không cần GPU và tài nguyên Kaggle
có thể thay đổi. Nếu Python trên Kaggle ngoài 3.11–3.12, cell sẽ dừng để điều chỉnh
lockfile và kiểm thử lại, không tự bỏ ràng buộc phiên bản.

## 9. Tự kiểm tra

1. **Vì sao không đưa `/home/...` vào manifest?** Đường dẫn local không tồn tại trên Kaggle.
2. **File trong working đã chắc chắn tồn tại ở phiên sau chưa?** Chưa; cần lưu output và gắn lại phiên đã lưu.
3. **Notebook chạy local chứng minh Kaggle chạy được không?** Không; nó xác minh logic và kernel execution, chưa xác minh mount/runtime Kaggle.
4. **Vì sao cần restart khi fingerprint import khác bundle?** Python có thể còn cache module cũ trong kernel.

## 10. Bước tiếp theo

Chạy notebook này trên Kaggle thật. Khi có `last-status.json` thành công, report
15 category và ảnh/mask hợp lệ, dùng chính split manifest đó để xây evaluator và
chạy smoke test model ở giai đoạn 2.
