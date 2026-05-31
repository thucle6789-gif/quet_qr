import streamlit as st
import requests
from PIL import Image
import cv2
import numpy as np
from camera_input_live import camera_input_live

# 1. Điền đường link Web App URL Google Apps Script của bạn vào đây
WEB_APP_URL = "DÁN_ĐƯỜNG_LINK_WEB_APP_URL_CỦA_BẠN_VÀO_ĐÂY"

st.set_page_config(page_title="Quét QR Code Tối Ưu", layout="centered")

# Nhúng CSS làm đẹp giao diện
st.markdown("""
    <style>
    .main-title { text-align: center; font-family: Arial, sans-serif; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    /* Khung viền bao quanh camera trực tuyến */
    .camera-box { border: 6px solid #222222; border-radius: 16px; overflow: hidden; background-color: #000; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Quét QR Code & Nhập Dữ Liệu</h1>", unsafe_allow_html=True)

# --- KHỞI TẠO CÁC BIẾN TRẠNG THÁI (SESSION STATE) ---
if "camera_on" not in st.session_state:
    st.session_state.camera_on = False  # Trạng thái bật/tắt camera
if "qr_code_detected" not in st.session_state:
    st.session_state.qr_code_detected = ""  # Lưu chuỗi QR quét được

# --- KHU VỰC ĐIỀU KHIỂN CAMERA ---
st.subheader("📸 Máy quét QR Code")

# Nếu camera đang tắt, hiển thị nút bấm để mở
if not st.session_state.camera_on:
    if st.button("▶️ MỞ CAMERA ĐỂ QUẾT QR", use_container_width=True, type="primary"):
        st.session_state.camera_on = True
        st.session_state.qr_code_detected = "" # Xóa dữ liệu cũ khi quét mới
        st.rerun()

# Nếu camera đang bật, tiến hành live stream hình ảnh và tự động nhận diện QR
else:
    # Nút bấm thủ công nếu muốn tắt camera giữa chừng mà không quét nữa
    if st.button("❌ TẮT CAMERA", use_container_width=True):
        st.session_state.camera_on = False
        st.rerun()
        
    st.markdown('<div class="camera-box">', unsafe_allow_html=True)
    # Thành phần camera_input_live sẽ liên tục trả về hình ảnh từ luồng video mà không bắt bấm chụp
    jpeg_image = camera_input_live(debounce=200) # Đọc ảnh mỗi 200 mili-giây
    st.markdown('</div>', unsafe_allow_html=True)

    if jpeg_image is not None:
        try:
            # Đọc hình ảnh luồng trực tiếp sang OpenCV
            file_bytes = np.asarray(bytearray(jpeg_image.read()), dtype=np.uint8)
            opencv_img = cv2.imdecode(file_bytes, 1)
            
            # Giải mã QR bằng bộ xử lý OpenCV
            detector = cv2.QRCodeDetector()
            data, bbox, straight_qrcode = detector.detectAndDecode(opencv_img)
            
            # KHI NHẬN ĐƯỢC QR CODE THÀNH CÔNG
            if data:
                st.session_state.qr_code_detected = data # Lưu dữ liệu vào ô nhập liệu
                st.session_state.camera_on = False       # TỰ ĐỘNG THOÁT CAMERA
                st.toast("Quét thành công! Đang đóng camera...", icon="✅")
                st.rerun() # Tải lại trang để áp dụng tắt camera và điền dữ liệu
        except Exception as e:
            pass

st.markdown("---")

# --- KHU VỰC FORM ĐIỀN THÔNG TIN ---
st.subheader("📝 Thông tin bản ghi")

with st.form(key="factory_data_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    
    with col1:
        # Trường Headcode tự động nhận diện từ QR, hoặc nhập tay bình thường
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
                    st.session_state.qr_code_detected = "" # Clear để chuẩn bị cho lần sau
                else:
                    st.error(f"Lỗi phản hồi từ máy chủ (Mã lỗi: {response.status_code})")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")
