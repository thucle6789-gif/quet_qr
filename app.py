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
    /* Giấu phần khung kéo thả file mặc định của Streamlit để trông giống nút bấm hơn */
    div[data-testid="stFileUploaderDropzone"] {
        padding: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Quét QR Code & Nhập Dữ Liệu</h1>", unsafe_allow_html=True)

st.subheader("📸 Máy quét bằng Camera Hệ thống")

# Khởi tạo biến lưu trữ dữ liệu QR quét được trong phiên làm việc
if "qr_code_detected" not in st.session_state:
    st.session_state.qr_code_detected = ""

# Sử dụng file_uploader cấu hình chụp ảnh bằng camera sau của hệ thống
uploaded_file = st.file_uploader(
    "▶️ BẤM VÀO ĐÂY ĐỂ MỞ CAMERA HỆ THỐNG CHỤP MÃ QR", 
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=False,
    label_visibility="visible"
)

# Xử lý ngay sau khi người dùng chụp xong và bấm "Dùng ảnh"
if uploaded_file is not None:
    try:
        # Đọc ảnh vừa chụp vào OpenCV
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        opencv_img = cv2.imdecode(file_bytes, 1)
        
        # Sử dụng bộ quét QR của OpenCV để giải mã
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(opencv_img)
        
        if data:
            st.session_state.qr_code_detected = data
            st.success(f"✅ Đã nhận diện thành công Headcode từ camera: {data}")
        else:
            st.error("❌ Ứng dụng không tìm thấy mã QR trong bức ảnh vừa chụp. Vui lòng bấm mở lại camera và chụp rõ nét hơn!")
    except Exception as e:
        st.error(f"Lỗi xử lý hình ảnh: {e}")

st.markdown("---")

# --- KHU VỰC FORM ĐIỀN THÔNG TIN ---
st.subheader("📝 Thông tin bản ghi")

# Danh sách các công đoạn bạn yêu cầu để làm Dropdown
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

with st.form(key="factory_data_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    
    with col1:
        # Trường Headcode tự động điền từ QR, hoặc có thể gõ tay
        headcode = st.text_input("Headcode *", value=st.session_state.qr_code_detected)
        
        # CHUYỂN THÀNH DROPDOWN: Sử dụng st.selectbox thay cho st.text_input
        congdoan = st.selectbox("Công đoạn", options=DANH_SACH_CONG_DOAN)
        
    with col2:
        soluong = st.number_input("Số lượng", min_value=1, value=1, step=1)
        nguoibao = st.text_input("Người báo")

    submit_button = st.form_submit_button(label="💾 Gửi dữ liệu lên Google Sheet", use_container_width=True)

# --- XỬ LÝ GỬI DỮ LIỆU ---
if submit_button:
    if not headcode:
        st.error("Trường 'Headcode' đang trống. Vui lòng mở camera chụp QR hoặc điền tay.")
    elif not nguoibao:
        st.error("Vui lòng điền thông tin 'Người báo'.")
    else:
        payload = {
            "headcode": headcode,
            "soluong": int(soluong),
            "congdoan": congdoan,  # Giá trị được chọn từ danh sách dropdown sẽ gửi lên đây
            "nguoibao": nguoibao
        }
        
        with st.spinner("Đang truyền dữ liệu về hệ thống bảng tính..."):
            try:
                response = requests.post(WEB_APP_URL, json=payload)
                if response.status_code == 200:
                    st.success(f"🎉 Đã lưu thành công dữ liệu cho Headcode: {headcode}!")
                    st.session_state.qr_code_detected = "" # Đặt lại rỗng cho lượt tiếp theo
                    st.rerun() # Làm mới trang để cập nhật giao diện sạch sẽ
                else:
                    st.error(f"Lỗi phản hồi từ máy chủ (Mã lỗi: {response.status_code})")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")
