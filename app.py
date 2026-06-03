import streamlit as st
import requests
import cv2
import numpy as np
from datetime import datetime
import pytz

# =====================================================
# CẤU HÌNH
# =====================================================
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxB9cagxYoxM8kpbLtkFGKoQ6SND4QNqLbPTwFR1fs0bNUH-KNDFSaYtrTxKJ8VadEv8g/exec"
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

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

# =====================================================
# PAGE CONFIG & CSS
# =====================================================
st.set_page_config(page_title="Hệ Thống Quét QR Xưởng", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0f1117;
    color: #e0e0e0;
}

/* Header */
.sys-header {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%);
    border-bottom: 2px solid #00e5a0;
    padding: 18px 28px;
    margin: -1rem -1rem 1.5rem -1rem;
    display: flex;
    align-items: center;
    gap: 14px;
}
.sys-header h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.3rem;
    color: #00e5a0;
    margin: 0;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.sys-header .dot { 
    width: 10px; height: 10px; border-radius: 50%;
    background: #00e5a0;
    box-shadow: 0 0 10px #00e5a0;
    animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

/* Card */
.card {
    background: #1a1f2e;
    border: 1px solid #2a3045;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
}
.card-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #00e5a0;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 14px;
    border-bottom: 1px solid #2a3045;
    padding-bottom: 8px;
}

/* Status badges */
.badge-doing {
    background: #1a2e1a; color: #4ade80;
    border: 1px solid #4ade80;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.7rem; font-family: 'IBM Plex Mono', monospace;
    font-weight: 600; letter-spacing: 1px;
}
.badge-done {
    background: #1a1a2e; color: #818cf8;
    border: 1px solid #818cf8;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.7rem; font-family: 'IBM Plex Mono', monospace;
    font-weight: 600; letter-spacing: 1px;
}

/* Active jobs table */
.job-row {
    background: #1a1f2e;
    border: 1px solid #2a3045;
    border-left: 3px solid #f59e0b;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.job-headcode {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1rem;
    font-weight: 600;
    color: #f59e0b;
}
.job-meta {
    font-size: 0.78rem;
    color: #94a3b8;
    margin-top: 2px;
}
.job-time {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #64748b;
    text-align: right;
}

/* Scan mode buttons */
.stRadio > div { flex-direction: row !important; gap: 10px; }
.stRadio label {
    background: #1a1f2e !important;
    border: 1px solid #2a3045 !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    cursor: pointer;
    transition: all 0.2s;
}

