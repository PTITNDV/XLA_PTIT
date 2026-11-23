# Phát hiện và đếm đồng xu trong ảnh

Bài tập lớn môn **Xử lý ảnh số**. Chương trình nhận ảnh tĩnh, tự tách nền, phân tách xu chạm nhau, đếm và đo từng đồng xu. Không dùng AI, không huấn luyện mô hình.

## Chạy chương trình

Mở terminal tại thư mục dự án:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Mở **http://localhost:8501**. Dừng bằng **Ctrl+C**. Đã kiểm tra trên Python 3.14 của máy hiện tại.

Nếu muốn cài thư viện riêng cho dự án:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

## Cấu trúc

```text
app.py                    Giao diện Streamlit tiếng Việt
coin_counter/
  __init__.py
  pipeline.py             Thuật toán đếm và đo
anhdemo/                  9 ảnh thật để demo
docs/
  BAO_CAO.md              Khung nội dung báo cáo
requirements.txt          Các thư viện cần cài
README.md                 Hướng dẫn sử dụng
.vscode/tasks.json        Tác vụ chạy ứng dụng trong VS Code
```

## Cách demo

1. Chọn **Ảnh demo**, chọn lần lượt một trong 9 ảnh lấy trực tiếp từ [anhdemo](anhdemo).
2. Xem ảnh gốc, ảnh đánh ID, số xu và bảng diện tích/kích thước.
3. Mở **Xem các bước xử lý ảnh** để trình bày ảnh trung gian.
4. Tải bảng CSV hoặc ảnh kết quả nếu cần.
5. Chọn **Tải ảnh của bạn** để thử ảnh JPG/PNG khác.

Thuật toán và tham số đã cố định. Mục **Đổi kích thước sang mm** chỉ cần khi có vật chuẩn cùng mặt phẳng và đã đo được chiều dài tương ứng trên ảnh. Nếu chưa hiệu chuẩn, kết quả dùng pixel và pixel².

## Yêu cầu đối với ảnh và đồng xu

Các điều kiện dưới đây giúp chương trình hoạt động ổn định với cấu hình xử lý cố định; không đảm bảo mọi ảnh đáp ứng điều kiện đều cho kết quả đúng.

### Điều kiện ảnh đầu vào

| Đặc điểm | Yêu cầu phù hợp |
| --- | --- |
| Định dạng | Ảnh tĩnh JPG/JPEG hoặc PNG; giao diện giới hạn tối đa 16 megapixel |
| Góc chụp | Chụp gần vuông góc từ trên xuống để đồng xu nhìn gần tròn; hạn chế góc nghiêng lớn |
| Nền | Nền phẳng, đơn sắc, ít họa tiết và tương phản với đồng xu; tránh vật thể tròn khác dễ bị đếm nhầm |
| Ánh sáng | Chiếu sáng tương đối đều, hạn chế bóng đổ đậm và phản sáng làm mất đường viền |
| Độ nét | Ảnh rõ, không rung hoặc nhòe; đồng xu phải đủ lớn trên ảnh để thấy đường viền và tạo vùng liên thông ổn định |
| Bố cục | Đồng xu nằm trọn trong khung hình, có khoảng nền quanh mép ảnh; phần lớn viền ảnh cần thuộc nền để tự chọn chiều sáng/tối |

Không cần ảnh có độ phân giải quá lớn. Ảnh rõ với đường viền đầy đủ hữu ích hơn ảnh nhiều pixel nhưng bị nhòe hoặc phản sáng. Không quy định một số lượng xu tối đa cố định; khả năng xử lý phụ thuộc kích thước từng xu trên ảnh, mức độ dính và chất lượng tách nền.

### Đặc điểm và cách bố trí đồng xu

- Đồng xu có hình dạng gần tròn, đặt nằm phẳng trên cùng một mặt phẳng.
- Có thể khác kích thước, màu sắc hoặc mệnh giá. Chương trình đếm và đo hình học, chưa nhận diện mệnh giá hoặc tính tổng tiền.
- Ưu tiên các xu tách rời. Có thể chạm cạnh nhau nhưng cần còn thấy hình dạng từng xu để Distance Transform tạo marker và Watershed phân tách.
- Hạn chế xếp chồng hoặc chồng lấn che khuất nhiều. Chạm cạnh và chồng lấn là hai trường hợp khác nhau; thuật toán không đảm bảo khôi phục được phần xu đã bị che.
- Không để xu bị cắt bởi mép ảnh. Nếu có, chương trình đánh dấu `touches_border`; diện tích và kích thước chỉ mô tả phần đã phân đoạn.
- Tránh xu quá nhỏ so với toàn ảnh: bộ lọc hiện loại vùng dưới 150 pixel², và vùng chỉ vừa vượt ngưỡng này vẫn có thể không đủ chi tiết để tách, đo ổn định.

