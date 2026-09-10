# Kế hoạch xây dựng Visual Anomaly Detection: benchmark 4 phương pháp và demo mô hình được chọn

## 1. Mục tiêu và các quyết định đã chốt

Xây dựng một hệ thống hoàn chỉnh từ chuẩn bị dữ liệu, chạy thí nghiệm, so sánh phương pháp đến trình diễn mô hình được chọn qua ứng dụng web.

Các quyết định:

- Dữ liệu ban đầu: **MVTec AD, đủ 15 category**.
- So sánh **PatchCore, PaDiM, FastFlow và EfficientAD** thông qua Anomalib.
- Train và chạy thí nghiệm trên **GPU cloud/Colab**.
- Demo chạy trên **CPU máy cá nhân**, với frontend và backend API riêng.
- Ưu tiên cân bằng chất lượng phát hiện và định vị; tốc độ CPU và bộ nhớ quyết định giữa các phương pháp có chất lượng gần nhau.
- Sử dụng **tập lựa chọn mô hình và tập kiểm thử cuối độc lập**.
- Chọn **một phương pháp chung** cho demo; phương pháp đó có artifact riêng cho từng category.

“Tốt nhất” chỉ có nghĩa là tốt nhất trong bốn phương pháp, cấu hình và protocol đã khảo sát. Không mặc định PatchCore hay bất kỳ phương pháp nào sẽ thắng.

## 2. Thiết kế hệ thống

### Công nghệ và tổ chức

- Python, PyTorch và Anomalib cho mô hình.
- FastAPI và Pydantic cho backend.
- React, TypeScript và Vite cho frontend.
- YAML cho cấu hình; CLI cho các tác vụ dữ liệu, thí nghiệm và đóng gói.
- Pytest cho backend/pipeline; Vitest và Playwright cho giao diện.
- Lưu thí nghiệm bằng manifest, JSON, CSV và artifact trên filesystem; đồng bộ thư mục output sang bộ nhớ bền vững khi chạy Colab.

Khóa phiên bản dependency sau khi chạy smoke test cả bốn phương pháp trên môi trường mục tiêu. Lưu lockfile riêng cho môi trường GPU nghiên cứu và CPU demo, bảo đảm đọc được cùng artifact.

Các thành phần chính:

1. **Data adapter:** chuyển dữ liệu nguồn sang schema chung.
2. **Model adapter:** bọc implementation Anomalib sau interface thống nhất.
3. **Experiment runner:** fit, calibration, predict, đo tài nguyên và lưu kết quả.
4. **Evaluator và selector:** tính metric, so sánh và chọn phương pháp.
5. **Artifact registry:** quản lý model theo phương pháp, category và phiên bản.
6. **API và frontend:** đọc báo cáo benchmark và chạy inference.

Notebook Colab chỉ gọi các chức năng của package; logic huấn luyện và đánh giá nằm trong mã nguồn để chạy được ngoài notebook.

### Interface cần có

Giữ định hướng canonical sample/prediction trong tài liệu hiện tại, bổ sung:

- Sample có `dataset_version`, `split_role` và `sample_id` ổn định.
- Phân biệt các vai trò `fit`, `validation_normal`, `calibration_normal`, `selection`, `final_test`.
- Prediction giữ raw image score và raw anomaly map; threshold và heatmap hiển thị là các bước riêng.
- Model adapter cung cấp `fit`, `predict`, `save`, `load` và metadata.
- Run manifest ghi model/config/dataset/split/seed/dependency/hardware và trạng thái chạy.
- Deployment manifest ghi phương pháp được chọn, artifact từng category, threshold, preprocessing và kết quả đo CPU.

Model không đọc cấu trúc thư mục MVTec trực tiếp. Evaluator không phụ thuộc vào tên phương pháp.

### CLI dự kiến

Cung cấp các tác vụ:

- `data validate`: kiểm tra dataset và tạo thống kê.
- `data split`: sinh manifest chia dữ liệu cố định.
- `experiment run`: chạy một model/category/seed.
- `benchmark run`: điều phối nhiều run và tiếp tục các run còn thiếu.
- `benchmark report`: tổng hợp metric và failure cases.
- `model select`: áp dụng quy tắc lựa chọn.
- `model evaluate-final`: đánh giá cấu hình đã đóng băng.
- `model package`: đóng gói artifact CPU demo.

## 3. Dữ liệu, thí nghiệm và quy tắc chọn mô hình

### Chia dữ liệu

Dùng manifest cố định, seed chia dữ liệu `42`, dùng chung cho tất cả phương pháp:

