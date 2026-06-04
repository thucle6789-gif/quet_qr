import streamlit as st
import requests
from datetime import datetime, date
from zoneinfo import ZoneInfo
import time
import hashlib
from streamlit_cookies_manager import EncryptedCookieManager
from streamlit_camera_input_live import camera_input_live 
from PIL import Image
import cv2
import numpy as np

# =====================================================
# CẤU HÌNH
# =====================================================
def normalize_role(role_str: str) -> str:
    """Chuẩn hóa role về dạng không dấu, không khoảng trắng để so sánh an toàn."""
    import unicodedata
    s = role_str.strip().lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace(' ', '')
    return s

WEB_APP_URL = "https://script.google.com/macros/s/AKfycby1wv7X459Jr_w5X0JgMTHWkZKOhHCDH6WkhWHzmleyI1hnTCWkxXIKASXCt7jA5ThZqQ/exec"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

DANH_SACH_CONG_DOAN = [
    "P013_Tạo phôi và Sơchế","P014_Tinh chế và Định hình","P015_Chà nhám và Bề mặt",
    "P016_Lắp ráp và Liên kết","P017_Làm nguội và Hoàn thiện","P018_Sơn - Màu",
    "P019_Washing - Cleaning","P20_Lắp ráp hoàn thiện","P021_Đóng gói hoàn thành"
]

# =====================================================
# PAGE CONFIG & CSS
# =====================================================
st.set_page_config(page_title="Hệ Thống Quét QR Xưởng", layout="wide", initial_sidebar_state="collapsed")

cookie = EncryptedCookieManager(prefix="qr_system/", password="qr-xuong-san-xuat-2024")
if not cookie.ready():
    st.stop()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; background-color: #0f1117; color: #e0e0e0; }
