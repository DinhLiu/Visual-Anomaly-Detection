# Nguồn tham khảo

Các nguồn dưới đây ưu tiên trang dataset chính thức, paper gốc và mã nguồn của
tác giả. Ngày kiểm tra liên kết: **2026-09-10**.

## Dataset

1. MVTec Software GmbH, [MVTec AD — trang dataset chính thức](https://www.mvtec.com/research-teaching/datasets/mvtec-ad).
   Trang này cung cấp download, evaluation code và license CC BY-NC-SA 4.0.
2. Bergmann et al., [MVTec AD — A Comprehensive Real-World Dataset for Unsupervised Anomaly Detection](https://openaccess.thecvf.com/content_CVPR_2019/html/Bergmann_MVTec_AD_--_A_Comprehensive_Real-World_Dataset_for_Unsupervised_Anomaly_CVPR_2019_paper.html), CVPR 2019.
3. MVTec Software GmbH, [MVTec LOCO AD](https://www.mvtec.com/research-teaching/datasets/mvtec-loco-ad).
4. Bergmann et al., [Beyond Dents and Scratches: Logical Constraints in Unsupervised Anomaly Detection and Localization](https://link.springer.com/article/10.1007/s11263-022-01578-9), IJCV 2022.
5. Zou et al., [VisA dataset — repository của nhóm tác giả](https://github.com/amazon-science/spot-diff), ECCV 2022.
6. MVTec Software GmbH, [MVTec AD 2](https://www.mvtec.com/research-teaching/datasets/mvtec-ad-2).
7. MVTec Software GmbH, [MVTec 3D-AD](https://www.mvtec.com/research-teaching/datasets/mvtec-3d-ad).

## Phương pháp

8. Defard et al., [PaDiM: a Patch Distribution Modeling Framework for Anomaly Detection and Localization](https://arxiv.org/abs/2011.08785), ICPR 2021.
9. Roth et al., [Towards Total Recall in Industrial Anomaly Detection (PatchCore)](https://openaccess.thecvf.com/content/CVPR2022/html/Roth_Towards_Total_Recall_in_Industrial_Anomaly_Detection_CVPR_2022_paper.html), CVPR 2022.
10. Amazon Research, [PatchCore — implementation của tác giả](https://github.com/amazon-research/patchcore-inspection).
11. Batzner et al., [EfficientAD: Accurate Visual Anomaly Detection at Millisecond-Level Latencies](https://openaccess.thecvf.com/content/WACV2024/html/Batzner_EfficientAD_Accurate_Visual_Anomaly_Detection_at_Millisecond-Level_Latencies_WACV_2024_paper.html), WACV 2024.
12. Nelson Brilhante, [EfficientAD — implementation cộng đồng, không chính thức](https://github.com/nelson1425/EfficientAD).

## Cách dùng tài liệu tham khảo

- Dùng paper để hiểu giả định và thuật toán.
- Dùng implementation chính thức để đối chiếu chi tiết chưa được paper mô tả hết.
- Dùng evaluation code chính thức của dataset để kiểm tra metric.
- Luôn kiểm tra lại license tại nguồn trước khi tải, phân phối hoặc dùng thương mại.
- Không sao chép một con số leaderboard nếu chưa xác nhận protocol, backbone,
  resolution, metric implementation và cách average tương ứng.
