# Phát hiện, phân tách và đếm đồng xu

Bài tập lớn **Xử lý ảnh số** dùng Python, OpenCV, NumPy, Pandas và Streamlit. Đầu vào là **ảnh tĩnh**, gồm ảnh chụp từ trên xuống trên băng chuyền. Chương trình không theo dõi hoặc đếm cộng dồn video.

## Chạy trên Windows

Mở terminal tại thư mục dự án:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Truy cập **http://localhost:8501**. Nếu đã có thư viện, dùng `python -m streamlit run app.py`. Mã được kiểm tra bằng Python 3.14 trên máy hiện tại. Không cần training.

## Chức năng

- Tải ảnh JPG/PNG hoặc chọn 11 ảnh demo có sẵn.
- Otsu Threshold, tự động chọn chiều tương phản theo viền ảnh.
- Opening, Closing, lấp lỗ kín và lọc vùng nhỏ.
- Một luồng cố định dùng đủ Thresholding, Morphology, Connected Components, Watershed và Contour Analysis.
- Đánh ID, tâm, diện tích, chu vi, đường kính tương đương, đường kính bao ngoài, độ tròn và cờ sát biên.
- Xuất CSV và ảnh kết quả; hiệu chuẩn mm/pixel là tùy chọn khi có vật chuẩn.
- Xem các ảnh trung gian, marker và nhãn đối tượng.
- Đánh giá cả bộ ảnh bằng MAE, % ảnh đếm đúng/thiếu/thừa, thời gian và thống kê theo nhóm.

## Kịch bản demo

1. Chọn `separated` để xem ID và thông số từng xu.
2. Chọn `touching_pair` hoặc `touching_three`: chương trình tự dùng Watershed để tách xu dính. Xem số vùng trước phân tách và số xu cuối.
3. Xem ảnh Threshold, Morphology, Distance Transform, Marker và nhãn.
4. Thử `mixed_sizes`, `dark_coins`, `border`, `empty` và `noise`.
5. Thử `overlap_limit` như trường hợp ngoài phạm vi chính. Đếm đúng ảnh tổng hợp này không chứng minh xử lý được chồng lấn thật.
6. Tải ảnh chụp thật và xuất kết quả. Không cần chọn phương pháp hay chỉnh tham số. Có vật chuẩn thì mở mục đổi kích thước sang mm và nhập chiều dài đo trên chính ảnh đó.

## Thuật toán

Luồng cố định: BGR → grayscale → Gaussian 5×5 → Otsu → opening/closing → lấp lỗ → loại vùng nhỏ → Connected Components → Distance Transform/marker → Watershed → Contour Analysis → đếm và đo.

| Kỹ thuật | Vai trò | Nhận xét |
| --- | --- | --- |
| Thresholding | Tách nền bằng Otsu | Ngưỡng cường độ được tính từ ảnh |
| Morphology | Opening/Closing | Kernel elip 3×3, lấp lỗ và lọc vùng dưới 150 pixel² |
| Connected Components | Tìm vùng ban đầu | Một vùng có thể gồm nhiều xu chạm nhau |
| Watershed | Phân tách vùng có nhiều marker | Khoảng cách marker cố định hệ số 1.0 |
| Contour Analysis | Lấy đường bao và đo | Phân tích từng nhãn sau phân tách |

Các hằng số nằm trong `Config` của mã xử lý; giao diện không có bảng chọn thuật toán hoặc thanh chỉnh tham số. Cấu hình cố định cần điều kiện chụp tương đối ổn định và không đảm bảo đúng với mọi ảnh.

Marker được tìm riêng từng cụm từ cực đại cục bộ của Distance Transform, rồi loại cực đại quá gần dựa trên bán kính. Chương trình chạy **Watershed trên mask ba kênh**: biên mask giữ nền bên ngoài, nội vùng được chia theo sự lan truyền marker. Distance Transform dùng tạo marker. Đây là xấp xỉ hình học; biên phân chia không đảm bảo đúng với biên thật và marker sai có thể gây tách thừa/thiếu.

Với xu sáng gần màu nền, Otsu trực tiếp có thể mất vùng xu và nhận nhầm nền. Khi độ tròn trung bình có trọng số diện tích sau phân tách dưới 0.72, chương trình thử **gradient hình thái → Otsu → Closing → contour lồng nhau → convex hull** để khôi phục các viền tròn có đủ hỗ trợ. Chỉ dùng mask mới nếu diện tích còn ít nhất một nửa mask cũ và độ tròn tăng hơn 0.12. Các tiêu chí này là heuristic cố định, không phải xác suất đúng. Không dùng Hough hay AI. Vùng khôi phục là xấp xỉ theo đường viền, nên diện tích/kích thước cần đánh giá sai số riêng. Giao diện hiển thị thông báo khi dùng cách khôi phục này.