.sys-header { background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%); border-bottom: 2px solid #00e5a0; padding: 18px 28px; margin: -1rem -1rem 1.5rem -1rem; display: flex; align-items: center; justify-content: space-between; }
.sys-header-left { display:flex; align-items:center; gap:14px; }
.sys-header h1 { font-family: 'IBM Plex Mono', monospace; font-size: 1.3rem; color: #00e5a0; margin: 0; letter-spacing: 2px; text-transform: uppercase; }
.sys-header .dot { width: 10px; height: 10px; border-radius: 50%; background: #00e5a0; box-shadow: 0 0 10px #00e5a0; animation: pulse 2s infinite; }
.user-badge { background:#1a1f2e; border:1px solid #2a3045; border-radius:20px; padding:6px 14px; font-size:0.8rem; color:#00e5a0; font-family:'IBM Plex Mono',monospace; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.card { background: #1a1f2e; border: 1px solid #2a3045; border-radius: 10px; padding: 20px; margin-bottom: 16px; }
.card-title { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #00e5a0; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 14px; border-bottom: 1px solid #2a3045; padding-bottom: 8px; }
.job-row { background: #1a1f2e; border: 1px solid #2a3045; border-left: 3px solid #f59e0b; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; }
.job-headcode { font-family: 'IBM Plex Mono', monospace; font-size: 1rem; font-weight: 600; color: #f59e0b; }
.job-meta { font-size: 0.78rem; color: #94a3b8; margin-top: 2px; }
.login-title { font-family:'IBM Plex Mono',monospace; color:#00e5a0; font-size:1.2rem; text-align:center; margin-bottom:28px; letter-spacing:2px; }
.stTextInput input { background: #0f1117 !important; border: 1px solid #2a3045 !important; color: #e0e0e0 !important; border-radius: 6px !important; font-family: 'IBM Plex Mono', monospace !important; }
.stTextInput input:focus { border-color: #00e5a0 !important; box-shadow: 0 0 0 2px rgba(0,229,160,0.15) !important; }
.stTextInput input:disabled, .stTextInput input[disabled] { background: #1a1f2e !important; color: #00e5a0 !important; border: 1px solid #00e5a0 !important; -webkit-text-fill-color: #00e5a0 !important; opacity: 1 !important; cursor: default !important; font-weight: 600 !important; }
.stFormSubmitButton button { background: linear-gradient(135deg, #00e5a0, #00b37e) !important; color: #0f1117 !important; font-family: 'IBM Plex Mono', monospace !important; font-weight: 700 !important; font-size: 0.95rem !important; border: none !important; border-radius: 8px !important; height: 48px !important; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# API FUNCTIONS & QR DECODER (DÙNG OPENCV NGUYÊN BẢN)
# =====================================================
DATA_CACHE_TTL = 86400

def decode_qr_from_image(image_bytes):
    """Sử dụng thuật toán của OpenCV để nhận diện mã QR độc lập"""
    try:
        file_bytes = np.asarray(bytearray(image_bytes.read()), dtype=np.uint8)
        opencv_img = cv2.imdecode(file_bytes, 1)
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(opencv_img)
        if data:
            return data.strip()
    except Exception:
        pass
    return None

@st.cache_data(ttl=DATA_CACHE_TTL, show_spinner=False)
def fetch_init_data():
    try:
        resp = requests.get(WEB_APP_URL, params={"action":"init"}, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                hc_dict = {}
                for row in data.get("records", []):
                    hc = str(row[0]).strip()
                    if hc:
                        hc_dict[hc] = {"ten_cong_trinh": row[1], "ten_san_pham": row[2]}
                return {"active_jobs_raw": data.get("active_jobs",[]), "hc_dict": hc_dict,
                        "loaded_at": datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M")}
    except Exception:
        pass
    return None

def fetch_active_jobs_from_sheet():
    try:
        resp = requests.get(WEB_APP_URL + "?action=get_active", timeout=15)
        if resp.status_code == 200:
            jobs = {}
            for item in resp.json().get("active_jobs", []):
                jk = f"{item['headcode']}|{item['congdoan']}|{item['nguoibao'].strip().lower()}"
                jobs[jk] = item
            return jobs
    except Exception:
        pass
    return {}

def call_api(payload):
    try:
        resp = requests.post(WEB_APP_URL, json=payload, timeout=15)
        if resp.status_code == 200:
            return True, resp.json()
        return False, {"message": f"HTTP {resp.status_code}"}
    except Exception as ex:
        return False, {"message": str(ex)}

def lookup_in_cache(headcode: str):
    init = fetch_init_data()
    if init is None:
        return None
    info = init["hc_dict"].get(str(headcode).strip())
    return {"status":"found", **info} if info else {"status":"not_found"}

def do_login(user: str, password: str):
    try:
        resp = requests.get(WEB_APP_URL, params={"action":"login","user":user,"pass":password}, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def search_qr_log(query: str):
    try:
        resp = requests.get(WEB_APP_URL, params={"action":"search","query":query.strip()}, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("results", [])
    except Exception:
        pass
    return None

# =====================================================
# SESSION STATE
# =====================================================
defaults = {
    "logged_in":          False,
    "current_user":       "",
    "current_ten":        "",
    "login_error":        "",
    "qr_detected":        "",
    "headcode_val":       "",
    "nguoibao_val":       "",
    "congdoan_val":       DANH_SACH_CONG_DOAN[0],
    "soluong_val":        "",
    "form_key":           0,
    "active_jobs":        {},
    "active_jobs_loaded": False,
    "last_action":        None,
    "last_submit_key":    "",
    "last_submit_time":   0.0,
    "lookup_headcode":    "",
    "lookup_result":      None,
    "prefill_headcode":   "",
    "prefill_nguoibao":   "",
    "prefill_congdoan":   "",
    "prefill_soluong":    "",
    "search_query":       "",
    "search_results":     [],
    "cookie_checked":     False,
    "current_role":       "",   
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.get("logged_in") is not True:
    st.session_state["logged_in"] = False
    if not st.session_state.get("cookie_checked"):
        st.session_state["cookie_checked"] = True
        st.rerun()
    else:
        try:
            saved_user = cookie.get("qr_user", "")
            saved_ten  = cookie.get("qr_ten",  "")
            saved_date = cookie.get("qr_date", "")
            saved_role = cookie.get("qr_role", "")
            today_str  = date.today().strftime("%Y-%m-%d")
            if saved_user and saved_ten and saved_date == today_str:
                st.session_state.logged_in          = True
                st.session_state.current_user       = saved_user
                st.session_state.current_ten        = saved_ten
                st.session_state.current_role       = saved_role
                st.session_state.nguoibao_val       = saved_ten
                st.session_state.active_jobs_loaded = False
                st.rerun()
        except Exception:
            pass

# Trang đăng nhập
if not st.session_state.logged_in:
    st.markdown('<div style="text-align:center; margin-top:60px;"><div style="font-family:\'IBM Plex Mono\',monospace; font-size:1.6rem; color:#00e5a0; letter-spacing:4px;">⚙ HỆ THỐNG QR</div></div>', unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown('<div class="card"><div class="login-title">🔐 ĐĂNG NHẬP</div>', unsafe_allow_html=True)
        with st.form("login_form"):
            user_input = st.text_input("👤 Tên đăng nhập")
            pass_input = st.text_input("🔑 Mật khẩu", type="password")
            login_btn  = st.form_submit_button("▶ ĐĂNG NHẬP", use_container_width=True)
        if login_btn:
            result = do_login(user_input.strip(), pass_input.strip())
            if result and result.get("status") == "ok":
                cookie["qr_user"] = result.get("user")
                cookie["qr_ten"]  = result.get("ten")
                cookie["qr_role"] = result.get("role")
                cookie["qr_date"] = date.today().strftime("%Y-%m-%d")
                cookie.save()
                st.session_state.logged_in = True
                st.session_state.current_user = result.get("user")
                st.session_state.current_ten = result.get("ten")
                st.session_state.current_role = result.get("role")
                st.session_state.active_jobs_loaded = False
                st.rerun()
            else:
                st.error("Sai tài khoản hoặc mật khẩu")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Header thông tin user
col_h1, col_h2 = st.columns([3,1])
with col_h1:
    st.markdown('<div class="sys-header"><div class="sys-header-left"><div class="dot"></div><h1>⚙ Hệ Thống Quét QR Xưởng</h1></div></div>', unsafe_allow_html=True)
with col_h2:
    st.markdown(f'<div style="padding:18px 0; text-align:right;"><span class="user-badge">👤 {st.session_state.current_ten}</span></div>', unsafe_allow_html=True)
    if st.button("🚪 Đăng xuất", use_container_width=True):
        cookie.save()
        st.session_state.clear()
        st.rerun()

if not st.session_state.active_jobs_loaded:
    init_data = fetch_init_data()
    if init_data:
        jobs = {}
        for item in init_data.get("active_jobs_raw", []):
            jk = f"{item['headcode']}|{item['congdoan']}|{item['nguoibao'].strip().lower()}"
            jobs[jk] = item
        st.session_state.active_jobs = jobs
    st.session_state.active_jobs_loaded = True

if st.session_state.prefill_headcode:
    st.session_state.headcode_val = st.session_state.prefill_headcode
    st.session_state.congdoan_val = st.session_state.prefill_congdoan
    st.session_state.soluong_val  = st.session_state.prefill_soluong
    st.session_state.prefill_headcode = ""
    st.session_state.form_key += 1
    st.rerun()

col_scan, col_active = st.columns([1.1, 0.9], gap="large")

with col_scan:
    if normalize_role(st.session_state.current_role) != "sanxuat":
        st.warning("👁 CHẾ ĐỘ XEM: Tài khoản của bạn không có quyền quét hàng.")
    else:
        st.markdown('<div class="card"><div class="card-title">📷 CAMERA QUÉT MÃ QR TRỰC TIẾP</div>', unsafe_allow_html=True)
        
        # Gọi luồng video camera trực tiếp độ trễ thấp
        image_capture = camera_input_live(key=f"live_cam_{st.session_state.form_key}")
        
        if image_capture:
            scanned_qr = decode_qr_from_image(image_capture)
            if scanned_qr and scanned_qr != st.session_state.headcode_val:
                st.session_state.headcode_val = scanned_qr
                result = lookup_in_cache(scanned_qr)
                st.session_state.lookup_headcode = scanned_qr
                st.session_state.lookup_result = result
                st.toast(f"🎉 Đã quét được mã hàng: {scanned_qr}")
                st.rerun()

        if st.session_state.lookup_result and st.session_state.lookup_result.get("status") == "found":
            st.success(f"✅ Đang chọn mã: **{st.session_state.lookup_headcode}**")
        st.markdown('</div>', unsafe_allow_html=True)

        # Form điền dữ liệu tiến độ
        st.markdown('<div class="card"><div class="card-title">📝 Thông tin thao tác</div>', unsafe_allow_html=True)
        
        if st.session_state.lookup_result and st.session_state.lookup_result.get("status") == "found":
            r = st.session_state.lookup_result
            st.markdown(f'<div style="background:#0f2d1f; padding:10px; border-radius:8px; font-size:0.85rem;"><b>Công trình:</b> {r.get("ten_cong_trinh")}<br/><b>Sản phẩm:</b> {r.get("ten_san_pham")}</div>', unsafe_allow_html=True)

        _cd_key = f"_congdoan_{st.session_state.form_key}"
        st.selectbox("Công đoạn *", options=DANH_SACH_CONG_DOAN, index=DANH_SACH_CONG_DOAN.index(st.session_state.congdoan_val) if st.session_state.congdoan_val in DANH_SACH_CONG_DOAN else 0, key=_cd_key)
        st.session_state.congdoan_val = st.session_state[_cd_key]

        _hc_key = f"_headcode_{st.session_state.form_key}"
        def on_manual_hc():
            hc = st.session_state[_hc_key].strip()
            st.session_state.headcode_val = hc
            st.session_state.lookup_result = lookup_in_cache(hc)
            st.session_state.lookup_headcode = hc
        st.text_input("Headcode * (Quét tự động điền hoặc nhập tay)", value=st.session_state.headcode_val, key=_hc_key, on_change=on_manual_hc)

        hc_live = st.session_state.headcode_val.strip()
        _, is_active_live = (hc_live, hc_live|st.session_state.congdoan_val|st.session_state.current_ten.lower() in st.session_state.active_jobs) if hc_live else ("", False)
        mode_label = "🏁 HOÀN THÀNH" if is_active_live else "▶️ BẮT ĐẦU"

        with st.form(key=f"main_form_{st.session_state.form_key}"):
            soluong_str = st.text_input("Số lượng", value=st.session_state.soluong_val)
            submit = st.form_submit_button(label=f"💾 XÁC NHẬN — {mode_label}", use_container_width=True)

        if submit:
            headcode = st.session_state.headcode_val.strip()
            try: soluong = float(soluong_str.replace(",","."))
            except: soluong = None

            if not headcode or soluong is None:
                st.error("Vui lòng điền đầy đủ thông tin mã hàng và số lượng.")
            else:
                job_key = f"{headcode}|{st.session_state.congdoan_val}|{st.session_state.current_ten.lower()}"
                if job_key not in st.session_state.active_jobs:
                    payload = {"action":"start","headcode":headcode,"congdoan":st.session_state.congdoan_val,"soluong":soluong,"nguoibao":st.session_state.current_ten}
                    ok, resp = call_api(payload)
                    if ok and resp.get("status") == "ok":
                        st.session_state.active_jobs[job_key] = {"headcode":headcode,"congdoan":st.session_state.congdoan_val,"nguoibao":st.session_state.current_ten,"soluong":soluong,"gio_bat_dau":resp.get("gio_bat_dau"),"row_id":resp.get("row_id")}
                        st.session_state.headcode_val = ""; st.session_state.lookup_result = None; st.session_state.form_key += 1
                        st.rerun()
                else:
                    info = st.session_state.active_jobs[job_key]
                    payload = {"action":"finish","headcode":headcode,"congdoan":st.session_state.congdoan_val,"soluong":soluong,"nguoibao":st.session_state.current_ten,"gio_bat_dau":info["gio_bat_dau"],"gio_hoan_thanh":datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M:%S"),"row_id":info.get("row_id")}
                    ok, resp = call_api(payload)
                    if ok and resp.get("status") == "ok":
                        del st.session_state.active_jobs[job_key]
                        st.session_state.headcode_val = ""; st.session_state.lookup_result = None; st.session_state.form_key += 1
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with col_active:
    st.markdown('<div class="card"><div class="card-title">⚡ Đang xử lý tại xưởng</div>', unsafe_allow_html=True)
    if not st.session_state.active_jobs:
        st.caption("Chưa có lệnh hàng nào đang xử lý.")
    else:
        for jk, job in list(st.session_state.active_jobs.items()):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f'<div class="job-row"><b style="color:#f59e0b;">{job["headcode"]}</b><br/><span style="font-size:0.75rem; color:#94a3b8;">{job["congdoan"]} | SL: {job["soluong"]}</span></div>', unsafe_allow_html=True)
            with c2:
                if st.button("Xong", key=f"f_{jk}"):
                    st.session_state.prefill_headcode = job["headcode"]
                    st.session_state.congdoan_val = job["congdoan"]
                    st.session_state.soluong_val = str(job["soluong"])
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
