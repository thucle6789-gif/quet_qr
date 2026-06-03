import streamlit as st
import requests
import cv2
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo

# =====================================================
# CẤU HÌNH
# =====================================================
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzOFJsvHTtpPOzGv8NQRfr12SYMNp7bDUxoHEPl6vEkOChpzDxAwzhc_aNQls-97PankA/exec"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

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
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; background-color: #0f1117; color: #e0e0e0; }
.sys-header { background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%); border-bottom: 2px solid #00e5a0; padding: 18px 28px; margin: -1rem -1rem 1.5rem -1rem; display: flex; align-items: center; gap: 14px; }
.sys-header h1 { font-family: 'IBM Plex Mono', monospace; font-size: 1.3rem; color: #00e5a0; margin: 0; letter-spacing: 2px; text-transform: uppercase; }
.sys-header .dot { width: 10px; height: 10px; border-radius: 50%; background: #00e5a0; box-shadow: 0 0 10px #00e5a0; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.card { background: #1a1f2e; border: 1px solid #2a3045; border-radius: 10px; padding: 20px; margin-bottom: 16px; }
.card-title { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #00e5a0; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 14px; border-bottom: 1px solid #2a3045; padding-bottom: 8px; }
.badge-doing { background: #1a2e1a; color: #4ade80; border: 1px solid #4ade80; padding: 3px 10px; border-radius: 20px; font-size: 0.7rem; font-family: 'IBM Plex Mono', monospace; font-weight: 600; letter-spacing: 1px; }
.job-row { background: #1a1f2e; border: 1px solid #2a3045; border-left: 3px solid #f59e0b; border-radius: 6px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
.job-headcode { font-family: 'IBM Plex Mono', monospace; font-size: 1rem; font-weight: 600; color: #f59e0b; }
.job-meta { font-size: 0.78rem; color: #94a3b8; margin-top: 2px; }
.job-time { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; color: #64748b; text-align: right; }
.stTextInput input, .stSelectbox select, .stNumberInput input { background: #0f1117 !important; border: 1px solid #2a3045 !important; color: #e0e0e0 !important; border-radius: 6px !important; font-family: 'IBM Plex Mono', monospace !important; }
.stTextInput input:focus { border-color: #00e5a0 !important; box-shadow: 0 0 0 2px rgba(0,229,160,0.15) !important; }
.stFormSubmitButton button { background: linear-gradient(135deg, #00e5a0, #00b37e) !important; color: #0f1117 !important; font-family: 'IBM Plex Mono', monospace !important; font-weight: 700 !important; font-size: 0.95rem !important; letter-spacing: 1px !important; border: none !important; border-radius: 8px !important; height: 48px !important; }
.stAlert { border-radius: 8px !important; }
div[data-testid="stFileUploaderDropzone"] { padding: 10px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="sys-header">
    <div class="dot"></div>
    <h1>⚙ Hệ Thống Quét QR Xưởng Sản Xuất</h1>
</div>
""", unsafe_allow_html=True)

# =====================================================
# HÀM: LẤY DANH SÁCH ĐANG LÀM TỪ GOOGLE SHEET
# Được gọi khi app load lần đầu (active_jobs_loaded = False)
# =====================================================
def fetch_active_jobs_from_sheet():
    """Query Google Sheet để lấy tất cả dòng có trạng thái ĐANG LÀM."""
    try:
        resp = requests.get(WEB_APP_URL + "?action=get_active", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            jobs = {}
            for item in data.get("active_jobs", []):
                job_key = f"{item['headcode']}|{item['congdoan']}"
                jobs[job_key] = item
            return jobs
    except Exception:
        pass
    return {}

# =====================================================
# SESSION STATE INIT
# =====================================================
defaults = {
    "qr_detected": "",
    "nguoibao_val": "",
    "soluong_val": 1.000,
    "form_key": 0,
    "active_jobs": {},
    "active_jobs_loaded": False,  # ← FLAG: đã load từ Sheet chưa
    "last_action": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =====================================================
# LOAD ACTIVE JOBS TỪ SHEET KHI APP MỞ LẦN ĐẦU
# Đây là key fix cho vấn đề mất trạng thái khi thoát app
# =====================================================
if not st.session_state.active_jobs_loaded:
    with st.spinner("🔄 Đang đồng bộ trạng thái từ hệ thống..."):
        st.session_state.active_jobs = fetch_active_jobs_from_sheet()
        st.session_state.active_jobs_loaded = True

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

        job_key = f"{headcode}|{congdoan}" if headcode else ""
        is_active = job_key in st.session_state.active_jobs

        if is_active:
            job_info = st.session_state.active_jobs[job_key]
            st.info(f"🔄 Đang làm từ **{job_info['gio_bat_dau']}** — Xác nhận để **HOÀN THÀNH**")
            mode_label = "🏁 HOÀN THÀNH"
        else:
            st.info("🚀 Chưa bắt đầu tại công đoạn này — Xác nhận để **BẮT ĐẦU**")
            mode_label = "▶️ BẮT ĐẦU"

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
                        st.session_state.nguoibao_val = nguoibao
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

    if st.session_state.last_action:
        act = st.session_state.last_action
        if act["type"] == "start":
            st.success(f"🚀 ĐÃ BẮT ĐẦU: **{act['headcode']}** — {act['congdoan']}")
        else:
            st.success(f"🏁 ĐÃ HOÀN THÀNH: **{act['headcode']}** — {act['congdoan']}")

    # Nút refresh thủ công để đồng bộ lại từ Sheet
    if st.button("🔄 Làm mới danh sách", use_container_width=True):
        st.session_state.active_jobs = fetch_active_jobs_from_sheet()
        st.rerun()

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
                    <div class="job-meta">👤 {job['nguoibao']} &nbsp;|&nbsp; 📦 {job.get('soluong', 0):.3f}</div>
                </div>
                <div class="job-time">
                    <span class="badge-doing">ĐANG LÀM</span><br/>
                    <span style="margin-top:6px;display:block">{job['gio_bat_dau']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <div class="card-title">📖 Hướng dẫn</div>
        <div style="font-size:0.82rem; color:#94a3b8; line-height:1.8;">
            <b style="color:#f59e0b">Lần quét 1</b> → <span style="color:#4ade80">BẮT ĐẦU</span> — ghi giờ vào Sheet<br/>
            <b style="color:#818cf8">Lần quét 2</b> → <span style="color:#818cf8">HOÀN THÀNH</span> — cập nhật giờ xong<br/><br/>
            <span style="color:#64748b">⚠ Khi mở lại app, danh sách đang làm<br/>được tự động khôi phục từ Google Sheet</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
