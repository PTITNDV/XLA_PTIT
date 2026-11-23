# Khung báo cáo bài tập lớn

## 1. Tổng quan

**Tên đề tài:** Phát hiện, phân tách và đếm đồng xu trong ảnh.

Mô tả bốn yêu cầu: tách nền; xử lý xu chạm nhau; đếm; đo diện tích và kích thước. Phạm vi là ảnh tĩnh, không huấn luyện AI và không đếm cộng dồn từ video.

## 2. Cơ sở lý thuyết

Trình bày năm kỹ thuật: Thresholding, Morphology, Connected Components, Watershed, Contour Analysis. Giải thích ảnh xám, Gaussian Blur và Distance Transform là các bước hỗ trợ.

## 3. Cài đặt

Luồng chính: ảnh → grayscale/blur → Otsu → morphology/lấp lỗ → vùng liên thông → Distance Transform/marker → Watershed → contour → đếm và đo.

Mã giao diện ở [app.py](../app.py), mã xử lý ở [pipeline.py](../coin_counter/pipeline.py), ảnh demo ở [anhdemo](../anhdemo). Chụp giao diện, ảnh trung gian và bảng thông số để minh họa.

Với xu gần màu nền, mô tả gradient hình thái, threshold trên gradient, Closing và phân tích contour/convex hull để phục hồi vùng. Giải thích vì sao phải kiểm tra từng vùng thay vì chỉ nhìn chất lượng trung bình toàn ảnh. Vùng phục hồi là xấp xỉ, không phải hình dạng chuẩn tuyệt đối.

## 4. Thực nghiệm với 9 ảnh

Chạy từng ảnh trên giao diện. Điền số thật theo đếm tay và số dự đoán theo kết quả thực tế, không gán đáp án vào thuật toán.

| Ảnh | Số xu thật | Số chương trình đếm | Sai số tuyệt đối | Nhận xét |
| --- | --- | --- | --- | --- |
| anh_01.jpg | | | | |
| anh_02.jpg | | | | |
| anh_03.jpg | | | | |
| anh_04.jpg | | | | |
| anh_05.jpg | | | | |
| anh_06.jpg | | | | |
| anh_07.jpg | | | | |
| anh_09.jpg | | | | |
| anh_10.jpg | | | | |

Tính MAE bằng trung bình sai số tuyệt đối và tỷ lệ ảnh đếm đúng bằng số ảnh đúng chia 9. Đây là bộ ảnh demo có chọn lọc, không phải tập đánh giá độc lập. Giữ lại ví dụ sai nếu có và phân tích nguyên nhân.

Để đánh giá kích thước, cần vật chuẩn cùng mặt phẳng và số đo đường kính tham chiếu. Không suy ra độ chính xác đo từ việc đếm đúng. Nếu chỉ dùng pixel, nêu rõ đơn vị pixel và pixel².

## 5. Kết luận và bảo vệ

Đối chiếu yêu cầu, nêu giới hạn và hướng phát triển. Chuẩn bị giải thích: vì sao Otsu sai khi xu gần màu nền; opening/closing khác nhau; vì sao một vùng liên thông có nhiều xu; marker và Watershed tách xu như thế nào; khi nào đổi pixel sang mm; vì sao đếm đúng chưa chắc phân đoạn đúng.