/* Inputs */
.stTextInput input, .stSelectbox select, .stNumberInput input {
    background: #0f1117 !important;
    border: 1px solid #2a3045 !important;
    color: #e0e0e0 !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
.stTextInput input:focus {
    border-color: #00e5a0 !important;
    box-shadow: 0 0 0 2px rgba(0,229,160,0.15) !important;
}

/* Submit button */
.stFormSubmitButton button {
    background: linear-gradient(135deg, #00e5a0, #00b37e) !important;
    color: #0f1117 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 1px !important;
    border: none !important;
    border-radius: 8px !important;
    height: 48px !important;
    transition: all 0.2s !important;
}
.stFormSubmitButton button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(0,229,160,0.4) !important;
}

/* Alert override */
.stAlert { border-radius: 8px !important; }

div[data-testid="stFileUploaderDropzone"] { padding: 10px !important; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="sys-header">
    <div class="dot"></div>
    <h1>⚙ Hệ Thống Quét QR Xưởng Sản Xuất</h1>
</div>
""", unsafe_allow_html=True)

# =====================================================
# SESSION STATE INIT
# =====================================================
defaults = {
    "qr_detected": "",
    "nguoibao_val": "",
    "soluong_val": 1.000,
    "form_key": 0,
    # Danh sách các job đang làm: dict { "headcode|congdoan": {headcode, congdoan, nguoibao, gio_bat_dau, row_id} }
    "active_jobs": {},
    "last_action": None,   # {"type": "start"|"finish", "headcode": ..., "congdoan": ...}
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =====================================================
# LAYOUT: 2 cột chính
# =====================================================
col_scan, col_active = st.columns([1.1, 0.9], gap="large")

# =====================================================
# CỘT TRÁI: QUÉT QR & FORM
# =====================================================
with col_scan:
    st.markdown('<div class="card"><div class="card-title">📷 Quét mã QR</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "▶️ BẤM ĐỂ MỞ CAMERA CHỤP MÃ QR",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
        key=f"cam_{st.session_state.form_key}"
    )

    if uploaded_file is not None:
        try:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            opencv_img = cv2.imdecode(file_bytes, 1)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(opencv_img)
            if data:
                if data != st.session_state.qr_detected:
                    st.session_state.qr_detected = data
                    st.session_state.form_key += 1
                    st.rerun()
            else:
                st.error("❌ Không tìm thấy mã QR. Vui lòng chụp rõ hơn!")
        except Exception as e:
            st.error(f"Lỗi xử lý ảnh: {e}")

    if st.session_state.qr_detected:
        st.success(f"✅ Nhận diện: **{st.session_state.qr_detected}**")

    st.markdown('</div>', unsafe_allow_html=True)

    # --- FORM NHẬP LIỆU ---
    st.markdown('<div class="card"><div class="card-title">📝 Thông tin thao tác</div>', unsafe_allow_html=True)

    # Xác định chế độ tự động dựa vào active_jobs
    # Nếu QR đã có trong active_jobs với công đoạn được chọn → gợi ý "Hoàn thành"
    with st.form(key=f"main_form_{st.session_state.form_key}", clear_on_submit=False):
        headcode = st.text_input(
            "Headcode *",
            value=st.session_state.qr_detected,
            key=f"headcode_{st.session_state.form_key}"
        )

        congdoan = st.selectbox(
            "Công đoạn *",
            options=DANH_SACH_CONG_DOAN,
            key=f"congdoan_{st.session_state.form_key}"
        )

        # Tự động phát hiện chế độ
        job_key = f"{headcode}|{congdoan}" if headcode else ""
        is_active = job_key in st.session_state.active_jobs

        if is_active:
            job_info = st.session_state.active_jobs[job_key]
            st.info(f"🔄 Mã này đang **ĐANG LÀM** tại công đoạn này từ {job_info['gio_bat_dau']}. Quét để **HOÀN THÀNH**.")
            mode_label = "🏁 HOÀN THÀNH"
            btn_color_hint = "finish"
        else:
            st.info("🚀 Mã mới tại công đoạn này. Quét để **BẮT ĐẦU**.")
            mode_label = "▶️ BẮT ĐẦU"
            btn_color_hint = "start"

        col_a, col_b = st.columns(2)
        with col_a:
            soluong = st.number_input(
                "Số lượng",
                min_value=0.000,
                value=st.session_state.soluong_val,
                step=0.001,
                format="%.3f",
                key=f"soluong_{st.session_state.form_key}"
            )
        with col_b:
            nguoibao = st.text_input(
                "Người vận hành *",
                value=st.session_state.nguoibao_val,
                key=f"nguoibao_{st.session_state.form_key}"
            )

        submit = st.form_submit_button(
            label=f"💾 XÁC NHẬN — {mode_label}",
            use_container_width=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # =====================================================
    # XỬ LÝ SUBMIT
    # =====================================================
    if submit:
        if not headcode:
            st.error("Vui lòng quét hoặc điền Headcode.")
        elif not nguoibao:
            st.error("Vui lòng điền Người vận hành.")
        else:
            now_vn = datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M:%S")
            job_key = f"{headcode}|{congdoan}"
            is_active = job_key in st.session_state.active_jobs

            if not is_active:
                # ---- QUÉT LẦN 1: BẮT ĐẦU ----
                payload = {
                    "action": "start",
                    "headcode": headcode,
                    "congdoan": congdoan,
                    "soluong": float(soluong),
                    "nguoibao": nguoibao,
                    "gio_bat_dau": now_vn,
                }
                with st.spinner("Đang ghi nhận bắt đầu..."):
                    try:
                        resp = requests.post(WEB_APP_URL, json=payload)
                        resp_json = resp.json() if resp.status_code == 200 else {}
                        row_id = resp_json.get("row_id", "")

                        # Lưu vào active_jobs
                        st.session_state.active_jobs[job_key] = {
                            "headcode": headcode,
                            "congdoan": congdoan,
                            "nguoibao": nguoibao,
                            "soluong": float(soluong),
                            "gio_bat_dau": now_vn,
                            "row_id": row_id,
                        }
                        st.session_state.last_action = {"type": "start", "headcode": headcode, "congdoan": congdoan}
                        st.session_state.qr_detected = ""
                        st.session_state.nguoibao_val = nguoibao  # Giữ tên người vận hành
                        st.session_state.soluong_val = 1.000
                        st.session_state.form_key += 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi kết nối: {e}")
            else:
                # ---- QUÉT LẦN 2: HOÀN THÀNH ----
                job_info = st.session_state.active_jobs[job_key]
                payload = {
                    "action": "finish",
                    "headcode": headcode,
                    "congdoan": congdoan,
                    "soluong": float(soluong),
                    "nguoibao": nguoibao,
                    "gio_bat_dau": job_info["gio_bat_dau"],
                    "gio_hoan_thanh": now_vn,
                    "row_id": job_info.get("row_id", ""),
                }
                with st.spinner("Đang cập nhật hoàn thành..."):
                    try:
                        resp = requests.post(WEB_APP_URL, json=payload)
                        if resp.status_code == 200:
                            del st.session_state.active_jobs[job_key]
                            st.session_state.last_action = {"type": "finish", "headcode": headcode, "congdoan": congdoan}
                            st.session_state.qr_detected = ""
                            st.session_state.nguoibao_val = nguoibao
                            st.session_state.soluong_val = 1.000
                            st.session_state.form_key += 1
                            st.rerun()
                        else:
                            st.error(f"Lỗi server: {resp.status_code}")
                    except Exception as e:
                        st.error(f"Lỗi kết nối: {e}")

# =====================================================
# CỘT PHẢI: TRẠNG THÁI THỜI GIAN THỰC
# =====================================================
with col_active:

    # Thông báo hành động vừa rồi
    if st.session_state.last_action:
        act = st.session_state.last_action
        if act["type"] == "start":
            st.success(f"🚀 ĐÃ BẮT ĐẦU: **{act['headcode']}** — {act['congdoan']}")
        else:
            st.success(f"🏁 ĐÃ HOÀN THÀNH: **{act['headcode']}** — {act['congdoan']}")

    # --- BẢNG ĐANG XỬ LÝ ---
    st.markdown('<div class="card"><div class="card-title">⚡ Đang xử lý</div>', unsafe_allow_html=True)

    active_jobs = st.session_state.active_jobs
    if not active_jobs:
        st.markdown('<p style="color:#64748b; font-size:0.85rem; font-family:IBM Plex Mono,monospace;">— Chưa có công việc nào đang chạy —</p>', unsafe_allow_html=True)
    else:
        for jk, job in active_jobs.items():
            st.markdown(f"""
            <div class="job-row">
                <div>
                    <div class="job-headcode">{job['headcode']}</div>
                    <div class="job-meta">{job['congdoan']}</div>
                    <div class="job-meta">👤 {job['nguoibao']} &nbsp;|&nbsp; 📦 {job['soluong']:.3f}</div>
                </div>
                <div class="job-time">
                    <span class="badge-doing">ĐANG LÀM</span><br/>
                    <span style="margin-top:6px;display:block">{job['gio_bat_dau']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # --- HƯỚNG DẪN ---
    st.markdown("""
    <div class="card">
        <div class="card-title">📖 Hướng dẫn</div>
        <div style="font-size:0.82rem; color:#94a3b8; line-height:1.8;">
            <b style="color:#f59e0b">Lần quét 1</b> → Hệ thống ghi nhận <span style="color:#4ade80">BẮT ĐẦU</span><br/>
            — Tạo dòng mới trên Google Sheet<br/>
            — Ghi giờ bắt đầu & trạng thái <code>ĐANG LÀM</code><br/><br/>
            <b style="color:#818cf8">Lần quét 2</b> → Hệ thống ghi nhận <span style="color:#818cf8">HOÀN THÀNH</span><br/>
            — Cập nhật dòng cũ trên Sheet<br/>
            — Ghi giờ hoàn thành & trạng thái <code>XONG</code><br/><br/>
            <span style="color:#64748b">⚠ 1 mã QR có thể chạy song song nhiều công đoạn</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