### Các đại lượng

- `area_px2`: số pixel trong nhãn.
- `perimeter_px`: chu vi đường bao.
- `equiv_diameter_px = 2*sqrt(area_px2/pi)`.
- `circularity = 4*pi*contourArea/perimeter²`: diện tích và chu vi cùng đường bao.
- `width_px`, `height_px`: kích thước hộp bao, không phải đường kính thật.
- Với `s = mm/pixel`: `D_mm = D_px*s`, `A_mm2 = A_px2*s²`.
- `touches_border`: đối tượng bị cắt mép; loại khỏi đánh giá kích thước đầy đủ.

Pixel đường chia Watershed bị loại khỏi nhãn nên diện tích có thể giảm nhẹ. Chưa hiệu chuẩn thì cột mm để trống. Xu chồng lấn chỉ đo được phần phân đoạn nhìn thấy.

## Dữ liệu và đánh giá

[dataset/demo](dataset/demo) chứa **11 ảnh tổng hợp**, dùng kiểm tra/demo, không đại diện độ chính xác ảnh thật. Có thể tạo lại:

```powershell
python tools/generate_demo.py
```

Đưa ảnh thật vào [dataset/real](dataset/real), điền [ground_truth.csv](dataset/real/ground_truth.csv):

```csv
image_name,actual_count,group,notes
A_01.jpg,5,separated,nen toi
B_01.jpg,6,touching,hai cap xu cham nhau
```

Nên tự chụp 60–100 ảnh: xu riêng, cụm 2–3 xu chạm, nhiều kích thước, bóng/ánh sáng thay đổi, nền sáng/tối, ảnh trống và xu sát biên. Nhóm chồng lấn đánh giá riêng. Giữ riêng tập chỉnh tham số và tập đánh giá cuối dù không huấn luyện mô hình; không điều chỉnh từng ảnh trong tập đánh giá cuối rồi báo cáo như cấu hình cố định.

Chạy giao diện hoặc terminal:

```powershell
python evaluate.py --dataset dataset/demo --output results/demo
python evaluate.py --dataset dataset/real --output results/real
```

Xuất `details.csv`, `summary.csv`, `by_group.csv`, `config.json`. Mỗi ảnh chạy đúng một luồng xử lý, không so sánh phương pháp. Thời gian gồm thuật toán và tạo ảnh minh họa, không gồm đọc ảnh/giao diện; mỗi ảnh chạy một lần nên thời gian chỉ tham khảo.

**MAE** = trung bình |số dự đoán − số thật|; **exact_percent** = % ảnh đếm đúng hoàn toàn. Đây là chỉ số đếm, không phải precision/recall phát hiện từng xu. Đánh giá phân đoạn cần mask thật, đánh giá kích thước cần số đo tham chiếu; hai phần này chưa tự động hóa.

## Kiểm tra

```powershell
python -m unittest discover -s tests -v
```

Kiểm tra ảnh trống, xu riêng/chạm, nhiều kích thước, xu tối, cắt biên, nhiễu, phép đo và ảnh lỗi. Có thêm ảnh thật hồi quy tại [four_coins.jpg](tests/fixtures/four_coins.jpg), kiểm tra cả vị trí từng xu và không nhận nhầm nền, vì tổng số đúng chưa đủ. Kiểm thử giao diện dùng Streamlit AppTest. Các ảnh tổng hợp và một ảnh thật chưa đại diện cho độ chính xác tổng quát.

## Mã nguồn

- [app.py](app.py): giao diện tiếng Việt.
- [pipeline.py](coin_counter/pipeline.py): thuật toán độc lập giao diện.
- [evaluation.py](coin_counter/evaluation.py): đánh giá và tổng hợp chỉ số.
- [evaluate.py](evaluate.py): đánh giá qua terminal.
- [generate_demo.py](tools/generate_demo.py): tạo ảnh tổng hợp.
- [tests](tests): kiểm thử.
- [Khung báo cáo](docs/BAO_CAO.md): nội dung để hoàn thiện báo cáo môn học.

## Giới hạn

Ưu tiên ảnh gần vuông góc, nền tương phản, ánh sáng đều. Phản sáng mạnh, bóng đổ, nền họa tiết, che khuất hoặc marker không ổn định có thể làm sai kết quả. Tự chọn nền giả định phần lớn viền ảnh là nền; cần chụp lại khi giả định này không phù hợp. Chưa nhận diện mệnh giá, tính tổng tiền hay theo dõi băng chuyền bằng video.
