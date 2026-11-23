"""Giao diện: python -m streamlit run app.py"""
from pathlib import Path
import cv2
import pandas as pd
import streamlit as st
from coin_counter.pipeline import Config, COLUMNS, process, read_image

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Đếm đồng xu · Xử lý ảnh số", page_icon="🪙", layout="wide")
st.title("🪙 Phát hiện và đếm đồng xu")
st.caption("Thresholding → Morphology → Connected Components → Watershed → Contour Analysis")


def show_image(image, **kwargs):
    st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if image.ndim == 3 else image, **kwargs)


def csv_bytes(frame):
    return frame.to_csv(index=False).encode("utf-8-sig")


# Fixed algorithm parameters; physical calibration is optional.
scale = 0.0
with st.expander("Đổi kích thước sang mm (tùy chọn)"):
    if st.checkbox("Có vật chuẩn cùng mặt phẳng"):
        st.caption("Đo cùng một vật chuẩn trên ảnh và ngoài thực tế.")
        real = st.number_input("Chiều dài vật chuẩn (mm)", min_value=0.01, value=20.0)
        pixels = st.number_input("Chiều dài tương ứng trên ảnh (pixel)", min_value=0.01, value=100.0)
        scale = real / pixels
        st.caption(f"Hệ số: {scale:.5f} mm/pixel")
config = Config(mm_per_pixel=scale)
analyze_tab, guide_tab = st.tabs(["Đếm đồng xu", "Giải thích các bước"])

with analyze_tab:
    st.write("Chọn ảnh để tự động đếm và đo từng đồng xu.")
    source = st.radio("Nguồn ảnh", ["Ảnh demo", "Tải ảnh của bạn"], horizontal=True)
    image = None
    name = "image"
    if source == "Ảnh demo":
        demo_folder = ROOT / "anhdemo"
        files = sorted(p for p in demo_folder.iterdir()
                       if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}) if demo_folder.is_dir() else []
        if files:
            selected = st.selectbox("Chọn ảnh demo", files, format_func=lambda p: p.stem,
                index=0)
            try:
                image, name = read_image(selected), selected.stem
            except (ValueError, OSError, cv2.error) as error:
                st.error(f"Không đọc được ảnh demo: {error}")
            st.caption(f"Có {len(files)} ảnh trong thư mục anhdemo. Chọn từng ảnh để trình bày kết quả.")
        else:
            st.info("Chưa có ảnh demo. Thêm ảnh JPG/PNG vào thư mục anhdemo hoặc tải ảnh của bạn.")
    else:
        upload = st.file_uploader("Chọn ảnh JPG/PNG", type=["jpg", "jpeg", "png"])
        if upload:
            try:
                image, name = read_image(upload.getvalue()), Path(upload.name).stem
            except (ValueError, cv2.error) as error:
                st.error(str(error))
    result = None
    if image is not None:
        if image.shape[0] * image.shape[1] > 16_000_000:
            st.error("Ảnh lớn hơn 16 megapixel. Hãy giảm kích thước trước khi tải để demo ổn định.")
        else:
            try:
                result = process(image, config)
            except (ValueError, cv2.error) as error:
                st.error(f"Không xử lý được ảnh: {error}")
    if result:
        left, middle, right = st.columns(3)
        left.metric("Số đồng xu", result["count"])
        middle.metric("Vùng trước khi tách xu dính", result["before_count"])
        right.metric("Thời gian xử lý", f'{result["elapsed_ms"]:.1f} ms')
        left, right = st.columns(2)
        with left:
            show_image(image, caption=f"Ảnh gốc · {image.shape[1]} × {image.shape[0]} pixel")
        with right:
            show_image(result["output"], caption="Đường bao xanh · Tâm đỏ · ID vàng")
        st.subheader("Thông số từng đồng xu")
        frame = pd.DataFrame(result["rows"], columns=COLUMNS)
        st.dataframe(frame, hide_index=True)
        if result["recovered_from_rims"]:
            st.caption("Đã khôi phục vùng xu theo đường viền vì độ sáng xu gần nền. Diện tích và kích thước là ước lượng từ vùng khôi phục.")
        if not scale:
            st.caption("Kích thước tính bằng pixel, diện tích bằng pixel². Chỉ quy đổi sang mm khi có vật chuẩn.")
        if not result["count"]:
            st.info("Không tìm thấy đồng xu hợp lệ. Hãy thử ảnh nền tương phản, ánh sáng đều và xu rõ nét.")
        if any(row["touches_border"] for row in result["rows"]):
            st.warning("Có xu bị cắt bởi mép ảnh; thông số của xu này chỉ mô tả phần nhìn thấy.")
        a, b = st.columns(2)
        a.download_button("Tải bảng CSV", csv_bytes(frame), f"{name}_coins.csv", "text/csv")
        b.download_button("Tải ảnh kết quả", cv2.imencode(".png", result["output"])[1].tobytes(), f"{name}_result.png", "image/png")
        with st.expander("Xem các bước xử lý ảnh"):
            steps = list(result["steps"].items())
            for offset in range(0, len(steps), 3):
                for col, (title, step) in zip(st.columns(3), steps[offset:offset + 3]):
                    with col:
                        show_image(step, caption=title)

with guide_tab:
    st.markdown("""
### Một luồng xử lý cố định
1. **Thresholding (Otsu):** tách xu khỏi nền. Tự chọn chiều sáng/tối theo viền ảnh. Threshold trên gradient hình thái hỗ trợ tìm viền tròn. Nếu một vùng tròn chỉ chứa các mảnh rời, chương trình khôi phục vùng đó trước Watershed; nếu toàn mask kém, chỉ thay mask khi chất lượng hình dạng cải thiện đủ.
2. **Morphology:** Opening, Closing và lấp lỗ để làm sạch vùng xu.
3. **Connected Components:** gán nhãn các vùng liên thông ban đầu.
4. **Watershed:** dùng marker từ Distance Transform để phân tách xu chạm nhau.
5. **Contour Analysis:** lấy đường bao, đánh ID và đo từng xu.

Ảnh xám và Gaussian Blur là bước chuẩn bị. Distance Transform hỗ trợ tạo marker cho Watershed.

### Các phép đo
- Diện tích: số pixel trong nhãn đối tượng.
- Đường kính tương đương: **D = 2√(A/π)**.
- Độ tròn: **4πA_contour/P²**.
- Với s là mm/pixel: **D_mm = D_px × s**, **A_mm² = A_px² × s²**.
- Pixel đường chia Watershed bị bỏ khỏi nhãn nên diện tích có thể giảm nhẹ.

### Chụp ảnh để đếm ổn định
Dùng nền đơn sắc tương phản, ánh sáng đều, camera nhìn từ trên xuống. Đặt xu trọn trong ảnh. Khi xu chạm nhau, cần thấy rõ hình dạng từng xu; chồng lấn che khuất mạnh có thể gây sai số.

Hệ thống dùng cấu hình cố định, không đảm bảo mọi ảnh đều đếm đúng. Tự chọn nền giả định phần lớn viền ảnh thuộc nền.

### Phạm vi và báo cáo
Xử lý ảnh tĩnh, gồm ảnh chụp trên băng chuyền; chưa đếm cộng dồn video. Ảnh demo là ảnh thật trong thư mục anhdemo. Khi viết báo cáo, ghi lại số xu thật, số chương trình đếm được và phân tích ví dụ sai; đếm đúng chưa đảm bảo đo kích thước đúng.
""")
