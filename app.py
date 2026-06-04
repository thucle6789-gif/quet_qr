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
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyb03gkCikQtY9BtLcGBs25283b9eWXzAEzvKpuGFJvv0NiMjZrlEJcqEuHoDBp6zLGnA/exec"
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
.job-row { background: #1a1f2e; border: 1px solid #2a3045; border-left: 3px solid #f59e0b; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; }
.job-headcode { font-family: 'IBM Plex Mono', monospace; font-size: 1rem; font-weight: 600; color: #f59e0b; }
.job-meta { font-size: 0.78rem; color: #94a3b8; margin-top: 2px; }
.stTextInput input, .stSelectbox select, .stNumberInput input { background: #0f1117 !important; border: 1px solid #2a3045 !important; color: #e0e0e0 !important; border-radius: 6px !important; font-family: 'IBM Plex Mono', monospace !important; }
.stTextInput input:focus { border-color: #00e5a0 !important; box-shadow: 0 0 0 2px rgba(0,229,160,0.15) !important; }
.stFormSubmitButton button { background: linear-gradient(135deg, #00e5a0, #00b37e) !important; color: #0f1117 !important; font-family: 'IBM Plex Mono', monospace !important; font-weight: 700 !important; font-size: 0.95rem !important; letter-spacing: 1px !important; border: none !important; border-radius: 8px !important; height: 48px !important; }
.stFormSubmitButton button:disabled { opacity: 0.5 !important; cursor: not-allowed !important; }
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
# HÀM GỌI API
# =====================================================
# =====================================================
# Cache DATA 24h — chỉ gọi API 1 lần khi app khởi động
# Khi DATA có mã mới → bấm "Làm mới dữ liệu DATA" để clear cache
# =====================================================
DATA_CACHE_TTL = 86400  # 24 giờ

@st.cache_data(ttl=DATA_CACHE_TTL, show_spinner=False)
def fetch_init_data():
    """
    Gọi 1 request DUY NHẤT khi app khởi động, lấy cả:
    - active_jobs (danh sách đang làm từ QR_Log)
    - records (toàn bộ mã hợp lệ từ DATA)
    Tránh 2 request song song gây tranh lock Apps Script.
    """
    try:
        resp = requests.get(
            WEB_APP_URL,
            params={"action": "init"},
            timeout=60  # DATA lớn, cần thời gian
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                # Build dict headcode → info
                hc_dict = {}
                for row in data.get("records", []):
                    hc = str(row[0]).strip()
                    if hc:
                        hc_dict[hc] = {
                            "ten_cong_trinh": row[1],
                            "ten_san_pham":   row[2],
                        }
                loaded_at = datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M")
                return {
                    "active_jobs_raw": data.get("active_jobs", []),
                    "hc_dict":         hc_dict,
                    "loaded_at":       loaded_at,
                }
    except Exception:
        pass
    return None

def fetch_active_jobs_from_sheet():
    """Gọi riêng get_active khi cần refresh danh sách (bấm nút làm mới)."""
    try:
        resp = requests.get(WEB_APP_URL + "?action=get_active", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            jobs = {}
            for item in data.get("active_jobs", []):
                jk = f"{item['headcode']}|{item['congdoan']}|{item['nguoibao'].strip().lower()}"
                jobs[jk] = item
            return jobs
    except Exception:
        pass
    return {}

def call_api(payload):
    """Gọi POST API, trả về (ok: bool, data: dict)."""
    try:
        resp = requests.post(WEB_APP_URL, json=payload, timeout=15)
        if resp.status_code == 200:
            return True, resp.json()
        return False, {"message": f"HTTP {resp.status_code}"}
    except Exception as ex:
        return False, {"message": str(ex)}

def lookup_in_cache(headcode: str):
    """Tra cứu headcode trong cache dict. < 1ms, không gọi API."""
    init = fetch_init_data()
    if init is None:
        return None  # Lỗi kết nối
    hc   = str(headcode).strip()
    info = init["hc_dict"].get(hc)
    if info:
        return {"status": "found", **info}
    return {"status": "not_found"}

# =====================================================
# SESSION STATE INIT
# =====================================================
defaults = {
    "qr_detected":        "",
    "nguoibao_val":       "",
    "congdoan_val":       DANH_SACH_CONG_DOAN[0],
    "soluong_val":        1.000,
    "form_key":           0,
    "active_jobs":        {},
    "active_jobs_loaded": False,
    "last_action":        None,
    # Khi bấm nút hoàn thành từ danh sách → prefill form
    "last_submit_key":    "",   # Chặn double-submit
    "last_submit_time":   0.0,
    # Kết quả lookup headcode từ sheet DATA
    "headcode_val":       "",   # giá trị ô headcode realtime (ngoài form)
    "lookup_headcode":    "",   # headcode đã lookup
    "lookup_result":      None, # dict {status, ten_cong_trinh, ten_san_pham} hoặc None
    "prefill_headcode":   "",
    "prefill_nguoibao":   "",
    "prefill_congdoan":   "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Load active jobs lần đầu
if not st.session_state.active_jobs_loaded:
    with st.spinner("🔄 Đang khởi động hệ thống (lần đầu có thể mất 10-20s)..."):
        init_data = fetch_init_data()
        if init_data:
            jobs = {}
            for item in init_data.get("active_jobs_raw", []):
                jk = f"{item['headcode']}|{item['congdoan']}|{item['nguoibao'].strip().lower()}"
                jobs[jk] = item
            st.session_state.active_jobs = jobs
        else:
            st.session_state.active_jobs = {}
        st.session_state.active_jobs_loaded = True

# =====================================================
# XỬ LÝ PREFILL TỪ DANH SÁCH (bấm nút Hoàn thành trên job card)
# Phải xử lý TRƯỚC khi render form để giá trị kịp hiển thị
# =====================================================
if st.session_state.prefill_headcode:
    st.session_state.qr_detected    = st.session_state.prefill_headcode
    st.session_state.headcode_val    = st.session_state.prefill_headcode
    st.session_state.nguoibao_val   = st.session_state.prefill_nguoibao
    st.session_state.congdoan_val   = st.session_state.prefill_congdoan
    st.session_state.prefill_headcode = ""
    st.session_state.prefill_nguoibao = ""
    st.session_state.prefill_congdoan = ""
    st.session_state.form_key += 1
    st.rerun()

# =====================================================
# TÍNH TRẠNG THÁI REALTIME
# =====================================================
def get_current_job_state():
    hc = st.session_state.qr_detected.strip()
    cd = st.session_state.congdoan_val
    nb = st.session_state.nguoibao_val.strip()
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
            detector   = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(opencv_img)
            if data:
                if data != st.session_state.qr_detected:
                    st.session_state.qr_detected = data
                    st.session_state.headcode_val = data
                    st.session_state.form_key += 1
                    st.rerun()
            else:
                st.error("❌ Không tìm thấy mã QR. Vui lòng chụp rõ hơn!")
        except Exception as ex:
            st.error(f"Lỗi xử lý ảnh: {ex}")

    if st.session_state.lookup_result and st.session_state.lookup_result.get("status") == "found":
        r = st.session_state.lookup_result
        st.success(f"✅ **{st.session_state.lookup_headcode}** — {r.get('ten_san_pham','')}")
    elif st.session_state.lookup_headcode:
        st.error(f"❌ Mã **{st.session_state.lookup_headcode}** không tồn tại!")
    st.markdown('</div>', unsafe_allow_html=True)

    # Form
    st.markdown('<div class="card"><div class="card-title">📝 Thông tin thao tác</div>', unsafe_allow_html=True)

    # Hiển thị thông tin sản phẩm nếu đã lookup thành công
    if (st.session_state.lookup_result and
            st.session_state.lookup_result.get("status") == "found"):
        r = st.session_state.lookup_result
        st.markdown(f"""
        <div style="background:#0f2d1f; border:1px solid #00e5a0; border-radius:8px;
                    padding:10px 14px; margin-bottom:12px; font-size:0.82rem;">
            <div style="color:#00e5a0; font-family:IBM Plex Mono,monospace;
                        font-size:0.7rem; letter-spacing:1px; margin-bottom:6px;">
                📦 THÔNG TIN SẢN PHẨM
            </div>
            <div style="color:#e0e0e0;">
                <b>Công trình:</b> {r.get('ten_cong_trinh','')}
            </div>
            <div style="color:#e0e0e0; margin-top:4px;">
                <b>Sản phẩm:</b> {r.get('ten_san_pham','')}
            </div>
        </div>
        """, unsafe_allow_html=True)


    # Người vận hành & công đoạn NGOÀI form để cập nhật realtime
    # ✅ Key động theo form_key → khi prefill từ danh sách, form_key tăng
    # → widget tạo mới hoàn toàn với value= mới, không bị Streamlit giữ giá trị cũ
    _nb_key = f"_nguoibao_{st.session_state.form_key}"
    _cd_key = f"_congdoan_{st.session_state.form_key}"

    def on_nguoibao_change():
        st.session_state.nguoibao_val = st.session_state[_nb_key]

    def on_congdoan_change():
        st.session_state.congdoan_val = st.session_state[_cd_key]

    st.text_input(
        "Người vận hành *",
        value=st.session_state.nguoibao_val,
        key=_nb_key,
        on_change=on_nguoibao_change,
        placeholder="Gõ tên rồi Enter...",
    )
    st.selectbox(
        "Công đoạn *",
        options=DANH_SACH_CONG_DOAN,
        index=DANH_SACH_CONG_DOAN.index(st.session_state.congdoan_val)
              if st.session_state.congdoan_val in DANH_SACH_CONG_DOAN else 0,
        key=_cd_key,
        on_change=on_congdoan_change,
    )

    # Banner trạng thái realtime
    job_key_live, is_active_live = get_current_job_state()
    if not st.session_state.headcode_val.strip():
        st.info("📷 Quét QR hoặc nhập tay Headcode")
    elif not st.session_state.nguoibao_val.strip():
        st.info("👤 Gõ tên người vận hành để xác định trạng thái")
    elif is_active_live:
        job_info = st.session_state.active_jobs[job_key_live]
        st.warning(f"🔄 **{st.session_state.nguoibao_val}** đang làm từ **{job_info['gio_bat_dau']}** → Xác nhận **HOÀN THÀNH**")
    else:
        st.info(f"🚀 **{st.session_state.nguoibao_val}** chưa bắt đầu → Xác nhận **BẮT ĐẦU**")

    mode_label = "🏁 HOÀN THÀNH" if is_active_live else "▶️ BẮT ĐẦU"

    # ── Headcode NGOÀI form để on_change trigger lookup realtime ──
    _hc_key = f"_headcode_{st.session_state.form_key}"

    def on_headcode_change():
        new_hc = st.session_state[_hc_key].strip()
        st.session_state.headcode_val = new_hc
        st.session_state.qr_detected  = new_hc
        if new_hc:
            # ✅ Lookup NGAY TRONG on_change — không cần rerun thêm lần nào
            # Cache dict → tra cứu < 1ms, hoàn toàn an toàn khi gọi trong callback
            result = lookup_in_cache(new_hc)
            st.session_state.lookup_headcode = new_hc
            st.session_state.lookup_result   = result
        else:
            st.session_state.lookup_headcode = ""
            st.session_state.lookup_result   = None

    st.text_input(
        "Headcode *",
        value=st.session_state.headcode_val,
        key=_hc_key,
        on_change=on_headcode_change,
        placeholder="Quét QR hoặc nhập tay...",
    )

    # Fallback: nếu headcode_val có giá trị nhưng chưa lookup (VD: prefill từ danh sách)
    hc_live = st.session_state.headcode_val.strip()
    if hc_live and hc_live != st.session_state.lookup_headcode:
        result = lookup_in_cache(hc_live)
        st.session_state.lookup_headcode = hc_live
        st.session_state.lookup_result   = result

    with st.form(key=f"main_form_{st.session_state.form_key}", clear_on_submit=False):
        # Headcode chỉ hiển thị readonly trong form để truyền vào submit
        headcode = st.session_state.headcode_val.strip()
        soluong = st.number_input(
            "Số lượng",
            min_value=0.000,
            value=st.session_state.soluong_val,
            step=0.001,
            format="%.3f",
            key=f"soluong_{st.session_state.form_key}"
        )
        submit = st.form_submit_button(
            label=f"💾 XÁC NHẬN — {mode_label}",
            use_container_width=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # =====================================================
    # XỬ LÝ SUBMIT
    # =====================================================
    if submit:
        nguoibao = st.session_state.nguoibao_val.strip()
        congdoan  = st.session_state.congdoan_val

        # ✅ Chặn double-submit: nếu cùng key trong vòng 5 giây → bỏ qua
        _submit_key = f"{headcode}|{congdoan}|{nguoibao}"
        _now = time.time()
        _is_dup = (
            _submit_key == st.session_state.last_submit_key and
            (_now - st.session_state.last_submit_time) < 5.0
        )
        if not _is_dup:
            st.session_state.last_submit_key  = _submit_key
            st.session_state.last_submit_time = _now

        if _is_dup:
            st.warning("⚠️ Thao tác vừa được ghi nhận, vui lòng chờ...")
        elif not headcode:
            st.error("Vui lòng quét hoặc điền Headcode.")
        elif not nguoibao:
            st.error("Vui lòng điền Người vận hành.")
        elif headcode.strip() != st.session_state.lookup_headcode:
            # ✅ Headcode trong form khác với headcode đã lookup → không hợp lệ
            st.error("❌ Headcode không khớp với mã đã kiểm tra. Vui lòng quét lại.")
            st.session_state.qr_detected     = ""
            st.session_state.lookup_headcode = ""
            st.session_state.lookup_result   = None
            st.session_state.form_key += 1
            st.rerun()
        elif st.session_state.lookup_result is None or st.session_state.lookup_result.get("status") != "found":
            # ✅ Lookup chưa thành công → chặn
            st.error("❌ Mã chưa được xác nhận hợp lệ. Vui lòng quét lại.")
            st.session_state.qr_detected     = ""
            st.session_state.lookup_headcode = ""
            st.session_state.lookup_result   = None
            st.session_state.form_key += 1
            st.rerun()
        else:
            job_key   = f"{headcode}|{congdoan}|{nguoibao.lower()}"
            is_active = job_key in st.session_state.active_jobs


            if not is_active:
                # ---- BẮT ĐẦU ----
                # Kiểm tra trùng trong session trước khi gọi API
                payload = {
                    "action":     "start",
                    "headcode":   headcode,
                    "congdoan":   congdoan,
                    "soluong":    float(soluong),
                    "nguoibao":   nguoibao,
                }
                with st.spinner("Đang ghi nhận bắt đầu..."):
                    ok, resp_data = call_api(payload)

                if ok and resp_data.get("status") == "ok":
                    row_id      = resp_data.get("row_id", "")
                    gio_bat_dau = resp_data.get("gio_bat_dau", "")
                    st.session_state.active_jobs[job_key] = {
                        "headcode":    headcode,
                        "congdoan":    congdoan,
                        "nguoibao":    nguoibao,
                        "soluong":     float(soluong),
                        "gio_bat_dau": gio_bat_dau,
                        "row_id":      row_id,
                    }
                    st.session_state.last_action     = {"type": "start", "headcode": headcode, "congdoan": congdoan}
                    st.session_state.qr_detected     = ""
                    st.session_state.headcode_val    = ""
                    st.session_state.lookup_headcode = ""
                    st.session_state.lookup_result   = None
                    st.session_state.soluong_val     = 1.000
                    st.session_state.form_key       += 1
                    st.rerun()
                elif resp_data.get("status") == "duplicate":
                    # Apps Script báo đã tồn tại → load lại danh sách
                    st.warning("⚠️ Mã này đã được ghi nhận bắt đầu trước đó. Đang đồng bộ lại...")
                    st.session_state.active_jobs  = fetch_active_jobs_from_sheet()
                    st.session_state.form_key    += 1
                    st.rerun()
                else:
                    st.error(f"Lỗi: {resp_data.get('message', 'Không rõ')}")

            else:
                # ---- HOÀN THÀNH ----
                job_info = st.session_state.active_jobs[job_key]
                payload  = {
                    "action":         "finish",
                    "headcode":       headcode,
                    "congdoan":       congdoan,
                    "soluong":        float(soluong),
                    "nguoibao":       nguoibao,
                    "gio_bat_dau":    job_info["gio_bat_dau"],
                    "gio_hoan_thanh": datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M:%S"),
                    "row_id":         job_info.get("row_id", ""),
                }
                with st.spinner("Đang cập nhật hoàn thành..."):
                    ok, resp_data = call_api(payload)

                if ok and resp_data.get("status") == "ok":
                    del st.session_state.active_jobs[job_key]
                    st.session_state.last_action     = {"type": "finish", "headcode": headcode, "congdoan": congdoan}
                    st.session_state.qr_detected     = ""
                    st.session_state.headcode_val    = ""
                    st.session_state.lookup_headcode = ""
                    st.session_state.lookup_result   = None
                    st.session_state.soluong_val     = 1.000
                    st.session_state.form_key       += 1
                    st.rerun()
                else:
                    st.error(f"Lỗi: {resp_data.get('message', 'Không rõ')}")

# ─────────────────────────────────────────────────
# CỘT PHẢI — DANH SÁCH ĐANG XỬ LÝ
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
            # Xóa cache Streamlit → lần lookup tiếp sẽ load lại từ Sheet
            fetch_init_data.clear()
            st.session_state.lookup_headcode = ""
            st.session_state.lookup_result   = None
            st.success("✅ Đã xóa cache, dữ liệu sẽ được tải lại!")
            st.rerun()

    # Hiển thị thời gian cache DATA
    init_info = fetch_init_data()
    loaded_at = init_info["loaded_at"] if init_info else None
    if loaded_at:
        st.markdown(
            f'<div style="font-size:0.72rem; color:#64748b; text-align:center; margin-bottom:8px;">'
            f'🗄️ Dữ liệu DATA: <b style="color:#94a3b8">{loaded_at}</b>'
            f' &nbsp;|&nbsp; Tự làm mới sau 24h</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="card"><div class="card-title">⚡ Đang xử lý</div>', unsafe_allow_html=True)

    active_jobs = st.session_state.active_jobs
    if not active_jobs:
        st.markdown('<p style="color:#64748b; font-size:0.85rem; font-family:IBM Plex Mono,monospace;">— Chưa có công việc nào đang chạy —</p>', unsafe_allow_html=True)
    else:
        for jk, job in list(active_jobs.items()):
            # Mỗi job card: thông tin + nút Hoàn thành inline
            c_info, c_btn = st.columns([3, 1])
            with c_info:
                st.markdown(f"""
                <div class="job-row">
                    <div class="job-headcode">{job['headcode']}</div>
                    <div class="job-meta">{job['congdoan']}</div>
                    <div class="job-meta">👤 {job['nguoibao']} &nbsp;|&nbsp; 📦 {job.get('soluong', 0):.3f}</div>
                    <div class="job-meta" style="color:#64748b; font-size:0.72rem;">🕐 {job['gio_bat_dau']}</div>
                </div>
                """, unsafe_allow_html=True)
            with c_btn:
                # Nút bấm trực tiếp → prefill form bên trái rồi rerun
                btn_key = f"finish_btn_{jk}"
                if st.button("✅ Xong", key=btn_key, use_container_width=True):
                    st.session_state.prefill_headcode = job["headcode"]
                    st.session_state.prefill_nguoibao = job["nguoibao"]
                    st.session_state.prefill_congdoan = job["congdoan"]
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <div class="card-title">📖 Hướng dẫn</div>
        <div style="font-size:0.82rem; color:#94a3b8; line-height:1.8;">
            <b style="color:#f59e0b">Lần quét 1</b> → <span style="color:#4ade80">BẮT ĐẦU</span><br/>
            <b style="color:#818cf8">Lần quét 2</b> → <span style="color:#818cf8">HOÀN THÀNH</span><br/>
            <b style="color:#00e5a0">Nút ✅ Xong</b> → Chọn nhanh từ danh sách<br/><br/>
            <span style="color:#64748b">⚠ Danh sách tự khôi phục khi mở lại app</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
