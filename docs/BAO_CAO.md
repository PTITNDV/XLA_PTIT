# Khung báo cáo bài tập lớn

## 1. Tổng quan

Tên đề tài: **Phát hiện, phân tách và đếm đồng xu trong ảnh bằng kỹ thuật xử lý ảnh số**.

Nêu bài toán, đầu vào JPG/PNG, đầu ra số xu, ID, thông số hình học và ảnh minh họa. Phạm vi: ảnh tĩnh chụp từ trên xuống, xử lý xu chạm nhau; chồng lấn mạnh là khảo sát giới hạn. Ảnh chụp trên băng chuyền vẫn được phân tích từng ảnh, chưa đếm liên tục bằng video.

## 2. Cơ sở lý thuyết

Trình bày grayscale, Gaussian, Otsu, erosion/dilation, opening/closing, liên thông 8, Distance Transform, cực đại cục bộ, marker-controlled Watershed và contour. Giải thích vì sao một vùng liên thông có thể chứa nhiều xu.

## 3. Thiết kế và cài đặt

Vẽ pipeline. Mô tả tạo marker riêng từng cụm, loại cực đại gần nhau và tham số khoảng cách. Nêu rõ Watershed chạy trên mask ba kênh, Distance Transform tạo marker. Giải thích công thức đo và giới hạn đối với xu sát biên/che khuất. Chèn ảnh giao diện và các ảnh trung gian từ chương trình.

Mô tả bước phục hồi đường viền khi Otsu trực tiếp bỏ sót xu gần màu nền: gradient hình thái, Otsu trên gradient, Closing và chọn contour/convex hull tròn. Chỉ thay mask nếu tiêu chí hình dạng cải thiện. Đây là xấp xỉ hình học; không dùng kết quả đo vùng phục hồi như số đo chính xác tuyệt đối.

## 4. Thực nghiệm

### Bộ dữ liệu

Tách rõ 11 ảnh tổng hợp có sẵn và bộ ảnh tự chụp. Ghi điều kiện camera, ánh sáng, vật chuẩn, số ảnh mỗi nhóm, số xu thật và cách tách tập chỉnh tham số/tập đánh giá cuối.

### Kết quả đếm

Điền kết quả thực tế từ CSV; không thay kết quả bằng chỉ tiêu kỳ vọng:

| Nhóm ảnh | Số ảnh | MAE | % đúng | % thiếu | % thừa | ms/ảnh |
| --- | --- | --- | --- | --- | --- | --- |
| Toàn bộ | Điền sau thực nghiệm | | | | | |
| Xu tách rời | | | | | | |
| Xu chạm nhau | | | | | | |
| Nhiều kích thước | | | | | | |

Chỉ đánh giá một luồng xử lý cố định dùng đủ năm kỹ thuật. Phân tích lỗi mask, marker, bộ lọc và che khuất. Nêu rõ cấu hình cố định, điều kiện chụp và giới hạn thực tế.

### Kết quả đo

Chọn 10–20 xu không cắt/che, hiệu chuẩn trên cùng mặt phẳng, đo đường kính tham chiếu bằng thước phù hợp. Tổng hợp sai số tuyệt đối và tương đối giữa dự đoán và số đo thật. Nếu có mask thật, bổ sung sai số diện tích/IoU. Ứng dụng chưa tự tính các chỉ số đo/phân đoạn này; cần bảng tổng hợp riêng. Đếm đúng không đảm bảo đo đúng.

## 5. Kết luận

Đối chiếu bốn yêu cầu: tách nền, xử lý xu chạm, đếm, tính diện tích/kích thước. Nêu kết quả thực nghiệm, giới hạn và hướng phát triển: video + tracking + vạch đếm, nhận dạng mệnh giá, hiệu chuẩn camera, xử lý che khuất.

## Câu hỏi bảo vệ

- Vì sao Otsu có thể sai với phản sáng?
- Opening và Closing ảnh hưởng thế nào tới xu nhỏ và vùng chạm?
- Connected Components và Contour Analysis có vai trò gì trong luồng xử lý?
- Distance Transform tạo marker như thế nào?
- Khoảng cách marker ảnh hưởng tới tách thừa/thiếu ra sao?
- Vì sao chọn mask làm địa hình Watershed, cách này có giới hạn gì?
- Diện tích pixel khác contourArea ở đâu?
- Khi nào được quy đổi pixel sang mm?
- Vì sao đếm đúng chưa chứng minh phân đoạn/đo đúng?
