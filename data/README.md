# Dữ liệu cục bộ

Không commit MVTec AD hoặc dữ liệu sản xuất vào Git.

Đường dẫn dataset truyền qua `configs/data.yaml` hoặc `vad data prepare --root`.
Mặc định Kaggle: `/kaggle/input/datasets/ipythonx/mvtec-ad`. Output nằm ngoài
dataset, mặc định `/kaggle/working/visual-ad`. Cấu trúc MVTec AD và quy tắc adapter được mô tả
tại [docs/knowledge/02-mvtec-ad.md](../docs/knowledge/02-mvtec-ad.md) và
[docs/knowledge/03-data-contract.md](../docs/knowledge/03-data-contract.md).

Trước khi tải hoặc sử dụng dữ liệu, đọc license tại trang chính thức. MVTec AD
hiện được phát hành theo CC BY-NC-SA 4.0 và không được mặc định là phù hợp cho
mục đích thương mại.

Chạy kiểm tra/chia dữ liệu:

```bash
uv run --frozen vad data prepare --root /path/to/mvtec-ad --output outputs/prepared
```

Manifest lưu đường dẫn tương đối và hash nội dung; không sửa tay split. Nếu dữ
liệu hoặc cấu hình thay đổi, dùng output directory mới. Ảnh trùng, thiếu mask
hoặc mask không hợp lệ sẽ dừng kiểm tra để người dùng xử lý rõ ràng.
