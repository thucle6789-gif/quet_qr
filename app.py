import streamlit as st
import requests
import cv2
import numpy as np

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

# --- DANH SÁCH CÔNG ĐOẠN MẶC ĐỊNH ---
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

# --- KHỞI TẠO CÁC GIÁ TRỊ BAN ĐẦU TRONG BỘ NHỚ ---
if "qr_tam" not in st.session_state:
    st.session_state.qr_tam = ""

# --- KHU VỰC CHỤP ẢNH / CAMERA HỆ THỐNG ---
st.subheader("📸 Máy quét bằng Camera Hệ thống")

uploaded_file = st.file_uploader(
    "▶️ BẤM VÀO ĐÂY ĐỂ MỞ CAMERA HỆ THỐNG CHỤP MÃ QR", 
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=False,
    label_visibility="visible",
    key="camera_uploader"
)

# Xử lý ảnh chụp từ camera (Lưu vào một biến trung gian an toàn)
if uploaded_file is not None:
    try:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        opencv_img = cv2.imdecode(file_bytes, 1)
        
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(opencv_img)
        
        if data:
            # Lưu vào biến tạm trung gian, KHÔNG chạm vào key của widget để tránh lỗi
            st.session_state.qr_tam = data
            st.toast(f"✅ Đã nhận diện thành công Headcode: {data}", icon="✅")
        else:
            st.error("❌ Không tìm thấy mã QR trong bức ảnh vừa chụp. Vui lòng lấy nét rõ ràng và chụp lại!")
    except Exception as e:
        st.error(f"Lỗi xử lý hình ảnh: {e}")

st.markdown("---")

# --- KHU VỰC FORM ĐIỀN THÔNG TIN ---
st.subheader("📝 Thông tin bản ghi")

# Định nghĩa hàm reset form trống khi gửi dữ liệu lên Google Sheet thành công
def clear_form_callback():
    st.session_state.qr_tam = "" # Xóa mã QR tạm
    st.session_state.input_headcode = ""
    st.session_state.input_soluong = 1.000
    st.session_state.input_nguoibao = ""
    st.session_state.input_congdoan = DANH_SACH_CONG_DOAN[0]

# Sử dụng st.form để bao bọc dữ liệu
with st.form(key="factory_data_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    
    with col1:
        # Nếu có dữ liệu quét từ QR tam thời, gán nó làm giá trị mặc định lúc khởi tạo
        val_headcode = st.session_state.qr_tam if st.session_state.qr_tam else ""
        
        headcode = st.text_input(
            "Headcode *", 
            value=val_headcode,
            key="input_headcode"
        )
        
        congdoan = st.selectbox(
            "Công đoạn", 
            options=DANH_SACH_CONG_DOAN, 
            key="input_congdoan"
        )
        
    with col2:
        soluong = st.number_input(
            "Số lượng", 
            min_value=0.000, 
            value=1.000,
            step=0.001, 
            format="%.3f",
            key="input_soluong"
        )
        
        nguoibao = st.text_input(
            "Người báo", 
            key="input_nguoibao"
        )

    # Nút gửi dữ liệu
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
            "soluong": float(soluong),
            "congdoan": congdoan,
            "nguoibao": nguoibao
        }
        
        with st.spinner("Đang truyền dữ liệu về hệ thống bảng tính..."):
            try:
                response = requests.post(WEB_APP_URL, json=payload)
                if response.status_code == 200:
                    # Gọi hàm xóa toàn bộ dữ liệu form về trống
                    clear_form_callback()
                    st.toast("🎉 Đã up dữ liệu thành công", icon="✅")
                    st.success("🎉 Đã up dữ liệu thành công")
                    # Tải lại trang để cập nhật giao diện form trống hoàn toàn
                    st.rerun()
                else:
                    st.error(f"Lỗi phản hồi từ máy chủ (Mã lỗi: {response.status_code})")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")
