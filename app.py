import streamlit as st
import requests
import cv2
import numpy as np
from PIL import Image

# 1. Điền đường link Web App URL Google Apps Script của bạn vào đây
WEB_APP_URL = "DÁN_ĐƯỜNG_LINK_WEB_APP_URL_CỦA_BẠN_VÀO_ĐÂY"

st.set_page_config(page_title="Quét QR Code Tối Ưu", layout="centered")

st.markdown("""
    <style>
    .main-title { text-align: center; font-family: Arial, sans-serif; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    /* Tùy biến khung camera gốc của Streamlit cho đẹp hơn */
    div[data-testid="stCameraInput"] {
        border: 6px solid #222222;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0px 6px 12px rgba(0,0,0,0.15);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Quét QR Code & Nhập Dữ Liệu</h1>", unsafe_allow_html=True)

# --- KHỞI TẠO BIẾN TRẠNG THÁI (SESSION STATE) ---
if "qr_code_detected" not in st.session_state:
    st.session_state.qr_code_detected = ""  # Lưu chuỗi QR quét được
if "show_camera" not in st.session_state:
    st.session_state.show_camera = False    # Trạng thái ẩn/hiện camera

st.subheader("📸 Máy quét QR Code")

# BƯỚC 1: Nếu trạng thái hiển thị camera là SAI -> Hiện nút bấm để MỞ
if not st.session_state.show_camera:
    if st.button("▶️ MỞ CAMERA ĐỂ QUẾT QR", use_container_width=True, type="primary"):
        st.session_state.show_camera = True
        st.session_state.qr_code_detected = "" # Xóa dữ liệu cũ để quét mới
        st.rerun()

# BƯỚC 2: Nếu trạng thái hiển thị camera là ĐÚNG -> Mở khung camera của Streamlit
else:
    if st.button("❌ HỦY QUẾT / TẮT CAMERA", use_container_width=True):
        st.session_state.show_camera = False
        st.rerun()

    # Dùng camera_input gốc, cực kỳ ổn định, tự động tối ưu camera sau trên điện thoại
    img_file_buffer = st.camera_input("Hãy đưa mã QR vào chính giữa khung hình và bấm nút chụp")

    if img_file_buffer is not None:
        try:
            # Đọc ảnh từ bộ nhớ buffer sang OpenCV để giải mã
            file_bytes = np.asarray(bytearray(img_file_buffer.read()), dtype=np.uint8)
            opencv_img = cv2.imdecode(file_bytes, 1)
            
            # Sử dụng bộ quét QR của OpenCV
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(opencv_img)
            
            if data:
                st.session_state.qr_code_detected = data # Điền vào ô nhập liệu
                st.session_state.show_camera = False    # TỰ ĐỘNG TẮT CAMERA BIẾN MẤT
                st.toast("Quét mã QR thành công!", icon="✅")
                st.rerun() # Tải lại trang để áp dụng ẩn camera ngay lập tức
            else:
                st.error("❌ Ảnh chụp không rõ hoặc không có mã QR. Vui lòng căn nét thẳng góc và chụp lại!")
        except Exception as e:
            st.error(f"Lỗi xử lý hình ảnh: {e}")

st.markdown("---")

# --- KHU VỰC FORM ĐIỀN THÔNG TIN ---
st.subheader("📝 Thông tin bản ghi")

with st.form(key="factory_data_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    
    with col1:
        # Trường Headcode tự động điền từ QR, hoặc có thể gõ tay
        headcode = st.text_input("Headcode *", value=st.session_state.qr_code_detected)
        congdoan = st.text_input("Công đoạn")
        
    with col2:
        soluong = st.number_input("Số lượng", min_value=1, value=1, step=1)
        nguoibao = st.text_input("Người báo")

    submit_button = st.form_submit_button(label="💾 Gửi dữ liệu lên Google Sheet", use_container_width=True)

# --- XỬ LÝ GỬI DỮ LIỆU ---
if submit_button:
    if not headcode:
        st.error("Trường 'Headcode' đang trống. Vui lòng bật camera để quét hoặc điền tay.")
    elif not nguoibao:
        st.error("Vui lòng điền thông tin 'Người báo'.")
    else:
        payload = {
            "headcode": headcode,
            "soluong": int(soluong),
            "congdoan": congdoan,
            "nguoibao": nguoibao
        }
        
        with st.spinner("Đang truyền dữ liệu về hệ thống bảng tính..."):
            try:
                response = requests.post(WEB_APP_URL, json=payload)
                if response.status_code == 200:
                    st.success(f"🎉 Đã lưu thành công dữ liệu cho Headcode: {headcode}!")
                    st.session_state.qr_code_detected = "" # Đặt lại rỗng cho lượt tiếp theo
                else:
                    st.error(f"Lỗi phản hồi từ máy chủ (Mã lỗi: {response.status_code})")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")
