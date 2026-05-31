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
