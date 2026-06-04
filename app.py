import streamlit as st
import requests
import cv2
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo
import time

# =====================================================
# CẤU HÌNH
# =====================================================
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxvwuD1SFZ8R1BzbccOC2-ZmUaHxRN4vOkmkghM_mFmUlnpx9ZO7GC4ZCktJwnfpVH1/exec"
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

# CSS toàn cục (luôn load — cần thiết cho cả trang login lẫn app)
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
.badge-doing { background: #1a2e1a; color: #4ade80; border: 1px solid #4ade80; padding: 3px 10px; border-radius: 20px; font-size: 0.7rem; font-family: 'IBM Plex Mono', monospace; font-weight: 600; }
.job-row { background: #1a1f2e; border: 1px solid #2a3045; border-left: 3px solid #f59e0b; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; }
.job-headcode { font-family: 'IBM Plex Mono', monospace; font-size: 1rem; font-weight: 600; color: #f59e0b; }
.job-meta { font-size: 0.78rem; color: #94a3b8; margin-top: 2px; }
.login-wrap { min-height: 80vh; display: flex; align-items: center; justify-content: center; }
.login-box { width: 100%; max-width: 400px; padding: 40px; background: #1a1f2e; border: 1px solid #2a3045; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,229,160,0.08); }
.login-title { font-family:'IBM Plex Mono',monospace; color:#00e5a0; font-size:1.2rem; text-align:center; margin-bottom:28px; letter-spacing:2px; }
.login-logo { text-align:center; margin-bottom:24px; }
.login-logo-text { font-family:'IBM Plex Mono',monospace; font-size:1.6rem; color:#00e5a0; letter-spacing:4px; }
.login-logo-sub { color:#64748b; font-size:0.85rem; margin-top:6px; }
.stTextInput input { background: #0f1117 !important; border: 1px solid #2a3045 !important; color: #e0e0e0 !important; border-radius: 6px !important; font-family: 'IBM Plex Mono', monospace !important; }
.stTextInput input:focus { border-color: #00e5a0 !important; box-shadow: 0 0 0 2px rgba(0,229,160,0.15) !important; }
.stTextInput input:disabled, .stTextInput input[disabled] { background: #1a1f2e !important; color: #00e5a0 !important; border: 1px solid #00e5a0 !important; -webkit-text-fill-color: #00e5a0 !important; opacity: 1 !important; cursor: default !important; font-weight: 600 !important; }
.stFormSubmitButton button { background: linear-gradient(135deg, #00e5a0, #00b37e) !important; color: #0f1117 !important; font-family: 'IBM Plex Mono', monospace !important; font-weight: 700 !important; font-size: 0.95rem !important; border: none !important; border-radius: 8px !important; height: 48px !important; }
.stFormSubmitButton button:hover { opacity: 0.9 !important; transform: translateY(-1px); }
.stAlert { border-radius: 8px !important; }
div[data-testid="stFileUploaderDropzone"] { padding: 10px !important; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# API FUNCTIONS
# =====================================================
DATA_CACHE_TTL = 86400

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
# Khởi tạo session state — chỉ set nếu key chưa tồn tại
# "logged_in" mặc định False → bắt buộc qua trang login mỗi phiên mới
defaults = {
    # Auth — QUAN TRỌNG: logged_in phải là False khi chưa xác thực
    "logged_in":          False,
    "current_user":       "",
    "current_ten":        "",
    "login_error":        "",
    # App state
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
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# GUARD: nếu logged_in không phải bool True thì reset về False
if st.session_state.get("logged_in") is not True:
    st.session_state["logged_in"] = False

# =====================================================
# TRANG ĐĂNG NHẬP — chặn toàn bộ nội dung phía dưới nếu chưa login
# =====================================================
if not st.session_state.logged_in:
    st.markdown("""
    <div style="max-width:420px; margin:60px auto 0 auto; text-align:center;">
        <div style="font-family:'IBM Plex Mono',monospace; font-size:1.6rem;
                    color:#00e5a0; letter-spacing:4px; margin-bottom:6px;">⚙ HỆ THỐNG QR</div>
        <div style="color:#64748b; font-size:0.85rem; margin-bottom:32px;">Xưởng Sản Xuất — Vui lòng đăng nhập</div>
    </div>
    """, unsafe_allow_html=True)

    _, col_center, _ = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">🔐 ĐĂNG NHẬP</div>', unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            user_input = st.text_input("👤 Tên đăng nhập", placeholder="Nhập username...")
            pass_input = st.text_input("🔑 Mật khẩu", type="password", placeholder="Nhập mật khẩu...")
            login_btn  = st.form_submit_button("▶ ĐĂNG NHẬP", use_container_width=True)

        if st.session_state.login_error:
            st.error(st.session_state.login_error)

        if login_btn:
            if not user_input.strip() or not pass_input.strip():
                st.session_state.login_error = "⚠️ Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu."
                st.rerun()
            else:
                with st.spinner("Đang xác thực..."):
                    result = do_login(user_input.strip(), pass_input.strip())
                if result and result.get("status") == "ok":
                    st.session_state.logged_in          = True
                    st.session_state.current_user       = result.get("user", user_input.strip())
                    st.session_state.current_ten        = result.get("ten", user_input.strip())
                    st.session_state.nguoibao_val       = result.get("ten", user_input.strip())
                    st.session_state.login_error        = ""
                    st.session_state.active_jobs_loaded = False
                    st.rerun()
                elif result:
                    st.session_state.login_error = f"❌ {result.get('message', 'Sai tên đăng nhập hoặc mật khẩu')}"
                    st.rerun()
                else:
                    st.session_state.login_error = "❌ Không thể kết nối tới máy chủ. Vui lòng thử lại."
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # QUAN TRỌNG: st.stop() dừng render — không cho hiện app khi chưa login
    st.stop()

# =====================================================
# ĐÃ ĐĂNG NHẬP — HEADER
# =====================================================
col_h1, col_h2 = st.columns([3,1])
with col_h1:
    st.markdown("""
    <div class="sys-header">
        <div class="sys-header-left">
            <div class="dot"></div>
            <h1>⚙ Hệ Thống Quét QR Xưởng Sản Xuất</h1>
        </div>
    </div>""", unsafe_allow_html=True)
with col_h2:
    st.markdown(f"""
    <div style="padding:18px 0; text-align:right;">
        <span class="user-badge">👤 {st.session_state.current_ten}</span>
    </div>""", unsafe_allow_html=True)
    if st.button("🚪 Đăng xuất", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# =====================================================
# LOAD INIT DATA (lần đầu)
# =====================================================
if not st.session_state.active_jobs_loaded:
    with st.spinner("🔄 Đang khởi động hệ thống..."):
        init_data = fetch_init_data()
        if init_data:
            jobs = {}
            for item in init_data.get("active_jobs_raw", []):
                jk = f"{item['headcode']}|{item['congdoan']}|{item['nguoibao'].strip().lower()}"
                jobs[jk] = item
            st.session_state.active_jobs = jobs
        st.session_state.active_jobs_loaded = True

# =====================================================
# PREFILL TỪ DANH SÁCH
# =====================================================
if st.session_state.prefill_headcode:
    st.session_state.qr_detected     = st.session_state.prefill_headcode
    st.session_state.headcode_val    = st.session_state.prefill_headcode
    st.session_state.congdoan_val    = st.session_state.prefill_congdoan
    st.session_state.soluong_val     = st.session_state.prefill_soluong
    st.session_state.prefill_headcode = ""
    st.session_state.prefill_nguoibao = ""
    st.session_state.prefill_congdoan = ""
    st.session_state.prefill_soluong  = ""
    st.session_state.form_key += 1
    st.rerun()

# =====================================================
# REALTIME JOB STATE
# =====================================================
def get_current_job_state():
    hc = st.session_state.headcode_val.strip()
    cd = st.session_state.congdoan_val
    nb = st.session_state.current_ten.strip()
    if hc and nb:
        jk = f"{hc}|{cd}|{nb.lower()}"
        return jk, jk in st.session_state.active_jobs
    return "", False

# =====================================================
# LAYOUT
# =====================================================
col_scan, col_active = st.columns([1.1, 0.9], gap="large")

# ─────────────────────────────────────────────────
# CỘT TRÁI
# ─────────────────────────────────────────────────
with col_scan:
    # Camera
    st.markdown('<div class="card"><div class="card-title">📷 Quét mã QR</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("▶️ BẤM ĐỂ MỞ CAMERA CHỤP MÃ QR",
        type=["jpg","jpeg","png"], accept_multiple_files=False,
        key=f"cam_{st.session_state.form_key}")
    if uploaded_file is not None:
        try:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            opencv_img = cv2.imdecode(file_bytes, 1)
            detector   = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(opencv_img)
            if data:
                if data != st.session_state.qr_detected:
                    st.session_state.qr_detected  = data
                    st.session_state.headcode_val = data
                    result = lookup_in_cache(data)
                    st.session_state.lookup_headcode = data
                    st.session_state.lookup_result   = result
                    st.session_state.form_key += 1
                    st.rerun()
            else:
                st.error("❌ Không tìm thấy mã QR. Vui lòng chụp rõ hơn!")
        except Exception as ex:
            st.error(f"Lỗi: {ex}")

    if st.session_state.lookup_result and st.session_state.lookup_result.get("status") == "found":
        r = st.session_state.lookup_result
        st.success(f"✅ **{st.session_state.lookup_headcode}** — {r.get('ten_san_pham','')}")
    elif st.session_state.lookup_headcode and st.session_state.lookup_result and st.session_state.lookup_result.get("status") == "not_found":
        st.error(f"❌ Mã **{st.session_state.lookup_headcode}** không tồn tại!")
    st.markdown('</div>', unsafe_allow_html=True)

    # Form
    st.markdown('<div class="card"><div class="card-title">📝 Thông tin thao tác</div>', unsafe_allow_html=True)

    # Thông tin sản phẩm
    if st.session_state.lookup_result and st.session_state.lookup_result.get("status") == "found":
        r = st.session_state.lookup_result
        st.markdown(f"""
        <div style="background:#0f2d1f; border:1px solid #00e5a0; border-radius:8px;
                    padding:10px 14px; margin-bottom:12px; font-size:0.82rem;">
            <div style="color:#00e5a0; font-family:IBM Plex Mono,monospace;
                        font-size:0.7rem; letter-spacing:1px; margin-bottom:6px;">📦 THÔNG TIN SẢN PHẨM</div>
            <div style="color:#e0e0e0;"><b>Công trình:</b> {r.get('ten_cong_trinh','')}</div>
            <div style="color:#e0e0e0; margin-top:4px;"><b>Sản phẩm:</b> {r.get('ten_san_pham','')}</div>
        </div>""", unsafe_allow_html=True)

    # ── Công đoạn (ngoài form, realtime) ──
    _cd_key = f"_congdoan_{st.session_state.form_key}"
    def on_congdoan_change():
        st.session_state.congdoan_val = st.session_state[_cd_key]
    st.selectbox("Công đoạn *", options=DANH_SACH_CONG_DOAN,
        index=DANH_SACH_CONG_DOAN.index(st.session_state.congdoan_val)
              if st.session_state.congdoan_val in DANH_SACH_CONG_DOAN else 0,
        key=_cd_key, on_change=on_congdoan_change)

    # ── Người vận hành: hiển thị readonly (từ tài khoản đăng nhập) ──
    st.text_input("Người vận hành", value=st.session_state.current_ten,
                  disabled=True, key=f"nb_display_{st.session_state.form_key}")

    # Banner trạng thái
    job_key_live, is_active_live = get_current_job_state()
    if not st.session_state.headcode_val.strip():
        st.info("📷 Quét QR hoặc nhập tay Headcode")
    elif is_active_live:
        job_info = st.session_state.active_jobs[job_key_live]
        st.warning(f"🔄 Đang làm từ **{job_info['gio_bat_dau']}** → Xác nhận **HOÀN THÀNH**")
    else:
        st.info(f"🚀 Chưa bắt đầu → Xác nhận **BẮT ĐẦU**")
    mode_label = "🏁 HOÀN THÀNH" if is_active_live else "▶️ BẮT ĐẦU"

    # ── Headcode (ngoài form, realtime lookup) ──
    _hc_key = f"_headcode_{st.session_state.form_key}"
    def on_headcode_change():
        new_hc = st.session_state[_hc_key].strip()
        st.session_state.headcode_val = new_hc
        st.session_state.qr_detected  = new_hc
        if new_hc:
            result = lookup_in_cache(new_hc)
            st.session_state.lookup_headcode = new_hc
            st.session_state.lookup_result   = result
        else:
            st.session_state.lookup_headcode = ""
            st.session_state.lookup_result   = None

    st.text_input("Headcode *", value=st.session_state.headcode_val,
        key=_hc_key, on_change=on_headcode_change,
        placeholder="Quét QR hoặc nhập tay...")

    # Fallback lookup nếu chưa lookup
    hc_live = st.session_state.headcode_val.strip()
    if hc_live and hc_live != st.session_state.lookup_headcode:
        result = lookup_in_cache(hc_live)
        st.session_state.lookup_headcode = hc_live
        st.session_state.lookup_result   = result

    with st.form(key=f"main_form_{st.session_state.form_key}", clear_on_submit=False):
        headcode = st.session_state.headcode_val.strip()
        soluong_str = st.text_input("Số lượng", value=st.session_state.soluong_val,
            placeholder="Nhập số lượng...",
            key=f"soluong_{st.session_state.form_key}")
        try:
            soluong = float(soluong_str.replace(",",".")) if soluong_str.strip() else None
        except ValueError:
            soluong = None
        submit = st.form_submit_button(
            label=f"💾 XÁC NHẬN — {mode_label}", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── SUBMIT ──
    if submit:
        nguoibao = st.session_state.current_ten.strip()  # Luôn lấy từ tài khoản
        congdoan  = st.session_state.congdoan_val

        _submit_key = f"{headcode}|{congdoan}|{nguoibao}"
        _now = time.time()
        _is_dup = (_submit_key == st.session_state.last_submit_key and
                   (_now - st.session_state.last_submit_time) < 5.0)
        if not _is_dup:
            st.session_state.last_submit_key  = _submit_key
            st.session_state.last_submit_time = _now

        if _is_dup:
            st.warning("⚠️ Thao tác vừa được ghi nhận, vui lòng chờ...")
        elif not headcode:
            st.error("Vui lòng quét hoặc điền Headcode.")
        elif soluong is None:
            st.error("Vui lòng nhập số lượng hợp lệ.")
        elif headcode != st.session_state.lookup_headcode:
            st.error("❌ Headcode chưa được kiểm tra. Vui lòng nhập lại.")
            st.session_state.headcode_val = ""; st.session_state.lookup_headcode = ""
            st.session_state.lookup_result = None; st.session_state.form_key += 1
            st.rerun()
        elif not st.session_state.lookup_result or st.session_state.lookup_result.get("status") != "found":
            st.error("❌ Headcode không hợp lệ.")
            st.session_state.headcode_val = ""; st.session_state.lookup_headcode = ""
            st.session_state.lookup_result = None; st.session_state.form_key += 1
            st.rerun()
        else:
            job_key   = f"{headcode}|{congdoan}|{nguoibao.lower()}"
            is_active = job_key in st.session_state.active_jobs

            if not is_active:
                payload = {"action":"start","headcode":headcode,"congdoan":congdoan,
                           "soluong":soluong,"nguoibao":nguoibao}
                with st.spinner("Đang ghi nhận bắt đầu..."):
                    ok, resp_data = call_api(payload)
                if ok and resp_data.get("status") == "ok":
                    st.session_state.active_jobs[job_key] = {
                        "headcode":headcode,"congdoan":congdoan,"nguoibao":nguoibao,
                        "soluong":soluong,"gio_bat_dau":resp_data.get("gio_bat_dau",""),
                        "row_id":resp_data.get("row_id",""),
                    }
                    st.session_state.last_action = {"type":"start","headcode":headcode,"congdoan":congdoan}
                    st.session_state.qr_detected = ""; st.session_state.headcode_val = ""
                    st.session_state.lookup_headcode = ""; st.session_state.lookup_result = None
                    st.session_state.soluong_val = ""; st.session_state.form_key += 1
                    st.rerun()
                elif resp_data.get("status") == "duplicate":
                    st.warning("⚠️ Mã đã được ghi nhận. Đang đồng bộ...")
                    st.session_state.active_jobs = fetch_active_jobs_from_sheet()
                    st.session_state.form_key += 1; st.rerun()
                else:
                    st.error(f"Lỗi: {resp_data.get('message','Không rõ')}")
            else:
                job_info = st.session_state.active_jobs[job_key]
                payload  = {"action":"finish","headcode":headcode,"congdoan":congdoan,
                            "soluong":soluong,"nguoibao":nguoibao,
                            "gio_bat_dau":job_info["gio_bat_dau"],
                            "gio_hoan_thanh":datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M:%S"),
                            "row_id":job_info.get("row_id","")}
                with st.spinner("Đang cập nhật hoàn thành..."):
                    ok, resp_data = call_api(payload)
                if ok and resp_data.get("status") == "ok":
                    del st.session_state.active_jobs[job_key]
                    st.session_state.last_action = {"type":"finish","headcode":headcode,"congdoan":congdoan}
                    st.session_state.qr_detected = ""; st.session_state.headcode_val = ""
                    st.session_state.lookup_headcode = ""; st.session_state.lookup_result = None
                    st.session_state.soluong_val = ""; st.session_state.form_key += 1
                    st.rerun()
                else:
                    st.error(f"Lỗi: {resp_data.get('message','Không rõ')}")

# ─────────────────────────────────────────────────
# CỘT PHẢI
# ─────────────────────────────────────────────────
with col_active:
    if st.session_state.last_action:
        act = st.session_state.last_action
        if act["type"] == "start":
            st.success(f"🚀 ĐÃ BẮT ĐẦU: **{act['headcode']}** — {act['congdoan']}")
        else:
            st.success(f"🏁 ĐÃ HOÀN THÀNH: **{act['headcode']}** — {act['congdoan']}")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🔄 Làm mới danh sách", use_container_width=True):
            st.session_state.active_jobs = fetch_active_jobs_from_sheet()
            st.rerun()
    with col_r2:
        if st.button("🗄️ Làm mới dữ liệu DATA", use_container_width=True):
            fetch_init_data.clear()
            st.session_state.lookup_headcode = ""; st.session_state.lookup_result = None
            st.success("✅ Đã xóa cache!"); st.rerun()

    init_info = fetch_init_data()
    loaded_at = init_info["loaded_at"] if init_info else None
    if loaded_at:
        st.markdown(f'<div style="font-size:0.72rem; color:#64748b; text-align:center; margin-bottom:8px;">'
                    f'🗄️ DATA: <b style="color:#94a3b8">{loaded_at}</b> | Tự làm mới sau 24h</div>',
                    unsafe_allow_html=True)

    # Danh sách đang xử lý
    st.markdown('<div class="card"><div class="card-title">⚡ Đang xử lý</div>', unsafe_allow_html=True)
    active_jobs = st.session_state.active_jobs
    if not active_jobs:
        st.markdown('<p style="color:#64748b; font-size:0.85rem; font-family:IBM Plex Mono,monospace;">— Chưa có công việc nào —</p>', unsafe_allow_html=True)
    else:
        for jk, job in list(active_jobs.items()):
            c_info, c_btn = st.columns([3,1])
            with c_info:
                st.markdown(f"""
                <div class="job-row">
                    <div class="job-headcode">{job['headcode']}</div>
                    <div class="job-meta">{job['congdoan']}</div>
                    <div class="job-meta">👤 {job['nguoibao']} | 📦 {job.get('soluong',0)}</div>
                    <div class="job-meta" style="color:#64748b;font-size:0.72rem;">🕐 {job['gio_bat_dau']}</div>
                </div>""", unsafe_allow_html=True)
            with c_btn:
                if st.button("✅ Xong", key=f"finish_btn_{jk}", use_container_width=True):
                    # Kiểm tra người thực hiện có khớp với người đang đăng nhập không
                    job_nguoi   = job["nguoibao"].strip().lower()
                    login_nguoi = st.session_state.current_ten.strip().lower()
                    if job_nguoi != login_nguoi:
                        st.session_state[f"owner_err_{jk}"] = True
                    else:
                        st.session_state.pop(f"owner_err_{jk}", None)
                        sl = job.get("soluong","")
                        st.session_state.prefill_headcode = job["headcode"]
                        st.session_state.prefill_nguoibao = job["nguoibao"]
                        st.session_state.prefill_congdoan = job["congdoan"]
                        st.session_state.prefill_soluong  = str(sl) if sl != "" else ""
                    st.rerun()
                # Hiển thị cảnh báo nếu sai người
                if st.session_state.get(f"owner_err_{jk}"):
                    st.warning("⚠️ Mã hàng này không phải mã hàng bạn đang thực hiện")
    st.markdown('</div>', unsafe_allow_html=True)

    # Hướng dẫn
    st.markdown("""
    <div class="card">
        <div class="card-title">📖 Hướng dẫn</div>
        <div style="font-size:0.82rem; color:#94a3b8; line-height:1.8;">
            <b style="color:#f59e0b">Lần quét 1</b> → <span style="color:#4ade80">BẮT ĐẦU</span><br/>
            <b style="color:#818cf8">Lần quét 2</b> → <span style="color:#818cf8">HOÀN THÀNH</span><br/>
            <b style="color:#00e5a0">Nút ✅ Xong</b> → Chọn nhanh từ danh sách<br/><br/>
            <span style="color:#64748b">⚠ Danh sách tự khôi phục khi mở lại app</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Tra cứu QR_Log ──
    st.markdown('<div class="card"><div class="card-title">🔍 Tra cứu lịch sử QR_Log</div>', unsafe_allow_html=True)

    def on_search_change():
        st.session_state.search_query   = st.session_state["_search_input"]
        st.session_state.search_results = []

    st.text_input("Nhập số đuôi headcode (3+ ký tự)",
        value=st.session_state.search_query, key="_search_input",
        on_change=on_search_change, placeholder="VD: 878 → tìm ...878")

    q = st.session_state.search_query.strip()
    if len(q) >= 3 and not st.session_state.search_results:
        with st.spinner("🔍 Đang tìm kiếm..."):
            rows = search_qr_log(q)
        if rows is None:
            st.error("❌ Không thể kết nối.")
        elif len(rows) == 0:
            st.info("Không tìm thấy kết quả nào.")
            st.session_state.search_results = ["__empty__"]
        else:
            st.session_state.search_results = rows

    results = st.session_state.search_results
    if results and results != ["__empty__"]:
        st.markdown(f'<div style="font-size:0.75rem;color:#00e5a0;margin-bottom:8px;">Tìm thấy <b>{len(results)}</b> kết quả</div>', unsafe_allow_html=True)
        st.markdown("""<div style="display:grid;grid-template-columns:1.2fr 1.5fr 0.6fr 0.8fr 1fr 1fr 0.7fr;
            gap:4px;padding:6px 8px;background:#0f1117;border-radius:6px;margin-bottom:4px;
            font-family:IBM Plex Mono,monospace;font-size:0.63rem;color:#64748b;text-transform:uppercase;">
            <div>Headcode</div><div>Công đoạn</div><div>SL</div><div>Người</div>
            <div>Bắt đầu</div><div>Hoàn thành</div><div>TT</div></div>""", unsafe_allow_html=True)
        for row in results:
            tt    = row.get("trang_thai","")
            color = "#4ade80" if tt=="ĐANG LÀM" else "#818cf8" if tt=="HOÀN THÀNH" else "#94a3b8"
            sl    = row.get("soluong","")
            try: sl = f"{float(sl):.3f}" if sl != "" else ""
            except: sl = str(sl)
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:1.2fr 1.5fr 0.6fr 0.8fr 1fr 1fr 0.7fr;
                gap:4px;padding:8px;background:#1a1f2e;border:1px solid #2a3045;
                border-left:3px solid {color};border-radius:6px;margin-bottom:4px;
                font-size:0.72rem;color:#e0e0e0;">
                <div style="font-family:IBM Plex Mono,monospace;color:#f59e0b;font-weight:600;">{row.get('headcode','')}</div>
                <div style="color:#94a3b8;font-size:0.65rem;">{row.get('congdoan','')}</div>
                <div>{sl}</div>
                <div style="color:#94a3b8;">{row.get('nguoibao','')}</div>
                <div style="font-size:0.63rem;">{row.get('gio_bat_dau','')}</div>
                <div style="font-size:0.63rem;">{row.get('gio_hoan_thanh','')}</div>
                <div style="color:{color};font-weight:600;font-size:0.65rem;">{tt}</div>
            </div>""", unsafe_allow_html=True)
    elif q and len(q) < 3:
        st.caption("Nhập ít nhất 3 số đuôi để tìm kiếm.")
    st.markdown('</div>', unsafe_allow_html=True)
