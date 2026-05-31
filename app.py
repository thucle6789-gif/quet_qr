import streamlit as st
import requests
from PIL import Image
import cv2
import numpy as np

# 1. Điền đường link Web App URL Google Apps Script của bạn vào đây
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxB9cagxYoxM8kpbLtkFGKoQ6SND4QNqLbPTwFR1fs0bNUH-KNDFSaYtrTxKJ8VadEv8g/exec"

# Cấu hình giao diện trang web
st.set_page_config(page_title="Quét QR Code & Nhập Dữ Liệu", layout="centered")

# Nhúng mã CSS tùy biến giao diện camera giống một chiếc máy ảnh chuyên dụng
st.markdown("""
    <style>
    /* Làm đẹp tiêu đề chính */
    .main-title {
        text-align: center;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: bold;
        color: #1E1E1E;
        margin-bottom: 20px;
    }
    /* Tạo khung viền giống máy quét cho khu vực Camera */
    div[data-testid="stCameraInput"] {
        border: 8px solid #222222;
        border-radius: 20px;
        padding: 10px;
        background-color: #151515;
        box-shadow: 0px 8px 16px rgba(0,0,0,0.3);
    }
    /* Tùy biến nút bấm Chụp (Quét) của Streamlit thành màu đỏ nổi bật */
    div[data-testid="stCameraInput"] button {
        background-color: #DC3545 !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border-radius: 50px !important;
        padding: 10px 24px !important;
        border: 3px solid #FFFFFF !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3) !important;
        text-transform: uppercase;
    }
    div[data-testid="stCameraInput"] button:hover {
        background-color: #C82333 !important;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>Quét QR Code & Nhập Dữ Liệu</h1>", unsafe_allow_html=True)

# --- KHU VỰC MÁY QUẾT CAMERA ---
st.subheader("📸 Ống kính Máy quét")

# Khởi tạo biến lưu trữ dữ liệu QR quét được trong phiên làm việc
if "qr_code_detected" not in st.session_state:
    st.session_state.qr_code_detected = ""

# Giao diện camera tích hợp nút chụp
img_file_buffer = st.camera_input("Đưa mã QR vào khung hình và bấm nút QUÉT phía dưới")

# Xử lý hình ảnh bằng OpenCV khi người dùng bấm nút chụp (Nút màu đỏ)
if img_file_buffer is not None:
    try:
        # Chuyển đổi dữ liệu ảnh buffer sang dạng định dạng mà OpenCV có thể đọc được
        file_bytes = np.asarray(bytearray(img_file_buffer.read()), dtype=np.uint8)
        opencv_img = cv2.imdecode(file_bytes, 1)
        
        # Khởi tạo bộ dò mã QR tích hợp sẵn trong OpenCV (Không cần thư viện ngoài zbar)
        detector = cv2.QRCodeDetector()
        
        # Tiến hành giải mã hình ảnh
        data, bbox, straight_qrcode = detector.detectAndDecode(opencv_img)
        
        if data:
            st.session_state.qr_code_detected = data
            st.toast("Quét mã thành công!", icon="✅")
        else:
            st.error("❌ Không tìm thấy mã QR nào trong ảnh chụp. Vui lòng căn giữa thẳng góc và bấm QUÉT lại!")
    except Exception as e:
        st.warning("Hệ thống camera đang sẵn sàng. Hãy bấm nút màu đỏ để quét.")

st.markdown("---")

# --- KHU VỰC FORM ĐIỀN THÔNG TIN ---
st.subheader("📝 Thông tin bản ghi")

# Tạo form nhập liệu xếp gọn gàng theo hàng/cột
with st.form(key="factory_data_form", clear_on_submit=False):
    
    # Chia form thành 2 cột cân đối
    col1, col2 = st.columns(2)
    
    with col1:
        # Trường Headcode tự động điền giá trị vừa quét được từ QR, người dùng vẫn có thể nhập tay
        headcode = st.text_input("Headcode *", value=st.session_state.qr_code_detected, help="Tự động điền sau khi bấm nút quét trên camera")
        congdoan = st.text_input("Công đoạn")
        
    with col2:
        # Trường Số lượng mặc định số nguyên bằng 1
        soluong = st.number_input("Số lượng", min_value=1, value=1, step=1)
        nguoibao = st.text_input("Người báo")

    # Nút bấm gửi dữ liệu đồng bộ lên Google Sheet đặt ở cuối form
    submit_button = st.form_submit_button(label="💾 Gửi dữ liệu lên Google Sheet", use_container_width=True)

# --- XỬ LÝ KHI BẤM NÚT GỬI ---
if submit_button:
    if not headcode:
        st.error("Trường 'Headcode' đang trống. Vui lòng quét QR hoặc nhập tay.")
    elif not nguoibao:
        st.error("Vui lòng điền thông tin 'Người báo' trước khi gửi.")
    else:
        # Tạo cấu trúc JSON đóng gói gửi đi
        payload = {
            "headcode": headcode,
            "soluong": int(soluong),
            "congdoan": congdoan,
            "nguoibao": nguoibao
        }
        
        with st.spinner("Đang truyền dữ liệu về hệ thống bảng tính..."):
            try:
                # Thực hiện lệnh POST gửi dữ liệu tới Web App URL (Apps Script)
                response = requests.post(WEB_APP_URL, json=payload)
                
                if response.status_code == 200:
                    st.success(f"🎉 Đã lưu thành công dữ liệu cho Headcode: {headcode} vào hàng tiếp theo!")
                    # Xóa bộ nhớ tạm của mã QR cũ để sẵn sàng cho lượt quét tiếp theo
                    st.session_state.qr_code_detected = "" 
                else:
                    st.error(f"Gặp sự cố phản hồi từ máy chủ Google (Mã lỗi: {response.status_code})")
            except Exception as e:
                st.error(f"Không thể kết nối. Vui lòng kiểm tra lại mạng hoặc link Web App URL. Lỗi: {e}")
