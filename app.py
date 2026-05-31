import streamlit as st
import requests
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

# 1. Điền đường link Web App URL Google Apps Script của bạn vào đây
WEB_APP_URL = "DÁN_ĐƯỜNG_LINK_WEB_APP_URL_CỦA_BẠN_VÀO_ĐÂY"

st.set_page_config(page_title="Quét QR Code Tối Ưu", layout="centered")

# Nhúng CSS làm đẹp giao diện
st.markdown("""
    <style>
    .main-title { text-align: center; font-family: Arial, sans-serif; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    /* Làm đẹp khu vực hiển thị camera */
    div[data-testid="stWebrtcStreamer"] {
        border: 6px solid #222222;
        border-radius: 16px;
        overflow: hidden;
        background-color: #000;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Quét QR Code & Nhập Dữ Liệu</h1>", unsafe_allow_html=True)

# --- KHỞI TẠO CÁC BIẾN TRẠNG THÁI (SESSION STATE) ---
if "qr_code_detected" not in st.session_state:
    st.session_state.qr_code_detected = ""  # Lưu chuỗi QR quét được
if "camera_active" not in st.session_state:
    st.session_state.camera_active = True   # Trạng thái bật/tắt của hệ thống camera

st.subheader("📸 Máy quét QR Code (Mặc định camera sau)")

# Hàm callback xử lý từng khung hình video từ WebRTC bằng OpenCV để quét QR
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    
    # Sử dụng bộ dò mã QR của OpenCV
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)
    
    if data:
        # Khi tìm thấy mã QR, lưu vào session_state và tắt camera
        st.session_state.qr_code_detected = data
        st.session_state.camera_active = False
        st.toast("Quét mã QR thành công!", icon="✅")
        
    return frame

# HIỂN THỊ CAMERA
if st.session_state.camera_active:
    webrtc_ctx = webrtc_streamer(
        key="qr-scanner",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
        video_frame_callback=video_frame_callback,
        # CẤU HÌNH MẶC ĐỊNH ÉP BUỘC MỞ CAMERA SAU TRÊN ĐIỆN THOẠI
        media_stream_constraints={
            "video": {
                "facingMode": "environment",  # "environment" nghĩa là camera phía sau
                "width": {"ideal": 640},
                "height": {"ideal": 480}
            },
            "audio": False # Tắt mic tránh đòi quyền âm thanh
        },
        async_processing=True,
    )
else:
    # Nếu camera đã tự động tắt sau khi quét thành công, hiện nút để bấm quét lại lượt mới nếu muốn
    if st.button("🔄 BẬT LẠI CAMERA ĐỂ QUẾT MÃ MỚI", use_container_width=True, type="primary"):
        st.session_state.camera_active = True
        st.session_state.qr_code_detected = ""
        st.rerun()

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
                    # Sau khi gửi thành công, mở lại camera chuẩn bị cho lượt quét tiếp theo
                    st.session_state.qr_code_detected = ""
                    st.session_state.camera_active = True
                    st.rerun()
                else:
                    st.error(f"Lỗi phản hồi từ máy chủ (Mã lỗi: {response.status_code})")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")
