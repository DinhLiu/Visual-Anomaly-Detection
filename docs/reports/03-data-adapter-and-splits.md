# Bước 03 — Adapter, schema, fingerprint và chia tập

**Trạng thái:** đã triển khai và kiểm thử local. Chưa kiểm tra dữ liệu Kaggle thật.

## 1. Mục tiêu và bối cảnh

Một phép so sánh phương pháp chỉ có ý nghĩa nếu các model dùng cùng dữ liệu và
không được lợi từ test leakage. Bước này biến thư mục MVTec thành danh sách sample
có danh tính ổn định, metadata hợp lệ và vai trò split rõ ràng.

Tham chiếu nền: [MVTec AD](../knowledge/02-mvtec-ad.md),
[data contract](../knowledge/03-data-contract.md), [thí nghiệm](../knowledge/06-experimentation.md).

## 2. Kiến thức cần hiểu

**Adapter** hiểu cấu trúc dataset, còn model về sau nhận schema chung. Ví dụ tên
`ground_truth/scratch/000_mask.png` chỉ thuộc trách nhiệm adapter MVTec.

**Schema** xác định cả kiểu dữ liệu và quan hệ giữa trường: một sample anomaly
phải có mask, path phải khớp category/split/defect type; kiểm tra mỗi trường riêng
lẻ chưa đủ bảo đảm sample hợp lệ.

**Fingerprint** là SHA-256 của dữ liệu đã canonicalize. Nó giúp phát hiện nội dung
hoặc phân chia thay đổi; không thay thế việc kiểm tra logic split. Một người sửa
manifest rồi tính hash lại vẫn có thể tạo manifest sai nếu không có validation.

**Calibration** là dữ liệu để chọn threshold ở bước sau. Nếu dùng test lỗi để chọn
threshold tốt nhất, con số F1 trên chính test đó sẽ lạc quan.

## 3. Thiết kế dữ liệu

```text
Dataset root
    ↓ resolve_root: đúng một root hợp lệ
    ↓ inspect_dataset: decode + mask + duplicate + checksum
inventory.json
    ↓ make_split: phân nhóm → sort → shuffle xác định → gán vai trò
split-manifest.json
    ↓ validate_manifest / verify_files
canonical sample + report
```

[schema.py](../../src/visual_ad/schema.py) định nghĩa `SampleRecord` với:

- `sample_id`: hash rút gọn của đường dẫn tương đối, ổn định khi chuyển máy.
- `image_path`, `mask_path`: đường dẫn POSIX tương đối; từ chối tuyệt đối/`..`.
- `category`, `defect_type`, `label`, `original_split`: metadata có kiểm tra chéo.
- `original_size`: `[H, W]`, dù Pillow trả `.size` theo `(W, H)`.
- `image_hash`, `mask_hash`: SHA-256 file.
- `pixel_hash`: hash RGB đã decode và kích thước, để phát hiện ảnh giống nhau dù
  PNG được nén khác nhau.
- `split_role`: fit, validation_normal, calibration_normal, selection hoặc final_test.

Manifest cấp dataset bổ sung version, protocol, seed, danh sách category, warnings,
dataset fingerprint và split fingerprint. Không lưu absolute data root trong
manifest; `root_hint` chỉ nằm ở inventory để hỗ trợ chẩn đoán.

## 4. Chi tiết kiểm tra

[data.py](../../src/visual_ad/data.py) thực hiện:

1. Tìm category có `train/good` và `test`. Nếu có nhiều root phù hợp, dừng và nêu
   danh sách để người dùng chỉ định root cụ thể hơn.
2. Yêu cầu đủ 15 category mặc định; chế độ partial phải bật rõ ràng.
3. Decode từng PNG; từ chối ảnh hỏng, folder rỗng, cấu trúc ảnh lồng sai và định
   dạng ảnh khác trong folder mẫu.
4. Train chỉ chứa `good`. Test mỗi category phải có normal và anomaly.
5. Ghép mask bằng tên stem và `_mask.png`, không ghép theo thứ tự file.
6. Kiểm tra mask cùng kích thước, có pixel dương, giá trị thuộc `{0,1,255}`; mask
   sau đọc thành boolean. Từ chối mask không ghép được ảnh.
7. Nếu hai ảnh có cùng RGB pixels và kích thước, dừng với hai đường dẫn cụ thể.
   Không tự xóa một ảnh hoặc để chúng lọt sang các split khác nhau.
8. Khi đọc lại manifest, kiểm tra hash, sample ID, schema và vai trò split;
   `verify_files` đối chiếu file hiện tại với hash đã ghi.

Hash dataset được tính trên record đã sort theo ID; không phụ thuộc thứ tự trả
về của filesystem. Hash split bao gồm protocol và các vai trò gán cho từng ảnh.

## 5. Quy tắc chia tập và lý do

Train normal được chia riêng theo category. Với `n` mẫu:

```python
nval = max(1, int(n * 0.15))
ncal = max(1, int(n * 0.15))
nfit = n - nval - ncal
```

Ví dụ 20 ảnh cho `14/3/3`. Với 209 ảnh: `147/31/31`; tỷ lệ thực có làm tròn và
được báo bằng số lượng thật, không tuyên bố tỷ lệ chính xác tuyệt đối. Dưới ba
ảnh normal không đủ ba tập nên dừng.

Test được chia riêng theo `(category, defect_type)`, gồm `good`:

- Từ hai mẫu trở lên: selection lấy `floor(0.4 × n)`, chặn để cả hai tập có ít
  nhất một mẫu.
- Chỉ một mẫu: đưa vào final_test, ghi cảnh báo rõ ràng.