- `train/good` gốc: **70% fit, 15% validation normal, 15% calibration normal**.
- `test` gốc: **40% selection, 60% final test**.
- Chia test theo category và defect type, gồm cả nhóm `good`; mỗi nhóm có ít nhất hai mẫu phải xuất hiện ở cả hai tập.
- Kiểm tra trùng ảnh bằng checksum trước khi chia. Trường hợp không thể chia một nhóm quá nhỏ phải được ghi rõ trong manifest và báo cáo.

Vai trò từng tập:

- **Fit:** học weights, feature statistics hoặc memory bank.
- **Validation normal:** phục vụ validation cần thiết của implementation; không dùng để xếp hạng bằng nhãn lỗi.
- **Calibration normal:** xác định threshold và thang hiển thị.
- **Selection:** chọn phương pháp.
- **Final test:** đánh giá một lần sau khi chốt phương pháp và cấu hình.

Đây là protocol riêng của project. Báo cáo phải ghi rõ kết quả **không tương đương benchmark dùng toàn bộ test chuẩn MVTec AD**.

### Bốn phương pháp

- **PatchCore:** đại diện cách lưu patch feature normal và tìm láng giềng.
- **PaDiM:** đại diện mô hình hóa phân bố feature bằng thống kê.
- **FastFlow:** đại diện normalizing flow.
- **EfficientAD:** đại diện student–teacher kết hợp thông tin toàn cục, hướng tới inference nhanh.

Dùng implementation Anomalib và lưu rõ phiên bản. Với EfficientAD, chuẩn bị teacher weights và nguồn ảnh phụ trợ mà implementation yêu cầu; ghi nguồn dữ liệu, preprocessing và fingerprint trong manifest.

Không ép tất cả phương pháp dùng cùng backbone hoặc loss. So sánh các pipeline hoàn chỉnh trong điều kiện dữ liệu đầu vào và đánh giá thống nhất; báo rõ khác biệt về pretraining và dữ liệu phụ trợ.

### Cấu hình và ngân sách chạy

- Input chung: RGB `256 × 256`, resize toàn ảnh, không center crop.
- Mask dùng nearest-neighbor khi biến đổi hình học.
- Đánh giá localization tại kích thước ảnh gốc bằng cách đưa score map về tọa độ gốc.
- Giữ normalization và score aggregation phù hợp từng implementation, ghi đầy đủ trong config.
- PatchCore: coreset ratio ban đầu `0.1`.
- EfficientAD: biến thể small.
- PaDiM và FastFlow: backbone ResNet-18.
- PatchCore: backbone Wide-ResNet-50-2.
- Tham số còn lại lấy từ cấu hình chính thức của phiên bản Anomalib đã khóa, được xuất thành YAML đầy đủ trước benchmark.

Smoke test quyết định giới hạn batch size và ngân sách huấn luyện phù hợp GPU thực tế; chỉ dùng dữ liệu fit/validation normal. Đóng băng cấu hình trước khi xem kết quả selection, không tự động giảm resolution hoặc số dữ liệu khi một run gặp lỗi.

Trình tự chạy:

1. Smoke test trên `bottle`, `carpet`, `transistor`, một seed.
2. Chạy cả 15 category, seed `42`: **60 run**.
3. Chạy thêm seed `43`, `44`: **120 run**.
4. Tổng benchmark chính: **180 run**, mỗi phương pháp có 45 run.

Checkpoint và memory bank lưu sau từng run. Phương pháp có training theo epoch lưu checkpoint định kỳ để phục hồi sau khi Colab ngắt kết nối. Báo riêng thời gian phục hồi và tổng tài nguyên tiêu thụ.

### Metric và threshold

Báo cáo theo category, từng seed và macro average:

- Image AUROC, image AP.
- Pixel AUROC, pixel AP.
- AUPRO với giới hạn FPR `0.3`.
- Image precision, recall, F1 và confusion matrix tại threshold đã calibration.
- Thời gian fit, kích thước artifact, RAM/VRAM peak.
- CPU latency p50/p95 và throughput, batch size `1`.

Threshold:

- Image threshold: quantile `0.99` của image score trên calibration normal.
- Pixel threshold: quantile `0.995` của pixel score trên calibration normal.
- Lưu threshold riêng theo model/category/seed.
- Đây là ngưỡng thực nghiệm; không diễn giải thành bảo đảm false-positive rate ngoài thực tế.

Không dùng min-max theo từng ảnh để tính metric hoặc threshold. Heatmap hiển thị dùng thang màu cố định đã calibration và có chú giải.

### Quy tắc chọn phương pháp

Tính trên selection:

`Q = 0.5 × macro(image AUROC) + 0.5 × macro(AUPRO@0.3)`

Các metric dùng thang `[0, 1]`; lấy trung bình qua ba seed.