### Điều kiện đo kích thước thực

- Nếu chưa hiệu chuẩn, kết quả chỉ có đơn vị **pixel** và **pixel²**.
- Muốn đổi sang **mm** và **mm²**, cần vật chuẩn có chiều dài thật đã biết, nằm cùng mặt phẳng với đồng xu; đo chiều dài tương ứng trên chính ảnh đang xử lý.
- Giữ camera gần vuông góc và tránh méo phối cảnh lớn. Khi thay vị trí camera, khoảng cách chụp hoặc thay đổi kích thước ảnh, cần xác định lại hệ số mm/pixel.
- Xu bị che, cắt mép hoặc được khôi phục mask từ đường viền có thể có sai số đo lớn hơn. Số đếm đúng không chứng minh diện tích hoặc đường kính chính xác.

**Phạm vi đề tài:** Đếm và đo đồng xu gần tròn trên ảnh tĩnh chụp từ trên xuống, nền đơn giản, ánh sáng tương đối đều; hỗ trợ xu chạm nhau và hạn chế trường hợp chồng lấn mạnh. Chín ảnh demo là các ví dụ đã chọn để trình bày, không đại diện cho mọi điều kiện chụp.

## Năm kỹ thuật chính

| Kỹ thuật | Vai trò |
| --- | --- |
| Thresholding | Otsu tách xu khỏi nền, tự chọn chiều sáng/tối theo viền ảnh |
| Morphology | Opening, Closing, lấp lỗ; gradient hình thái hỗ trợ tìm viền |
| Connected Components | Gán nhãn vùng liên thông và đếm vùng trước phân tách |
| Watershed | Phân tách xu chạm nhau bằng marker từ Distance Transform |
| Contour Analysis | Phân tích đường bao, tính chu vi, độ tròn và kích thước |

Grayscale và Gaussian Blur là bước chuẩn bị. Khi xu gần màu nền, hệ thống kiểm tra các viền gần tròn và có thể khôi phục mask bằng contour/convex hull trước Watershed. Quy tắc kiểm tra áp dụng chung cho ảnh, không dùng tên ảnh hoặc đáp án để đếm.

## Phép đo và giới hạn

- Diện tích là số pixel trong nhãn; chu vi lấy từ contour.
- Đường kính tương đương: `D = 2*sqrt(A/pi)`.
- Độ tròn: `4*pi*contourArea/perimeter²`.
- Với `s` là mm/pixel: `D_mm = D_px*s`, `A_mm2 = A_px2*s²`.
- Xu cắt mép, che khuất, biên Watershed hoặc mask được khôi phục có thể làm sai phép đo. Đếm đúng chưa chứng minh đo đúng.

Phù hợp ảnh gần vuông góc, nền đơn giản và ánh sáng đều. Bóng đổ mạnh, phản sáng, nền họa tiết và xu chồng lấn nhiều có thể gây đếm sai. Chưa nhận diện mệnh giá, tổng tiền hoặc đếm cộng dồn băng chuyền bằng video. Các ảnh demo được chọn để trình bày, không đại diện độ chính xác tổng quát.

## Báo cáo và nguồn ảnh

Dùng [khung báo cáo](docs/BAO_CAO.md), ghi số xu đếm tay và số chương trình trả về để tổng hợp thực nghiệm. Không cần tệp nhãn hoặc bộ dữ liệu riêng để chạy ứng dụng.

Ảnh 01–07 lấy từ [HiiYL/Coin-Counting](https://github.com/HiiYL/Coin-Counting), tương ứng ảnh nguồn 1, 2, 4, 5, 6, 7, 8; đã cắt 20 pixel ở mỗi mép, không cắt xu. Ảnh 09 và 10 lấy từ [kaa/coins-dataset](https://github.com/kaa/coins-dataset), tương ứng `src/test/test_3.jpg` và `src/test/test_9.jpg`; đã giảm cạnh dài về 1280 pixel, ảnh 10 cắt thêm phần nền ngoài vùng xu. Bộ ảnh hiện có 9 tệp, không đổi số thứ tự tên ảnh.
