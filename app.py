import streamlit as st
import requests
import cv2
import numpy as np
from PIL import Image

# 1. Điền đường link Web App URL Google Apps Script của bạn vào đây
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxB9cagxYoxM8kpbLtkFGKoQ6SND4QNqLbPTwFR1fs0bNUH-KNDFSaYtrTxKJ8VadEv8g/exec"

st.set_page_config(page_title="Quét QR Code Hệ Thống", layout="centered")

st.markdown("""
    <style>
    .main-title { text-align: center; font-family: Arial, sans-serif; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    div[data-testid="stFileUploaderDropzone"] {
        padding: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Quét QR Code & Nhập Dữ Liệu</h1>", unsafe_allow_html=True)

st.subheader("📸 Máy quét bằng Camera Hệ thống")

# --- KHỞI TẠO CÁC BIẾN LƯU TRỮ TRẠNG THÁI ---
if "qr_code_detected" not in st.session_state:
    st.session_state.qr_code_detected = ""
if "soluong_val" not in st.session_state:
    st.session_state.soluong_val = 1.000
if "nguoibao_val" not in st.session_state:
    st.session_state.nguoibao_val = ""

# ✅ KEY: Biến đếm này được tăng lên sau mỗi lần submit thành công.
# Khi key của widget thay đổi, Streamlit tạo lại widget hoàn toàn mới => form tự clear.
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

DANH_SACH_CONG_DOAN = [
    "P013_Tạo phôi và Sơchế",
    "P014_Tinh chế và Định hình",
    "P015_Chà nhám và Bề mặt",
    "P016_Lắp ráp và Liên kết",
    "P017_Làm nguội và Hoàn thiện",
    "P018_Sơn - Màu",
    "P019_Washing - Cleaning",
    "P20_Lắp ráp hoàn thiện",
    "P021_Đóng gói hoàn thành"
]

# ✅ KEY ĐỘNG cho file uploader: thay đổi sau mỗi lần submit để reset camera upload
uploaded_file = st.file_uploader(
    "▶️ BẤM VÀO ĐÂY ĐỂ MỞ CAMERA HỆ THỐNG CHỤP MÃ QR",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=False,
    label_visibility="visible",
    key=f"camera_uploader_{st.session_state.form_key}"  # ✅ Key động
)

# Xử lý ảnh chụp từ camera
if uploaded_file is not None:
    try:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        opencv_img = cv2.imdecode(file_bytes, 1)

        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(opencv_img)

        if data:
            st.session_state.qr_code_detected = data
            st.success(f"✅ Đã nhận diện thành công Headcode: {data}")
        else:
            st.error("❌ Không tìm thấy mã QR trong bức ảnh vừa chụp. Vui lòng chụp rõ nét hơn!")
    except Exception as e:
        st.error(f"Lỗi xử lý hình ảnh: {e}")

st.markdown("---")

# --- KHU VỰC FORM ĐIỀN THÔNG TIN ---
st.subheader("📝 Thông tin bản ghi")

# ✅ KEY ĐỘNG cho form: thay đổi sau mỗi lần submit thành công
with st.form(key=f"factory_data_form_{st.session_state.form_key}", clear_on_submit=False):
    col1, col2 = st.columns(2)

    with col1:
        headcode = st.text_input(
            "Headcode *",
            value=st.session_state.qr_code_detected,
            key=f"headcode_{st.session_state.form_key}"  # ✅ Key động
        )

        congdoan = st.selectbox(
            "Công đoạn",
            options=DANH_SACH_CONG_DOAN,
            key=f"congdoan_{st.session_state.form_key}"  # ✅ Key động
        )

    with col2:
        soluong = st.number_input(
            "Số lượng",
            min_value=0.000,
            value=st.session_state.soluong_val,
            step=0.001,
            format="%.3f",
            key=f"soluong_{st.session_state.form_key}"  # ✅ Key động
        )

        nguoibao = st.text_input(
            "Người báo",
            value=st.session_state.nguoibao_val,
            key=f"nguoibao_{st.session_state.form_key}"  # ✅ Key động
        )

    submit_button = st.form_submit_button(label="💾 Gửi dữ liệu lên Google Sheet", use_container_width=True)

# --- XỬ LÝ GỬI DỮ LIỆU & RESET FORM ---
if submit_button:
    if not headcode:
        st.error("Trường 'Headcode' đang trống. Vui lòng mở camera chụp QR hoặc điền tay.")
    elif not nguoibao:
        st.error("Vui lòng điền thông tin 'Người báo'.")
    else:
        payload = {
            "headcode": headcode,
            "soluong": float(soluong),
            "congdoan": congdoan,
            "nguoibao": nguoibao
        }

        with st.spinner("Đang truyền dữ liệu về hệ thống bảng tính..."):
            try:
                response = requests.post(WEB_APP_URL, json=payload)
                if response.status_code == 200:
                    st.success("🎉 Đã up dữ liệu thành công")

                    # ✅ Reset toàn bộ: xóa session state VÀ tăng form_key
                    st.session_state.qr_code_detected = ""
                    st.session_state.soluong_val = 1.000
                    st.session_state.nguoibao_val = ""
                    st.session_state.form_key += 1  # ✅ Key mới => widget mới hoàn toàn

                    st.rerun()
                else:
                    st.error(f"Lỗi phản hồi từ máy chủ (Mã lỗi: {response.status_code})")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")