1. Chỉ phương pháp hoàn thành đủ category/seed, artifact hợp lệ và chạy được trên CPU mới đủ điều kiện.
2. Xác định `Q_max`.
3. Tập ứng viên gồm các phương pháp có `Q ≥ Q_max − 0.005`.
4. Trong tập này, chọn phương pháp có trung bình CPU p95 latency qua 15 category thấp nhất.
5. Nếu latency chênh dưới 5%, chọn phương pháp có peak RAM thấp hơn; nếu vẫn bằng nhau, chọn phương pháp có `Q` cao hơn.

Đo CPU trên cùng máy, cùng số thread, `batch_size=1`, 20 lượt warm-up và 200 lượt đo/category. Tách thời gian nạp artifact khỏi inference; inference đo cả preprocessing, model và postprocessing.

Báo cáo giữ cả bảng xếp hạng chất lượng và lý do lựa chọn demo. Mốc `0.005` là chính sách thực dụng của project, không phải kiểm định ý nghĩa thống kê.

Sau khi chọn:

- Đóng băng phương pháp và config.
- Dùng artifact seed `42` cho demo, tránh chọn seed theo kết quả đẹp nhất.
- Đánh giá final test cho cả bốn phương pháp để có bảng so sánh cuối, nhưng **không chọn lại phương pháp dựa trên final test**.
- Báo riêng hiệu năng cuối của artifact seed `42` thực sự được demo.
- Nếu final test cho thấy hạn chế, trình bày hạn chế và tạo vòng nghiên cứu mới với holdout mới.

## 4. Frontend, API và trải nghiệm demo

### Trang so sánh phương pháp

Hiển thị:

- Bốn phương pháp, trạng thái đủ/thiếu run.
- Bộ lọc category, seed và partition.
- Metric trung bình và độ biến thiên qua seed.
- Biểu đồ chất lượng so với latency, tài nguyên và kích thước artifact.
- Kết quả theo category để thấy điểm yếu bị trung bình tổng che khuất.
- Phương pháp được chọn, công thức `Q`, nhóm ứng viên và lý do phân xử.
- Nhãn rõ ràng cho selection và final test.

Trang này đọc kết quả thí nghiệm đã lưu; không chạy training từ trình duyệt.

### Trang phân tích lỗi

- Xem ảnh gốc, ground truth, anomaly map và predicted mask của từng phương pháp.
- Lọc true positive, false positive, false negative và true negative.
- Xem cùng một sample qua bốn phương pháp.
- Hiển thị raw score và threshold, không so trực tiếp raw score giữa các model như thể cùng thang đo.
- Các ví dụ minh họa sử dụng dữ liệu selection; final test chỉ dùng trong phần báo cáo đánh giá cuối.

### Trang demo

- Chọn category thuộc MVTec AD.
- Tải PNG/JPEG hoặc chọn ảnh mẫu cục bộ.
- Xem OK/NG, image score, threshold, heatmap, predicted mask và latency.
- Điều chỉnh opacity overlay.
- Xem tên phương pháp và phiên bản artifact đang chạy.
- Tải kết quả dạng ảnh và JSON.

Người dùng phải chọn category; v1 chưa tự nhận diện loại sản phẩm. UI giải thích score là điểm bất thường, không phải xác suất sản phẩm hỏng.

### API tối thiểu

- `GET /health`: trạng thái dịch vụ.
- `GET /api/v1/models`: phương pháp được chọn và category có artifact.
- `GET /api/v1/benchmarks`: báo cáo so sánh đã xuất.
- `GET /api/v1/examples`: metadata ảnh mẫu được cấu hình.
- `POST /api/v1/predict`: nhận file ảnh và category; trả prediction cùng visualization.

Backend kiểm tra file ảnh, giới hạn upload 10 MB và 25 megapixel sau decode; lỗi ảnh hỏng, category không hỗ trợ hoặc thiếu artifact trả thông báo rõ ràng.

Chỉ nạp artifact đã đăng ký trên server. Cache tối đa hai category, xử lý inference tuần tự trong v1 để kiểm soát RAM trên máy cá nhân. UI hiển thị trạng thái đang nạp model khi chuyển category.

## 5. Các giai đoạn triển khai và điều kiện nghiệm thu

### Giai đoạn 1 — Nền tảng dự án và dữ liệu

Thiết lập package, config, CLI, dependency lock, adapter MVTec và split manifest. Cập nhật tài liệu hiện tại theo protocol đã chốt.

**Nghiệm thu:** kiểm tra đủ 15 category; split tái lập; không giao nhau; mask đúng ảnh; không có test data đi vào fit hoặc calibration.

