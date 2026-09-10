# 8. Từ benchmark tới vận hành

## 8.1 Đơn vị quyết định thật sự

Trong dây chuyền, output thường không chỉ là “anomaly score” mà là một hành động:

- cho sản phẩm đi tiếp;
- loại sản phẩm;
- dừng line;
- chuyển ảnh/sản phẩm sang người kiểm tra.

Threshold phải tối ưu theo chi phí của hành động này. False negative có thể làm
lọt lỗi; false positive có thể làm tăng phế phẩm hoặc nghẽn dây chuyền.

## 8.2 Pipeline inference

```text
camera → quality gate → preprocessing → model → calibration
       → post-processing → business rule → log/alert/review
```

`quality gate` nên phát hiện ảnh mờ, cháy sáng, thiếu vật thể hoặc camera lệch.
Những lỗi thu nhận này cần được phân biệt với defect sản phẩm khi có thể.

## 8.3 Calibration và vùng không chắc chắn

Thay vì một threshold duy nhất, có thể dùng hai ngưỡng:

- score thấp: tự động OK;
- score cao: tự động NG;
- ở giữa: kiểm tra thủ công.

Thiết kế này biến uncertainty thành quy trình an toàn hơn, đồng thời tạo dữ liệu
có giá trị cho vòng cải tiến tiếp theo.

## 8.4 Domain shift và drift

Nguồn shift thường gặp:

- thay camera, lens, exposure hoặc firmware;
- thay góc đặt và khoảng cách;
- ánh sáng, rung, bụi;
- lô vật liệu, màu sắc, nhà cung cấp;
- hao mòn máy và thay đổi quy trình;
- product variant mới.

Theo dõi score distribution trên normal đã xác nhận, tỷ lệ cảnh báo, image
quality và metadata theo thời gian. Drift alarm không tự động chứng minh model
sai; nó báo cần điều tra hoặc recalibration.

## 8.5 Phản hồi và nhãn

Mỗi quyết định nên lưu:

- ảnh hoặc tham chiếu ảnh theo chính sách dữ liệu;
- raw score/map;
- threshold và model version;
- quyết định tự động;
- kết luận của người kiểm tra nếu có;
- camera/line/batch/timestamp.

Tách “model prediction” khỏi “final disposition” để có thể audit. Nhãn do người
vận hành sửa cần quy trình kiểm soát chất lượng, không đưa thẳng vào train.

## 8.6 Tiêu chí trước pilot

- Test trên dữ liệu nội bộ độc lập theo thời gian/lô.
- Có acceptance criteria gắn với chi phí false positive/negative.
- Có kiểm thử lỗi camera và input ngoài chuẩn.
- Latency p99 nằm trong cycle time.
- Artifact có version và rollback được.
- Có shadow mode trước khi tự động loại sản phẩm.
- Có owner xử lý cảnh báo, drift và incident.
- Kiểm tra license của dataset, backbone, weights và dependency.

## 8.7 Model card tối thiểu

Mỗi model phát hành nên mô tả intended use, dữ liệu, metric, threshold, phần cứng,
giới hạn, failure modes, version và người phê duyệt. Heatmap là công cụ hỗ trợ
điều tra, không mặc định là lời giải thích nhân quả cho quyết định của model.
