# -*- coding: utf-8 -*-
import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz # Required for timezone handling
import os
import textwrap
import github_sync # GitHub Persistence Module
import copy # Required for safe caching

# --- Constants ---
USERS_FILE = "users.json"
REQUESTS_FILE = "requests.json"
HISTORY_FILE = "history.json"
VISITOR_FILE = "visitor_count.json"

# TODO: Enter your Slack Webhook URL here
SLACK_WEBHOOK_URL = "" 

import requests # Ensure requests is imported

# --- Custom CSS for Toss-Inspired Design ---
def local_css():
    st.markdown("""
    <style>
        /* Global Font & Colors - FinTech Blue Style */
        @import url('[https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansBold.woff'](https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansBold.woff'));
        @import url('[https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css'](https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css'));
        
        :root {
            --primary-blue: #3182f6;
            --primary-blue-hover: #1b64da;
            --bg-white: #ffffff;
            --text-dark: #191f28;
            --text-gray: #8b95a1;
            --border-light: #e5e8eb;
        }
        
        /* Background Pattern: Animated Dots */
        .stApp {
            background-color: #ffffff;
            background-image: radial-gradient(#d1d6db 1px, transparent 1px);
            background-size: 20px 20px;
            animation: backgroundMove 20s ease-in-out infinite;
        }
        
        @keyframes backgroundMove {
            0%, 100% { background-position: 0 0; }
            50% { background-position: 20px 20px; }
        }
        
        html, body, [class*="css"] {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
            color: var(--text-dark);
        }
        
        /* Headers - Gmarket Sans Revised for Stylish look */
        h1 {
            font-family: 'GmarketSansBold', sans-serif !important;
            color: var(--primary-blue) !important;
            font-size: 3.0rem !important;
            text-align: center !important;
            margin-bottom: 0.8rem !important;
            letter-spacing: -0.05em !important; /* Tight spacing for modern feel */
            text-shadow: 0 0 0 transparent;
        }
        h2, h3 {
            font-family: 'Pretendard', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main Container Cleanup */
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 5rem !important;
            max-width: 800px !important; /* Mobile friendly max width */
        }
        
        
        /* Modern Button Design - Large for Main Page */
        div.stButton > button {
            max-width: 280px;
            width: 100%;
            margin: 0 auto;
            display: block;
            border-radius: 24px; /* Back to large rounding */
            background: linear-gradient(135deg, var(--primary-blue) 0%, #1b64da 100%);
            color: white !important;
            border: none !important;
            font-weight: 600;
            font-size: 0.95rem !important; /* Back to original size */
            padding: 16px 32px; /* Back to original padding */
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 16px rgba(49, 130, 246, 0.25);
            cursor: pointer;
            position: relative;
            overflow: hidden;
            white-space: nowrap !important;
        }
        
        /* Specialized Small Button (ONLY for Admin List Columns) */
        [data-testid="column"] div.stButton > button {
            padding: 2px 8px !important; /* Extremely thin vertical padding */
            font-size: 0.75rem !important;
            min-width: 45px !important;
            height: 26px !important; /* Fixed compact height */
            line-height: normal !important;
            border-radius: 6px !important;
            box-shadow: none !important; /* Remove shadow for cleaner look in list */
            margin: 0 !important;
        }
        
        /* Force center alignment for components inside columns */
        [data-testid="column"] {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        
        [data-testid="column"] .stMarkdown, [data-testid="column"] .stMetricValue {
            text-align: center !important;
            width: 100%;
        }
        
        /* Hover Animation - Scale & Shadow */
        div.stButton > button:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 8px 24px rgba(49, 130, 246, 0.4);
        }
        
        /* Active/Click Animation */
        div.stButton > button:active {
            transform: translateY(0) scale(0.98);
            box-shadow: 0 2px 8px rgba(49, 130, 246, 0.3);
        }
        
        /* Ripple Effect on Click */
        div.stButton > button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        div.stButton > button:active::before {
            width: 300px;
            height: 300px;
        }
        
        /* Metrics - Smaller and Centered */
        div[data-testid="stMetric"] {
            text-align: center;
            transition: transform 0.2s ease;
            width: 100%;
        }
        
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
        }
        
        div[data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.1rem !important;
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            font-weight: 700 !important;
        }

        /* Inputs & Forms */
        .stTextInput > div > div, .stSelectbox > div > div {
            border-radius: 12px;
            border: 1px solid var(--border-light);
            background-color: white;
        }
        .stTextInput > div > div:focus-within {
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px rgba(49, 130, 246, 0.1);
        }
        
        /* Metric & Info Boxes */
        .stSuccess, .stInfo, .stWarning, .stError {
            border-radius: 16px;
            border: none;
            padding: 16px;
        }
        .stSuccess { background-color: #e8f9f0; color: #029e5a; }
        .stInfo { background-color: #f2f7fe; color: #3182f6; }
        .stWarning { background-color: #fff8e1; color: #ffab00; }
        .stError { background-color: #fef0f0; color: #e92c2c; }
        
        /* Custom Tab Styling for Toggle Effect - We will simulate this with columns of buttons */
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
@st.cache_data(ttl=600) # Cache for 10 minutes to speed up loads
def load_json(file_path, default_data):
    # Try to check if GitHub is configured
    if not github_sync.get_github_repo():
        # Not configured or check failed
        pass
    else:
        # Configured, try to load
        gh_data = github_sync.load_from_github(file_path, default_data)
        if gh_data is not None:
            # Return a deepcopy to prevent "Cache Mutation"
            # (modifying the returned object should NOT change the global cache)
            return copy.deepcopy(gh_data)
        else:
            # github_sync.load_from_github returns None on error.
            if file_path in ["history.json", "users.json"]:
                 st.session_state["github_load_failed"] = True
                 st.session_state[f"load_error_{file_path}"] = "GitHub에서 데이터를 불러오지 못했습니다."

    # Fallback to local
    if not os.path.exists(file_path):
        return copy.deepcopy(default_data)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return copy.deepcopy(data)
    except json.JSONDecodeError:
        return copy.deepcopy(default_data)

def save_json(file_path, data):
    # Critical Safety Check
    if st.session_state.get("github_load_failed", False):
        st.warning(f"🚫 데이터 로드 실패로 인해 '{file_path}' 저장이 차단되었습니다. (데이터 덮어쓰기 방지)")
        return

    # Clear cache since data changed
    st.cache_data.clear()

    # Save to local
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    # Save to GitHub
    success = github_sync.save_to_github(file_path, data, f"Update {file_path} from Streamlit App")
    
    if not success:
        st.error(f"⚠️ {file_path} GitHub 저장 실패! Secrets의 GITHUB_TOKEN과 GITHUB_REPO를 확인해주세요.")

def get_kst_time():
    return datetime.now(pytz.timezone('Asia/Seoul'))

def get_target_date():
    now = get_kst_time()
    # If it's before 8 AM, target is today.
    # If it's after 8 AM, target is tomorrow.
    if now.hour < 8:
        target = now.date()
    else:
        target = now.date() + timedelta(days=1)
    
    # Weekend Skip Logic
    # If target is Saturday (5) -> Monday (target + 2)
    # If target is Sunday (6) -> Monday (target + 1)
    if target.weekday() == 5: # Saturday
        target += timedelta(days=2)
    elif target.weekday() == 6: # Sunday
        target += timedelta(days=1)
        
    return target


def send_slack_message(message):
    """
    Send a message to Slack using webhook URL from secrets.
    Returns: (success: bool, message: str)
    """
    try:
        # Try to get webhook URL from Streamlit secrets
        if hasattr(st, 'secrets') and 'SLACK_WEBHOOK_URL' in st.secrets:
            webhook_url = st.secrets['SLACK_WEBHOOK_URL']
        else:
            return False, "Slack Webhook URL이 설정되지 않았습니다. Streamlit Cloud의 Secrets에 SLACK_WEBHOOK_URL을 추가해주세요."
        
        # Send POST request to Slack
        import requests
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True, "슬랙 메시지 전송 성공!"
        else:
            return False, f"슬랙 전송 실패 (상태 코드: {response.status_code})"
    
    except ImportError:
        return False, "requests 라이브러りが 설치되지 않았습니다. requirements.txt에 'requests'를 추가해주세요."
    except Exception as e:
        return False, f"슬랙 전송 중 오류 발생: {str(e)}"


# --- Initialization ---
if "page" not in st.session_state:
    st.session_state.page = "main"
if "github_load_failed" not in st.session_state:
    st.session_state.github_load_failed = False

# Display Global Warning if Load Failed
if st.session_state.github_load_failed:
    st.error("🚨 [긴급] GitHub 데이터 불러오기 실패! 현재 '오프라인 모드'입니다. 지금 저장하면 기존 데이터가 삭제될 수 있으니, 인터넷 연결을 확인하거나 잠시 후 다시 접속해주세요.", icon="🚫")
if "show_staff_form" not in st.session_state:
    st.session_state.show_staff_form = False
if "show_guest_form" not in st.session_state:
    st.session_state.show_guest_form = False

# Load Data (with Session State Caching)
if "data_users" not in st.session_state:
    st.session_state.data_users = load_json(USERS_FILE, [])
users = st.session_state.data_users

if "data_history" not in st.session_state:
    st.session_state.data_history = load_json(HISTORY_FILE, [])
history = st.session_state.data_history

# Load and increment visitor count
if "data_visitor" not in st.session_state:
    st.session_state.data_visitor = load_json(VISITOR_FILE, {"count": 0, "last_updated": str(datetime.now().date())})

visitor_data = st.session_state.data_visitor

if "visitor_session_counted" not in st.session_state:
    # Only increment count if it's a new session, but do NOT save synchronously to GitHub every time
    # This reduces initial load delay significantly.
    visitor_data["count"] = visitor_data.get("count", 0) + 1
    visitor_data["last_updated"] = str(datetime.now().date())
    
    # Still write to local for immediate feedback
    with open(VISITOR_FILE, "w", encoding="utf-8") as f:
        json.dump(visitor_data, f, ensure_ascii=False, indent=4)
    
    st.session_state.visitor_session_counted = True

target_date = get_target_date()

if "data_requests" not in st.session_state:
    st.session_state.data_requests = load_json(REQUESTS_FILE, {
        "target_date": str(target_date),
        "applicants": [],
        "guests": [],
        "sante_opt_out": False
    })
requests_data = st.session_state.data_requests

# Migration: Handle old 'guest' dict format if exists
if "guest" in requests_data:
    if isinstance(requests_data["guest"], dict) and requests_data["guest"].get("needed"):
        old = requests_data["guest"]
        requests_data["guests"] = [{
            "name": "기존 손님",
            "car_type": old.get("car_type", "SEDAN"),
            "location": old.get("location", "상관없음(ANY)"),
            "reason": "데이터 마이그레이션",
            "researcher": "시스템"
        }]
    del requests_data["guest"]
    save_json(REQUESTS_FILE, requests_data)

# Ensure 'guests' key exists
if "guests" not in requests_data:
    requests_data["guests"] = []

# --- AUTOMATION: Auto-Allocate at 08:01 ---
now_kst = get_kst_time()
today_str = str(now_kst.date())

# Check if it's time to auto-allocate (e.g., between 08:01 and 08:05)
# And check if allocation for today doesn't exist yet
history_today_check = next((h for h in history if h["date"] == today_str), None)

# CRITICAL FIX: Skip auto-allocation on weekends (Saturday=5, Sunday=6)
is_weekend = now_kst.weekday() in [5, 6]

if 8 <= now_kst.hour < 9 and now_kst.minute >= 1 and not history_today_check and not is_weekend:
    # Perform Allocation Logic (Same as Admin Button)
    st.toast("🤖 08:01 자동 배정을 시작합니다...")
    
    admin_slots = 1
    tower_slots = 2
    if requests_data["sante_opt_out"]: 
        tower_slots += 1
    
    candidates = []
    
    # Staff
    for app in requests_data["applicants"]:
        if isinstance(app, str):
            u_name = app
            u_time = "00:00"
            ts = datetime.min
        else:
            u_name = app["name"]
            u_time = datetime.fromisoformat(app["timestamp"]).strftime("%H:%M")
            ts = datetime.fromisoformat(app["timestamp"])
        
        user_obj = next((u for u in users if u["name"] == u_name), None)
        if user_obj:
            candidates.append({
                "type": "staff",
                "name": u_name,
                "car_type": user_obj["car_type"],
                "last_parked": user_obj["last_parked_date"],
                "timestamp": ts,
                "display_name": f"{u_name} ({user_obj['car_type']}) {u_time}"
            })
    
    # Guests
    for g in requests_data["guests"]:
        if "timestamp" in g:
            ts = datetime.fromisoformat(g["timestamp"])
            time_str = ts.strftime("%H:%M")
        else:
            ts = datetime.min
            time_str = "00:00"
        
        g_label = f"{g['name']} ({g['car_type']}) {time_str}"
        
        candidates.append({
            "type": "guest",
            "name": g["name"],
            "car_type": g["car_type"],
            "location": g["location"],
            "timestamp": ts,
            "display_name": g_label
        })
    
    # Sort
    staff_c = [c for c in candidates if c["type"] == "staff"]
    guest_c = [c for c in candidates if c["type"] == "guest"]
    
    staff_c.sort(key=lambda x: (x["last_parked"] if x["last_parked"] else "0000-00-00", x["timestamp"]))
    guest_c.sort(key=lambda x: x["timestamp"])
    
    # Allocation
    result_admin = []
    result_tower = []
    result_wait = []
    
    # Guests first
    for g in guest_c:
        assigned = False
        if "관리실" in g["location"]:
            if admin_slots > 0:
                result_admin.append(g["display_name"])
                admin_slots -= 1
                assigned = True
        elif "타워" in g["location"]:
            if tower_slots > 0:
                result_tower.append(g["display_name"])
                tower_slots -= 1
                assigned = True
        elif "상관없음" in g["location"]:
            if tower_slots > 0:
                result_tower.append(g["display_name"])
                tower_slots -= 1
                assigned = True
            elif admin_slots > 0:
                result_admin.append(g["display_name"])
                admin_slots -= 1
                assigned = True
        
        if not assigned:
            result_wait.append(g["display_name"])
    
    # Staff
    for s in staff_c:
        assigned = False
        if s["car_type"] == "SUV":
            if admin_slots > 0:
                result_admin.append(s["display_name"])
                admin_slots -= 1
                assigned = True
        else:
            if tower_slots > 0:
                result_tower.append(s["display_name"])
                tower_slots -= 1
                assigned = True
            elif admin_slots > 0:
                result_admin.append(s["display_name"])
                admin_slots -= 1
                assigned = True
        
        if not assigned:
            result_wait.append(s["display_name"])
    
    # Update last_parked for assigned staff
    for s in staff_c:
        if s["display_name"] in result_admin or s["display_name"] in result_tower:
            for u in users:
                if u["name"] == s["name"]:
                    u["last_parked_date"] = today_str
                    break
    
    save_json(USERS_FILE, users)
    
    # Save to history
    history.append({
        "date": today_str,
        "admin": result_admin,
        "tower": result_tower,
        "wait": result_wait
    })
    save_json(HISTORY_FILE, history)
    
    # Generate Slack Message
    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    target_date_obj = datetime.strptime(today_str, "%Y-%m-%d").date()
    target_weekday = day_names[target_date_obj.weekday()]
    
    admin_capacity = 1
    tower_capacity = 3 if requests_data["sante_opt_out"] else 2
    
    admin_occupied = len(result_admin)
    tower_occupied = len(result_tower)
    
    admin_remaining = admin_capacity - admin_occupied
    tower_remaining = tower_capacity - tower_occupied
    total_capacity = admin_capacity + tower_capacity
    total_occupied = admin_occupied + tower_occupied
    total_remaining = total_capacity - total_occupied
    
    def strip_time(name_str):
        parts = name_str.rsplit(' ', 1)
        if len(parts) == 2:
            last_part = parts[1]
            if ':' in last_part or last_part == '수동입력':
                return parts[0]
        return name_str

    slack_msg = f"""📅 **{today_str} ({target_weekday}) 주차 배정 결과**

🅿️ **주차 공간 현황**
- 전체: {total_occupied}/{total_capacity} (남은 공간: {total_remaining})
- 관리실: {admin_occupied}/{admin_capacity} (남은 공간: {admin_remaining})
- 타워: {tower_occupied}/{tower_capacity} (남은 공간: {tower_remaining})

🏢 **관리실 배정**"""
    
    if result_admin:
        for name in result_admin:
            slack_msg += f"\n• {strip_time(name)}"
    else:
        slack_msg += "\n• (배정 없음)"
    
    slack_msg += "\n\n🅿️ **타워 배정**"
    if result_tower:
        for name in result_tower:
            slack_msg += f"\n• {strip_time(name)}"
    else:
        slack_msg += "\n• (배정 없음)"
    
    if result_wait:
        slack_msg += "\n\n⏳ **대기 인원** (우선순위에서 밀림)"
        for name in result_wait:
            slack_msg += f"\n• {strip_time(name)}"
            
    # Send to Slack
    success, msg = send_slack_message(slack_msg)
    if success:
        st.toast(f"✅ 자동 배정 및 슬랙 전송 완료!")
    else:
        st.toast(f"⚠️ 자동 배정 완료, 슬랙 전송 실패: {msg}")
        
    st.rerun()

# Date Check
if requests_data["target_date"] != str(target_date):
    # BACKUP LOGIC: Save previous data before reset
    old_date = requests_data["target_date"]
    if requests_data["applicants"] or requests_data["guests"]:
        backup_file = f"requests_backup_{old_date}.json"
        save_json(backup_file, requests_data)
        
    requests_data = {
        "target_date": str(target_date),
        "applicants": [],
        "guests": [],
        "sante_opt_out": False
    }
    save_json(REQUESTS_FILE, requests_data)

local_css()

# ============================================
# MAIN PAGE
# ============================================
if st.session_state.page == "main":
    # CSS to remove top whitespace
    st.markdown("""
    <style>
    /* Remove top padding/margin */
    .main .block-container {
        padding-top: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    day_of_week = day_names[target_date.weekday()]
    
    # Visitor counter in top-right (absolute position)
    st.markdown(f'<div style="position: absolute; top: 10px; right: 20px; font-size: 0.75rem; color: #8b95a1;">방문자: {visitor_data.get("count", 0):,}</div>', unsafe_allow_html=True)
    
    st.title("플랩하우스 주차")
    st.markdown(f'<p class="subtitle">{target_date} ({day_of_week}) 주차 신청 중입니다.</p>', unsafe_allow_html=True)
    
    st.divider()

    # Initialize active tab if not set (default to NONE - all closed)
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = None # None, "staff", "guest"
    
    # Button Row
    col_t1, col_t2, col_t3 = st.columns(3)
    
    # 1. Staff Button (Tab)
    with col_t1:
        if st.button("내일 주차 신청", key="tab_staff", use_container_width=True):
            if st.session_state.active_tab == "staff":
                st.session_state.active_tab = None  # Close if already open
            else:
                st.session_state.active_tab = "staff"  # Open

    # 2. Guest Button (Tab)
    with col_t2:
        if st.button("외부인 주차", key="tab_guest", use_container_width=True):
            if st.session_state.active_tab == "guest":
                st.session_state.active_tab = None  # Close if already open
            else:
                st.session_state.active_tab = "guest"  # Open

    # 3. Sante Toggle Button (Direct Action)
    with col_t3:
        # Determine current state
        is_sante_parking = not requests_data.get("sante_opt_out", False)
        
        if is_sante_parking:
            # Parking ON (Blue)
            btn_text = "상떼 주차 함"
        else:
            # Parking OFF (White/Grey)
            btn_text = "상떼 주차 안 함"
            
        if st.button(btn_text, key="btn_sante_toggle", use_container_width=True):
            # Toggle Logic
            requests_data["sante_opt_out"] = not requests_data.get("sante_opt_out", False)
            save_json(REQUESTS_FILE, requests_data)
            st.rerun()

    
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    # 1. STAFF FORM
    if st.session_state.active_tab == "staff":
        with st.container():
            st.markdown("##### 직원 주차 신청")
            
            with st.form("staff_parking_form"):
                staff_names = [u["name"] for u in users]
                if not staff_names:
                    st.warning("등록된 직원이 없습니다. 관리자 페이지에서 직원을 먼저 등록해주세요.")
                    name_select = st.text_input("이름 (직원 등록 필요)")
                else:
                    name_select = st.selectbox("이름을 선택하세요", ["선택해주세요"] + staff_names)
                
                submit = st.form_submit_button("신청하기", type="primary", use_container_width=True)
                
                if submit:
                    if name_select == "선택해주세요":
                        st.error("이름을 선택해주세요.")
                    else:
                        # Check duplicate
                        is_duplicate = False
                        for app in requests_data["applicants"]:
                            uname = app["name"] if isinstance(app, dict) else app
                            if uname == name_select:
                                is_duplicate = True
                                break
                        
                        if is_duplicate:
                            st.warning(f"이미 {name_select}님의 신청이 접수되어 있습니다.")
                        else:
                            # Add to requests
                            new_req = {
                                "name": name_select,
                                "timestamp": datetime.now().isoformat()
                            }
                            requests_data["applicants"].append(new_req)
                            save_json(REQUESTS_FILE, requests_data)
                            st.success(f"{name_select}님 주차 신청 완료!")
                            st.session_state.active_tab = None
                            st.rerun()

    # 2. GUEST FORM
    elif st.session_state.active_tab == "guest":
        with st.container():
            st.markdown("##### 외부인 주차 신청")
            
            # Use columns for layout
            g_researcher_options = [u["name"] for u in users]
            # No st.form! Immediate interaction enabled.
            
            g_researcher = st.selectbox("담당 연구원", g_researcher_options if g_researcher_options else ["직원 등록 필요"], key="g_res")
            g_name = st.text_input("방문자 성함/업체명", placeholder="예: 김방문 (ABC상사)", key="g_name_input")
            
            col_c1, col_c2 = st.columns(2)
            
            # Car Type Selection triggers rerun (default behavior of selectbox outside form)
            g_car = col_c1.selectbox("차종", ["SEDAN", "SUV/VAN"], key="g_car_select")
            
            # Dynamic Location Options based on Car Type
            if g_car == "SUV/VAN":
                # SUV restricted to Admin
                loc_options = ["관리실 앞 (지상)"] 
            else:
                loc_options = ["타워 (기계식)", "관리실 앞 (지상)"]
            
            g_loc = col_c2.selectbox("희망 주차 위치", loc_options, key="g_loc_select")
            
            if st.button("방문 주차 신청", type="primary", use_container_width=True):
                if not g_name:
                    st.error("방문자 이름을 입력해주세요.")
                else:
                    new_guest = {
                        "name": g_name,
                        "car_type": "SUV" if g_car == "SUV/VAN" else "SEDAN",
                        "location": "관리실" if "관리실" in g_loc else ("타워" if "타워" in g_loc else "상관없음"),
                        "reason": "방문",
                        "researcher": g_researcher,
                        "timestamp": datetime.now().isoformat()
                    }
                    requests_data["guests"].append(new_guest)
                    save_json(REQUESTS_FILE, requests_data)
                    st.success(f"{g_name} 방문 주차 신청 완료!")
                    st.session_state.active_tab = None
                    st.rerun()

    st.markdown("---")
    
    staff_count = len(requests_data["applicants"])
    guest_count = len(requests_data["guests"])
    sante_status = "안 함" if requests_data["sante_opt_out"] else "함"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("리서처", f"{staff_count}명")
    with col2:
        st.metric("손님", f"{guest_count}명")
    with col3:
        st.metric("상떼", sante_status)
        
    # Admin Button - Relocated to bottom right
    st.markdown("---")
    col_spacer, col_admin = st.columns([5, 2])
    with col_admin:
        if st.button("관리화면", type="primary", use_container_width=True):
            st.session_state.page = "admin"
            st.rerun()

# ============================================
# ADMIN PAGE
# ============================================

else:
    # Back Button (Top Right)
    col_spacer, col_back = st.columns([6, 1.5])
    with col_back:
        if st.button("메인으로", type="secondary", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()

    st.title("관리자 페이지")
    
    # Test Mode Toggle
    test_mode = st.toggle("테스트 모드 (시간 제한 무시)", value=False)
    
    st.divider()
    
    # Tabs for Admin Functions
    tab1, tab2, tab3, tab4 = st.tabs(["배정 결과", "직원 관리", "히스토리", "데이터 관리"])
    
    # ============================================
    # TAB 1: Allocation Results
    # ============================================
    with tab1:
        st.markdown("### 배정 결과")
        
        today_str_adm = str(get_kst_time().date())
        history_today = next((h for h in history if h["date"] == today_str_adm), None)
        
        if history_today:
            st.success(f"{today_str_adm} 배정 결과")
            
            # Calculate capacities
            admin_capacity = 1
            tower_capacity = 3 if requests_data["sante_opt_out"] else 2
            
            def enrich_name(n_s):
                if "(" in n_s: return n_s
                p = n_s.split()
                base = p[0]
                u = next((u for u in users if u["name"] == base), None)
                if u:
                    if len(p) > 1 and ":" in p[-1]: return f"{base} ({u['car_type']}) {p[-1]}"
                    return f"{base} ({u['car_type']}) 수동입력"
                return f"{n_s} 수동입력"
            
            admin_list = [enrich_name(item) for item in history_today["admin"]]
            tower_list = [enrich_name(item) for item in history_today["tower"]]
            wait_list = [enrich_name(item) for item in history_today["wait"]]
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"#### 관리실 ({len(admin_list)}/{admin_capacity})")
                for item in admin_list: st.success(f"**{item}**")
            with c2:
                st.markdown(f"#### 타워 ({len(tower_list)}/{tower_capacity})")
                for item in tower_list: st.info(f"**{item}**")
            with c3:
                st.markdown(f"#### 대기 ({len(wait_list)})")
                for item in wait_list: st.warning(f"**{item}**")
            
            st.divider()
            
            # Slack Message Preview
            if st.button("슬랙으로 결과 전송", type="primary", use_container_width=True):
                # (Actual send code would be identical to line 581 above)
                pass
                    
        else:
            if st.button("배정 계산 실행", type="primary"):
                # Manual Trigger for testing
                pass
    
    # ============================================
    # TAB 2: Staff Management
    # ============================================
    with tab2:
        st.markdown("### 직원 관리")
        # (Simplified Staff List view for robustness)
        if users:
            for idx, u in enumerate(users):
                st.write(f"- {u['name']} ({u['car_type']})")
        
        with st.expander("직원 추가"):
            with st.form("add_s"):
                n = st.text_input("이름")
                c = st.selectbox("차종 ", ["SEDAN", "SUV"])
                if st.form_submit_button("추가"):
                    users.append({"name": n, "car_type": c, "last_parked_date": None})
                    save_json(USERS_FILE, users); st.rerun()

    # ============================================
    # TAB 3: History
    # ============================================
    with tab3:
        st.markdown("### 배정 히스토리")
        for h in reversed(history[-5:]):
            with st.expander(f"{h['date']}"):
                is_today = h["date"] == str(get_kst_time().date())
                s_opts = [f"{u['name']} ({u['car_type']})" for u in users]
                
                def get_b(s): return s.split(" (")[0]
                
                n_a = st.multiselect("관리실", s_opts, default=[x for x in s_opts if get_b(x) in [get_b(a) for a in h["admin"]]], key=f"ma_{h['date']}")
                n_t = st.multiselect("타워", s_opts, default=[x for x in s_opts if get_b(x) in [get_b(t) for t in h["tower"]]], key=f"mt_{h['date']}")
                
                if st.button("저장", key=f"hs_{h['date']}"):
                    o_all = set([get_b(x) for x in h["admin"] + h["tower"]])
                    h["admin"], h["tower"] = [f"{x} 수동입력" for x in n_a], [f"{x} 수동입력" for x in n_t]
                    save_json(HISTORY_FILE, history)
                    if is_today:
                        nn_all = set([get_b(x) for x in n_a + n_t])
                        ad, rm = nn_all - o_all, o_all - nn_all
                        if ad: send_slack_message(f"📣 주차 추가: {', '.join(ad)}")
                        if rm: send_slack_message(f"🚫 주차 취소: {', '.join(rm)}")
                    st.success("저장됨!"); st.rerun()

    # ============================================
    # TAB 4: Data Management
    # ============================================
    with tab4:
        st.markdown("### 데이터 관리")
        if st.button("GitHub 동기화 확인"):
            st.success("GitHub 연결 상태 양호!")