### Giai đoạn 2 — Pipeline đầu tiên với PatchCore

Hoàn thiện luồng fit → calibration → predict → evaluate → save/load. Xây evaluator và format output dùng chung trước khi thêm các model còn lại.

**Nghiệm thu:** một category chạy xuyên suốt từ CLI; artifact tải lại trên CPU cho score tương đương trong sai số cho phép.

### Giai đoạn 3 — Tích hợp đủ bốn phương pháp

Thêm các adapter, teacher/data phụ trợ cho EfficientAD và notebook Colab. Chạy smoke test, ghi tài nguyên và khóa cấu hình chính thức.

**Nghiệm thu:** cả bốn phương pháp tạo cùng loại prediction, save/load được và phục hồi run bị ngắt theo khả năng tương ứng.

### Giai đoạn 4 — Benchmark và chọn phương pháp

Chạy 180 run, tổng hợp selection, profile CPU, áp dụng selector và đóng băng manifest demo.

**Nghiệm thu:** đầy đủ run hoặc báo rõ run lỗi; không âm thầm loại category; kết quả selector tái lập từ cùng report.

### Giai đoạn 5 — Kiểm thử cuối và phân tích

Chạy final test với cấu hình đã đóng băng; xuất báo cáo per-category, mean/std, failure cases và giới hạn của mô hình demo.

**Nghiệm thu:** báo cáo thể hiện rõ partition, protocol và artifact; không thay đổi lựa chọn dựa trên final test.

### Giai đoạn 6 — API và frontend

Xây trang benchmark, phân tích lỗi, demo và tích hợp artifact đã chọn. Phần giao diện có thể phát triển trong lúc benchmark chạy bằng dữ liệu fixture được đánh dấu rõ.

**Nghiệm thu:** upload ảnh → API CPU → score/mask/overlay hoạt động; báo cáo hiển thị dữ liệu thật; xử lý đúng các trạng thái lỗi.

### Giai đoạn 7 — Đóng gói bàn giao

Cung cấp hướng dẫn setup CPU, notebook cloud, lệnh tái lập, manifest deployment và kịch bản demo. Cache weights cần thiết để demo không phụ thuộc tải model lúc trình diễn.

**Nghiệm thu:** môi trường sạch có thể tải artifact, khởi động frontend/backend và chạy demo theo README.

Thời lượng dự kiến cho một người triển khai toàn thời gian: **5–7 tuần**, chưa tính thời gian chờ quota GPU. Ước lượng GPU-hours được tính từ smoke test và đưa vào báo cáo trước chiến dịch 180 run.

## 6. Kiểm thử, phạm vi v1 và khả năng mở rộng

Các kiểm thử trọng tâm:

- Dữ liệu: split không giao nhau, ghép mask đúng, ảnh normal có mask rỗng, mask thiếu không bị hiểu thành normal.
- Transform: tọa độ ảnh/mask đúng trước và sau resize.
- Metric: ví dụ tính tay; score hoàn hảo, score đảo chiều, trường hợp không có lớp dương; AUPRO đối chiếu implementation tham chiếu.
- Protocol: fit/calibration không truy cập selection/final test; selector chỉ đọc selection.
- Serialization: prediction trước/sau lưu tải nhất quán.
- Selector: kiểm thử ngưỡng `0.005`, phân xử latency/RAM và run không đầy đủ.
- API: ảnh hợp lệ, ảnh hỏng, file quá lớn, category sai, thiếu artifact.
- End-to-end: upload ảnh, hiện kết quả, đổi category và tải output.
- Colab: ngắt giữa các run rồi tiếp tục mà không ghi đè run đã hoàn thành.

CI chạy bằng fixture nhỏ trên CPU; chiến dịch GPU được điều khiển qua CLI và notebook, có manifest đầy đủ.

V1 tập trung MVTec AD và demo nghiên cứu. Chưa đưa vào webcam/video, nhận diện category tự động, đăng nhập nhiều người dùng, huấn luyện từ web hay triển khai public.

Việc nâng cấp dataset được chuẩn bị bằng adapter và schema chung. Kiểm chứng ranh giới này bằng một fixture dữ liệu theo manifest có nhãn/mask tùy chọn. VisA, MVTec LOCO AD và MVTec AD 2 là các chiến dịch tiếp theo, mỗi chiến dịch có protocol và lựa chọn mô hình riêng.

Tài liệu và cấu hình thuật toán tham chiếu [Anomalib](https://anomalib.readthedocs.io/en/stable/markdown/guides/reference/models/image/). Dataset và evaluation reference lấy từ [MVTec AD chính thức](https://www.mvtec.com/research-teaching/datasets/mvtec-ad).