Với nhóm 5 ảnh: selection 2, final_test 3. Với nhóm 2 ảnh: mỗi tập 1. Protocol
được đặt tên `normal70-15-15_test40-60_v1` để khóa ngữ nghĩa này.

Mỗi nhóm có RNG seed suy ra từ seed chung và tên nhóm. Vì vậy thêm một nhóm mới
không làm trạng thái RNG của các nhóm cũ dịch chuyển. Trước shuffle luôn sort
theo sample ID để không phụ thuộc thứ tự inventory.

Normal fit dùng học model; validation hỗ trợ training; calibration dùng xác định
threshold. Selection sẽ chọn phương pháp, final_test chỉ kiểm chứng sau khi đóng
băng. Có dùng anomaly label ở selection, nên cần mô tả chính xác là **fit normal-only,
model selection có nhãn**, không gọi toàn bộ quy trình là hoàn toàn không giám sát.

## 6. Canonical sample và hình học

```python
sample = load_sample(root, row, image_size=256)
# image: float32 [3,256,256], RGB [0,1]
# mask: bool [256,256]
# original_size: [H,W]
```

Giai đoạn này trả NumPy array, chưa phải torch.Tensor. Model adapter sau này sẽ
chuyển tensor ở biên ML. Đây là lựa chọn có chủ ý để loader/validation chạy không
cần PyTorch, và là chi tiết cụ thể hóa schema logic trong tài liệu nền.

Ảnh dùng bilinear; mask dùng nearest-neighbor. Resize trực tiếp toàn ảnh giúp giữ
tất cả vùng lỗi nhưng có thể biến dạng aspect ratio; đây là chính sách ban đầu
đã chốt, phải dùng giống nhau cho bốn phương pháp. Metadata lưu phép resize và
kích thước gốc để evaluator sau này đưa score map về hệ tọa độ gốc.

Ảnh normal không có file mask được tạo mask toàn 0 trong RAM. Với anomaly thiếu
mask, loader báo lỗi; tuyệt đối không tự tạo zero mask khiến lỗi trở thành normal.

## 7. Cách chạy từng bước và kiểm chứng

```bash
uv run --frozen vad data validate --root /path/to/mvtec --output outputs/prepared
uv run --frozen vad data split --root /path/to/mvtec --output outputs/prepared --inventory outputs/prepared/inventory.json
```

Hoặc `data prepare` làm cả hai bước và tạo report. Output trong dataset bị từ chối
để tránh ghi đè nguồn hoặc làm scanner thấy file sinh ra. Nếu output đã chứa config
khác, chọn folder mới; không đổi seed rồi ghi đè manifest cũ.

Các kiểm thử đã pass gồm missing/empty/soft/wrong-size/orphan mask, ảnh hỏng, duplicate
pixel, root mơ hồ, thiếu category, train label sai, fingerprint bị sửa, path traversal,
singleton, ít train, thứ tự inventory đảo, chuyển root, file bị đổi sau validation,
shape/dtype/geometry và manifest immutable. Bộ test ở [tests](../../tests).

Trên fixture đủ 15 category: tổng `fit=210`, `validation_normal=45`,
`calibration_normal=45`, `selection=60`, `final_test=90`. Tổng 450, không bỏ sample.
Đây là số liệu fixture phần mềm, không phải số lượng split MVTec thật.

## 8. Vấn đề và giới hạn

- Duplicate chính xác không bao phủ near-duplicate hoặc hai góc chụp cùng vật thể.
- Dừng khi có duplicate là chính sách bảo thủ; nếu dataset thật có duplicate cần
  xử lý/ghi quyết định curate trước khi tạo version mới, không bỏ qua cảnh báo.
- Singleton có thể làm selection thiếu lớp; report cảnh báo metric có thể undefined.
- Validation đọc toàn bộ ảnh và hash nên tốn I/O lần đầu; phù hợp cỡ MVTec nhưng
  dataset lớn hơn có thể cần cache có kiểm tra invalidation.
- Giữ dữ liệu holdout độc lập bằng manifest chưa ngăn một model runner tương lai
  tự ý đọc sai role. Giai đoạn runner phải bổ sung test truy cập đúng split.

Trong test đầu, hai fixture tạo cùng root gây `FileExistsError`; tách root fixture
đã sửa lỗi. Đây là lỗi bố trí test, không thay đổi protocol hoặc nội dung dataset.

## 9. Tự kiểm tra

1. **Ảnh thay nội dung nhưng giữ tên thì sample ID có đổi không?** Không; file hash
   và dataset fingerprint đổi, nên cả ID lẫn version cần được dùng cùng nhau.
2. **Vì sao không random toàn bộ test rồi chia?** Có thể mất một defect type khỏi
   selection/final test; phân tầng giữ đại diện trong giới hạn số mẫu.
3. **Cùng seed nhưng filesystem order khác có cùng split không?** Có, implementation sort trước shuffle.
4. **Vì sao ảnh normal thiếu mask khác anomaly thiếu mask?** Normal có ground truth
   zero được suy ra theo dataset; anomaly thiếu mask là thiếu annotation bắt buộc.
5. **Vì sao final_test không xuất hiện trong montage?** Để người phát triển không
   dùng failure pattern của holdout để chỉnh pipeline trước đánh giá cuối.

## 10. Bước tiếp theo

Chạy trên Kaggle thật và xem số lượng/cảnh báo từng category. Khi dữ liệu đạt yêu
cầu, dùng manifest này cho evaluator, calibration và model adapters. Không tạo
split riêng trong từng notebook huấn luyện.
