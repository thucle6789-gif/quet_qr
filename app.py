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

# --- KHỞI TẠO CÁC BIẾN LƯU TRỮ TRẠNG THÁI FORM (SESSION STATE) ---
if "qr_code_detected" not in st.session_state:
    st.session_state.qr_code_detected = ""
if "soluong_val" not in st.session_state:
    st.session_state.soluong_val = 1.000   # Mặc định ban đầu là dạng số lẻ
if "nguoibao_val" not in st.session_state:
    st.session_state.nguoibao_val = ""

# Thiết lập bộ upload ảnh từ camera hệ thống
uploaded_file = st.file_uploader(
    "▶️ BẤM VÀO ĐÂY ĐỂ MỞ CAMERA HỆ THỐNG CHỤP MÃ QR", 
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=False,
    label_visibility="visible"
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

# Sử dụng st.form để bọc các ô nhập liệu
with st.form(key="factory_data_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    
    with col1:
        # Nhận giá trị Headcode từ bộ nhớ tạm session_state
        headcode = st.text_input("Headcode *", value=st.session_state.qr_code_detected)
        
        # Danh sách chọn công đoạn
        congdoan = st.selectbox("Công đoạn", options=DANH_SACH_CONG_DOAN)
        
    with col2:
        # CẢI TIẾN SỐ LƯỢNG: Đổi sang định dạng số thực (float), định dạng hiển thị 3 chữ số thập phân (%.3f)
        soluong = st.number_input(
            "Số lượng", 
            min_value=0.000, 
            value=st.session_state.soluong_val, 
            step=0.001, 
            format="%.3f"
        )
        
        # Nhận giá trị Người báo từ bộ nhớ tạm session_state
        nguoibao = st.text_input("Người báo", value=st.session_state.nguoibao_val)

    submit_button = st.form_submit_button(label="💾 Gửi dữ liệu lên Google Sheet", use_container_width=True)

# --- XỬ LÝ GỬI DỮ LIỆU & RESET FORM ---
if submit_button:
    if not headcode:
        st.error("Trường 'Headcode' đang trống. Vui lòng mở camera chụp QR hoặc điền tay.")
    elif not nguoibao:
        st.error("Vui lòng điền thông tin 'Người báo'.")
    else:
        # Giữ nguyên giá trị float của số lượng để truyền đi
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
                    # 1. Hiển thị thông báo đúng yêu cầu của bạn
                    st.success("🎉 Đã up dữ liệu thành công")
                    
                    # 2. XÓA DỮ LIỆU ĐỂ TRẢ VỀ FORM TRỐNG HOÀN TOÀN
                    st.session_state.qr_code_detected = ""  # Xóa sạch Headcode
                    st.session_state.soluong_val = 1.000     # Trả số lượng về mặc định
                    st.session_state.nguoibao_val = ""      # Xóa sạch Người báo
                    
                    # Buộc trang tải lại để giao diện áp dụng các giá trị trống vừa cập nhật
                    st.rerun()
                else:
                    st.error(f"Lỗi phản hồi từ máy chủ (Mã lỗi: {response.status_code})")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")
