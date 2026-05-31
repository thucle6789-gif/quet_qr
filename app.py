import streamlit as st
import requests
import cv2
import numpy as np

# 1. Điền đường link Web App URL Google Apps Script của bạn vào đây
WEB_APP_URL = "DÁN_ĐƯỜNG_LINK_WEB_APP_URL_CỦA_BẠN_VÀO_ĐÂY"

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

# --- DANH SÁCH CÔNG ĐOẠN ---
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

# --- KHỞI TẠO BỘ NHỚ TẠM (SESSION STATE) ---
if "headcode_val" not in st.session_state:
    st.session_state.headcode_val = ""
if "congdoan_val" not in st.session_state:
    st.session_state.congdoan_val = DANH_SACH_CONG_DOAN[0]
if "soluong_val" not in st.session_state:
    st.session_state.soluong_val = 1.000
if "nguoibao_val" not in st.session_state:
    st.session_state.nguoibao_val = ""

# --- KHU VỰC QUET MÃ QR ---
st.subheader("📸 Máy quét bằng Camera Hệ thống")

uploaded_file = st.file_uploader(
    "▶️ BẤM VÀO ĐÂY ĐỂ MỞ CAMERA HỆ THỐNG CHỤP MÃ QR", 
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=False,
    label_visibility="visible",
    key="camera_key" # Định danh để hệ thống tự reset camera
)

# Xử lý ảnh chụp từ camera
if uploaded_file is not None:
    try:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        opencv_img = cv2.imdecode(file_bytes, 1)
        
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(opencv_img)
        
        if data:
            # Điền dữ liệu quét được thẳng vào bộ nhớ của ô nhập liệu
            st.session_state.headcode_val = data
            st.toast(f"✅ Đã nhận diện thành công Headcode: {data}", icon="✅")
            st.rerun() # Tải lại trang ngay lập tức để đồng bộ chữ lên màn hình
        else:
            st.error("❌ Không tìm thấy mã QR trong bức ảnh vừa chụp. Vui lòng lấy nét rõ ràng và chụp lại!")
    except Exception as e:
        st.error(f"Lỗi xử lý hình ảnh: {e}")

st.markdown("---")

# --- KHU VỰC THÔNG TIN BẢN GHI (KHÔNG DÙNG ST.FORM) ---
st.subheader("📝 Thông tin bản ghi")

col1, col2 = st.columns(2)

with col1:
    # Ô nhập Headcode nhận giá trị từ bộ nhớ tạm, cho phép chỉnh sửa tay thoải mái
    headcode_input = st.text_input("Headcode *", value=st.session_state.headcode_val)
    # Cập nhật ngược lại bộ nhớ nếu người dùng sửa tay
    st.session_state.headcode_val = headcode_input

    # Ô chọn Công đoạn
    try:
        idx = DANH_SACH_CONG_DOAN.index(st.session_state.congdoan_val)
    except ValueError:
        idx = 0
    congdoan_input = st.selectbox("Công đoạn", options=DANH_SACH_CONG_DOAN, index=idx)
    st.session_state.congdoan_val = congdoan_input
    
with col2:
    # Ô nhập Số lượng số lẻ
    soluong_input = st.number_input(
        "Số lượng", 
        min_value=0.000, 
        value=st.session_state.soluong_val,
        step=0.001, 
        format="%.3f"
    )
    st.session_state.soluong_val = soluong_input
    
    # Ô nhập Người báo
    nguoibao_input = st.text_input("Người báo", value=st.session_state.nguoibao_val)
    st.session_state.nguoibao_val = nguoibao_input

st.markdown("<br>", unsafe_allow_html=True)
# Nút bấm gửi dữ liệu độc lập bên ngoài form
submit_button = st.button("💾 Gửi dữ liệu lên Google Sheet", use_container_width=True, type="primary")

# --- XỬ LÝ GỬI DỮ LIỆU ---
if submit_button:
    if not st.session_state.headcode_val:
        st.error("Trường 'Headcode' đang trống. Vui lòng mở camera chụp QR hoặc điền tay.")
    elif not st.session_state.nguoibao_val:
        st.error("Vui lòng điền thông tin 'Người báo'.")
    else:
        payload = {
            "headcode": st.session_state.headcode_val,
            "soluong": float(st.session_state.soluong_val),
            "congdoan": st.session_state.congdoan_val,
            "nguoibao": st.session_state.nguoibao_val
        }
        
        with st.spinner("Đang truyền dữ liệu về hệ thống bảng tính..."):
            try:
                response = requests.post(WEB_APP_URL, json=payload)
                if response.status_code == 200:
                    # HIỂN THỊ THÔNG BÁO THÀNH CÔNG ĐÚNG YÊU CẦU
                    st.success("🎉 Đã up dữ liệu thành công")
                    
                    # XÓA TOÀN BỘ DỮ LIỆU ĐỂ TRẢ VỀ FORM TRỐNG HOÀN TOÀN
                    st.session_state.headcode_val = ""
                    st.session_state.soluong_val = 1.000
                    st.session_state.nguoibao_val = ""
                    st.session_state.congdoan_val = DANH_SACH_CONG_DOAN[0]
                    
                    # Ép buộc trang tải lại để giao diện áp dụng trạng thái trống vừa xóa
                    st.rerun()
                else:
                    st.error(f"Lỗi phản hồi từ máy chủ Google (Mã lỗi: {response.status_code})")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")
