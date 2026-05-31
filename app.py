import streamlit as st
import requests

# Thay thế bằng đường link Web App URL Apps Script bạn vừa copy ở bước trên
WEB_APP_URL = "DÁN_ĐƯỜNG_LINK_WEB_APP_URL_CỦA_BẠN_VÀO_ĐÂY"

st.set_page_config(page_title="Hệ thống nhập dữ liệu", layout="centered")
st.title("📊 Hệ thống Nhập Dữ liệu Sản xuất")

# --- PHẦN QUÉT QR CODE QUA CAMERA ---
st.subheader("📸 Bước 1: Quét mã QR (Nếu có)")
img_file_buffer = st.camera_input("Đưa mã QR vào trước camera (Hệ thống sẽ bắt mã)")

qr_data = None
if img_file_buffer is not None:
    # Đoạn logic quét QR từ ảnh (yêu cầu cài pillow và pyzbar hoặc opencv)
    from PIL import Image
    from pyzbar.pyzbar import decode
    
    try:
        img = Image.open(img_file_buffer)
        detected_barcodes = decode(img)
        if detected_barcodes:
            qr_data = detected_barcodes[0].data.decode("utf-8")
            st.success(f"Quét thành công Headcode: {qr_data}")
        else:
            st.warning("Không tìm thấy mã QR trong ảnh. Bạn có thể tự nhập tay ở dưới.")
    except Exception as e:
        st.info("Tính năng nhận diện tự động đang chờ cấu hình thư viện đầy đủ. Bạn hãy nhập tay ở form dưới.")

# --- PHẦN FORM NHẬP DỮ LIỆU ---
st.subheader("📝 Bước 2: Kiểm tra và Gửi thông tin")

with st.form(key="input_factory_form", clear_on_submit=False):
    # Ô Headcode sẽ tự điền nếu quét được QR, hoặc tự điền bằng tay
    headcode = st.text_input("Headcode *", value=qr_data if qr_data else "")
    
    # Ô nhập số lượng (mặc định là 1, bước nhảy là 1)
    soluong = st.number_input("Số lượng", min_value=1, value=1, step=1)
    
    # Ô nhập công đoạn
    congdoan = st.text_input("Công đoạn")
    
    # Ô nhập người báo cáo
    nguoibao = st.text_input("Người báo")
    
    # Nút bấm gửi
    submit_button = st.form_submit_button(label="🚀 Gửi lên Google Sheet")

# --- XỬ LÝ KHI BẤM NÚT GỬI ---
if submit_button:
    if not headcode:
        st.error("Vui lòng điền thông tin trường 'Headcode'.")
    elif not nguoibao:
        st.error("Vui lòng điền tên 'Người báo'.")
    else:
        # Đóng gói dữ liệu thành JSON (tên biến phải khớp chính xác với code Apps Script)
        payload = {
            "headcode": headcode,
            "soluong": int(soluong),
            "congdoan": congdoan,
            "nguoibao": nguoibao
        }
        
        with st.spinner("Đang kết nối và lưu dữ liệu..."):
            try:
                # Gửi yêu cầu sang Google Apps Script
                response = requests.post(WEB_APP_URL, json=payload)
                
                if response.status_code == 200:
                    st.success(f"🎉 Đã lưu thành công dữ liệu cho Headcode '{headcode}' vào Sheet 'input'!")
                else:
                    st.error(f"Lỗi hệ thống Google! Mã phản hồi: {response.status_code}")
            except Exception as e:
                st.error(f"Không thể kết nối đến Google Sheet. Chi tiết lỗi: {e}")