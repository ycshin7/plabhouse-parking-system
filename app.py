# -*- coding: utf-8 -*-
import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz # Required for timezone handling
import os
import textwrap
import github_sync # GitHub Persistence Module

# --- Constants ---
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
        @import url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansBold.woff');
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        
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
        
        
        /* Modern Button Design - Compact & Animated */
        div.stButton > button {
            max-width: 280px;
            margin: 0 auto;
            display: block;
            border-radius: 24px;
            background: linear-gradient(135deg, var(--primary-blue) 0%, #1b64da 100%);
            color: white !important;
            border: none !important;
            font-weight: 600;
            font-size: 0.95rem !important;
            padding: 16px 32px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 16px rgba(49, 130, 246, 0.25);
            cursor: pointer;
            position: relative;
            overflow: hidden;
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
        }
        
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
        }
        
        div[data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
            justify-content: center;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
            justify-content: center;
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
def load_json(file_path, default_data):
    # Try to check if GitHub is configured
    if not github_sync.get_github_repo():
        # Not configured or check failed
        pass
    else:
        # Configured, try to load
        gh_data = github_sync.load_from_github(file_path, default_data)
        if gh_data is not None:
            return gh_data
        else:
            # Configured BUT returned None -> LOAD FAILURE (Network or Auth or Missing File)
            # If it's a missing file, it might be fine, but if it's network, it's bad.
            # github_sync.load_from_github returns None on error.
            # Ideally we want to panic here if it's a critical file like history.json
            if file_path in ["history.json", "users.json"]:
                 st.session_state["github_load_failed"] = True
                 st.session_state[f"load_error_{file_path}"] = "GitHub에서 데이터를 불러오지 못했습니다."

    # Fallback to local
    if not os.path.exists(file_path):
        return default_data
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default_data

def save_json(file_path, data):
    # Critical Safety Check
    if st.session_state.get("github_load_failed", False):
        st.warning(f"🚫 데이터 로드 실패로 인해 '{file_path}' 저장이 차단되었습니다. (데이터 덮어쓰기 방지)")
        return

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
        return False, "requests 라이브러리가 설치되지 않았습니다. requirements.txt에 'requests'를 추가해주세요."
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
    visitor_data["count"] = visitor_data.get("count", 0) + 1
    visitor_data["last_updated"] = str(datetime.now().date())
    save_json(VISITOR_FILE, visitor_data) # This will update st.session_state.data_visitor internally if I update save_json too?
    # Wait, save_json just saves to disk/github. It doesn't update session state ref if I pass the object.
    # Since visitor_data IS st.session_state.data_visitor (ref), modifying it updates session state. OK.
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

if 8 <= now_kst.hour < 9 and now_kst.minute >= 1 and not history_today_check:
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
• 전체: {total_occupied}/{total_capacity} (남은 공간: {total_remaining})
• 관리실: {admin_occupied}/{admin_capacity} (남은 공간: {admin_remaining})
• 타워: {tower_occupied}/{tower_capacity} (남은 공간: {tower_remaining})

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
# Date Check
if requests_data["target_date"] != str(target_date):
    # BACKUP LOGIC: Save previous data before reset
    old_date = requests_data["target_date"]
    if requests_data["applicants"] or requests_data["guests"]:
        backup_file = f"requests_backup_{old_date}.json"
        save_json(backup_file, requests_data)
        # Optional: We could also log this action
        
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

    
    # ============================================
    # 3 ACTION CARDS - BUTTONS AS CARDS
    # ============================================
    
    # Inject CSS for Card Buttons (Secondary Buttons on Main Page)
    # Dynamic Colors based on State
    # Staff Card: Blue if form is open
    # ============================================
    # 3-BUTTON TOGGLE MENU (Mobile Friendly)
    # ============================================
    
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
    
    # ============================================
    # INTERACTION AREA (Forms appear here)
    # ============================================
    
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
                            st.session_state.active_tab = None  # Close form after submit

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
                    st.session_state.active_tab = None  # Close form after submit

    # 3. SANTE ALERT TOGGLE
    elif st.session_state.active_tab == "sante":
        with st.container():
            st.markdown("##### 🔔 산테 알림 설정")
            
            # Current Status
            is_visiting = not requests_data.get("sante_opt_out", False) # Default False means Visiting? No.
            # Logic check: 'sante_opt_out': True means "User Opted Out of Sante", so Sante is NOT visiting?
            # Or "Opt Out of allocation"?
            # Let's trust the previous UI logic:
            # "sante_title = '상떼 주차 함' if not current_sante else '상떼 주차 안 함'"
            # current_sante = requests_data["sante_opt_out"]
            # If opt_out is False -> "상떼 주차 함" (Sante Visiting)
            # If opt_out is True -> "상떼 주차 안 함" (Sante Not Visiting)
            
            is_visiting = not requests_data.get("sante_opt_out", False)
            
            if is_visiting:
                st.success("⭕ **내일 산테 방문함** (타워 1자리 비움)")
                st.info("방문이 취소되었다면 아래 버튼을 눌러주세요.")
                if st.button("방문 취소 (OFF)", use_container_width=True):
                    requests_data["sante_opt_out"] = True
                    save_json(REQUESTS_FILE, requests_data)
                    st.rerun()
            else:
                st.warning("❌ **내일 산테 방문 안 함**")
                st.info("방문이 예정되어 있다면 아래 버튼을 눌러주세요.")
                if st.button("방문 설정 (ON)", type="primary", use_container_width=True):
                    requests_data["sante_opt_out"] = False
                    save_json(REQUESTS_FILE, requests_data)
                    st.rerun()

    st.markdown("---")
    
    staff_count = len(requests_data["applicants"])
    guest_count = len(requests_data["guests"])
    sante_status = "안 함" if requests_data["sante_opt_out"] else "함"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("리서처 신청 현황", f"{staff_count}명")
    with col2:
        st.metric("손님 신청 현황", f"{guest_count}명")
    with col3:
        st.metric("상떼 주차 여부", sante_status)
        
    # Admin Button - Relocated to bottom right
    st.markdown("---")
    col_spacer, col_admin = st.columns([5, 2]) # Adjusted ratio for wider button
    with col_admin:
        if st.button("관리화면", type="primary", use_container_width=True):
            st.session_state.page = "admin"
            st.rerun()

# ============================================
# ADMIN PAGE
# ============================================

else:
    # Back Button (Top Right)
    col_spacer, col_back = st.columns([6, 1.5]) # Adjusted for button width
    with col_back:
        if st.button("메인으로", type="secondary", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()

    st.title("관리자 페이지")
    
    # Test Mode Toggle
    test_mode = st.toggle("테스트 모드 (시간 제한 무시)", value=False)
    if test_mode:
        st.info("테스트 모드가 켜졌습니다. 모든 기능을 언제든 사용할 수 있습니다.")
    
    st.divider()
    
    # Determine which tab to select based on session state
    tab_names = ["배정 결과", "직원 관리", "히스토리", "데이터 관리"]
    default_tab = 0  # Default to first tab
    
    # Check if admin_tab is set in session state
    if "admin_tab" in st.session_state:
        if st.session_state.admin_tab == "히스토리":
            default_tab = 2
        # Clear the session state after using it
        del st.session_state.admin_tab
    
    # Tabs for Admin Functions
    tab1, tab2, tab3, tab4 = st.tabs(tab_names)
    
    # ============================================
    # TAB 1: Allocation Results
    # ============================================
    with tab1:
        st.markdown("### 배정 결과")
        
        today_str = str(get_kst_time().date())
        history_today = next((h for h in history if h["date"] == today_str), None)
        
        if history_today:
            st.success(f"{today_str} 배정 결과가 확정되었습니다.")
            
            # Calculate capacities
            admin_capacity = 1
            tower_capacity = 3 if requests_data["sante_opt_out"] else 2
            
            # Helper function to enrich name with car type
            def enrich_name(name_str):
                if "(" in name_str and ")" in name_str:
                    return name_str
                
                parts = name_str.split()
                base_name = parts[0] if parts else name_str
                
                user = next((u for u in users if u["name"] == base_name), None)
                if user:
                    car_type = user["car_type"]
                    if len(parts) > 1 and ":" in parts[-1]:
                        time_part = parts[-1]
                        return f"{base_name} ({car_type}) {time_part}"
                    else:
                        return f"{base_name} ({car_type}) 수동입력"
                
                if len(parts) > 1 and ":" in parts[-1]:
                    return name_str
                else:
                    return f"{name_str} 수동입력"
            
            admin_list = [enrich_name(item) for item in history_today["admin"]]
            tower_list = [enrich_name(item) for item in history_today["tower"]]
            wait_list = [enrich_name(item) for item in history_today["wait"]]
            
            admin_occupied = len(admin_list)
            tower_occupied = len(tower_list)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"#### 관리실 ({admin_occupied}/{admin_capacity})")
                for item in admin_list:
                    st.success(f"**{item}**")
            with c2:
                st.markdown(f"#### 타워 ({tower_occupied}/{tower_capacity})")
                for item in tower_list:
                    st.info(f"**{item}**")
            with c3:
                wait_count = len(wait_list)
                st.markdown(f"#### 대기 ({wait_count})")
                for item in wait_list:
                    st.warning(f"**{item}**")
            
            st.divider()
            
            # Slack Message
            day_names = ["월", "화", "수", "목", "금", "토", "일"]
            target_date_obj = datetime.strptime(today_str, "%Y-%m-%d").date()
            target_weekday = day_names[target_date_obj.weekday()]
            
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
• 전체: {total_occupied}/{total_capacity} (남은 공간: {total_remaining})
• 관리실: {admin_occupied}/{admin_capacity} (남은 공간: {admin_remaining})
• 타워: {tower_occupied}/{tower_capacity} (남은 공간: {tower_remaining})

🏢 **관리실 배정**"""
            
            if admin_list:
                for name in admin_list:
                    slack_msg += f"\n• {strip_time(name)}"
            else:
                slack_msg += "\n• (배정 없음)"
            
            slack_msg += "\n\n🅿️ **타워 배정**"
            if tower_list:
                for name in tower_list:
                    slack_msg += f"\n• {strip_time(name)}"
            else:
                slack_msg += "\n• (배정 없음)"
            
            if wait_list:
                slack_msg += "\n\n⏳ **대기 인원** (우선순위에서 밀림)"
                for name in wait_list:
                    slack_msg += f"\n• {strip_time(name)}"
            
            st.markdown("#### 슬랙 메시지 (복사용)")
            st.code(slack_msg, language="markdown")
            
            if st.button("슬랙으로 결과 전송", type="primary", use_container_width=True):
                success, msg = send_slack_message(slack_msg)
                if success:
                    st.success(f"{msg}")
                else:
                    st.error(f"❌ {msg}")
                    
        elif datetime.now().hour < 8 and not test_mode:
            st.info(f"오늘({today_str}) 배정 결과는 08:00에 공개됩니다.")
        else:
            if st.button("배정 계산 실행", type="primary"):
                # Allocation Logic
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
                
                st.success("배정이 완료되었습니다!")
                st.rerun()
    
    # ============================================
    # TAB 2: Staff Management
    # ============================================
    with tab2:
        # Header with Excel Button
        col_header, col_excel = st.columns([8, 2])
        with col_header:
            st.markdown("### 직원 관리")
        with col_excel:
            if st.button("📥 엑셀", use_container_width=True):
                # Create DataFrame for export
                export_data = []
                for u in users:
                    export_data.append({
                        "이름": u["name"],
                        "차종": u["car_type"],
                        "차 번호": u.get("car_number", ""),
                        "상세 차종": u.get("car_details", ""),
                        "마지막 주차일": u.get("last_parked_date", "")
                    })
                df = pd.DataFrame(export_data)
                
                # Save to Excel
                excel_file = "staff_list.xlsx"
                df.to_excel(excel_file, index=False)
                
                # Read file for download
                with open(excel_file, "rb") as f:
                    file_data = f.read()
                
                st.download_button(
                    label="다운로드",
                    data=file_data,
                    file_name="staff_list.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_btn"
                )
        
        # Add New Staff
        with st.expander("새 직원 추가"):
            with st.form("add_staff_form"):
                col1, col2 = st.columns(2)
                new_name = col1.text_input("이름")
                new_car = col2.selectbox("차종", ["SEDAN", "SUV"])
                
                col3, col4 = st.columns(2)
                new_car_num = col3.text_input("차 번호 (선택)")
                new_car_detail = col4.text_input("상세 차종 (선택)")
                
                if st.form_submit_button("추가", type="primary"):
                    if not new_name:
                        st.error("이름을 입력해주세요.")
                    elif any(u["name"] == new_name for u in users):
                        st.error("이미 등록된 이름입니다.")
                    else:
                        users.append({
                            "name": new_name,
                            "car_type": new_car,
                            "car_number": new_car_num,
                            "car_details": new_car_detail,
                            "last_parked_date": None
                        })
                        save_json(USERS_FILE, users)
                        st.success(f"{new_name}님이 추가되었습니다!")
                        st.rerun()
        
        st.divider()
        
        # Staff List (Table Format)
        if users:
            st.markdown("#### 등록된 직원")
            
            # Table Header
            st.markdown("""
            <div style="display: flex; font-weight: bold; color: #6b7684; margin-bottom: 8px; padding: 0 10px;">
                <div style="flex: 2;">이름</div>
                <div style="flex: 1;">차종</div>
                <div style="flex: 1.5;">차 번호</div>
                <div style="flex: 1.5;">상세 차종</div>
                <div style="flex: 2;">마지막 주차일</div>
                <div style="flex: 0.6;"></div>
                <div style="flex: 0.6;"></div>
            </div>
            <hr style='margin: 0 0 5px 0; border: 0; border-top: 2px solid #e8e8ed;'>
            """, unsafe_allow_html=True)
            
            for idx, u in enumerate(users):
                # Check if editing
                if st.session_state.get(f"editing_user_{idx}", False):
                    with st.form(f"edit_user_form_{idx}"):
                        c1, c2, c3, c4 = st.columns(4)
                        # Capture old values for cascade update
                        old_name = u["name"]
                        old_car = u["car_type"]
                        
                        edit_name = c1.text_input("이름", value=u["name"])
                        edit_car = c2.selectbox("차종", ["SEDAN", "SUV"], index=0 if u["car_type"]=="SEDAN" else 1)
                        edit_num = c3.text_input("차 번호", value=u.get("car_number", ""))
                        edit_detail = c4.text_input("상세 차종", value=u.get("car_details", ""))
                        
                        save_col, cancel_col = st.columns([1, 1])
                        if save_col.form_submit_button("💾 저장", type="primary"):
                            # Check duplicate name if changed
                            if edit_name != u["name"] and any(user["name"] == edit_name for user in users):
                                st.error("이미 존재하는 이름입니다.")
                            else:
                                u["name"] = edit_name
                                u["car_type"] = edit_car
                                u["car_number"] = edit_num
                                u["car_details"] = edit_detail
                                save_json(USERS_FILE, users)
                                
                                # Cascade updates to Requests and History
                                # 1. Update Requests
                                for app in requests_data["applicants"]:
                                    if isinstance(app, dict) and app["name"] == old_name:
                                        app["name"] = edit_name
                                save_json(REQUESTS_FILE, requests_data)
                                
                                # 2. Update History
                                # History entries are strings: "Name (CarType) Time" or "Name (CarType)"
                                # We need to replace "OldName (OldCar)" with "NewName (NewCar)"
                                # Robust match: Check if starts with "OldName (" to handle cases where OldCar might differ
                                
                                history_updated = False
                                for h in history:
                                    for key in ["admin", "tower", "wait"]:
                                        new_list = []
                                        for item in h[key]:
                                            # Match if item starts with "OldName (" or is exactly "OldName"
                                            # This ignores the old car type in history, forcing an update to the new car type
                                            if item == old_name or item.startswith(f"{old_name} ("):
                                                # Try to preserve the time part
                                                # Split by last closing parenthesis to separate Car info from Time
                                                parts = item.rsplit(')', 1)
                                                if len(parts) > 1:
                                                    # parts[0] is "Name (Car", parts[1] is " Time" or empty
                                                    time_part = parts[1]
                                                    new_item = f"{edit_name} ({edit_car}){time_part}"
                                                else:
                                                    # No closing paren found, just replace with new format
                                                    new_item = f"{edit_name} ({edit_car})"
                                                new_list.append(new_item)
                                            else:
                                                new_list.append(item)
                                        
                                        if h[key] != new_list:
                                            h[key] = new_list
                                            history_updated = True
                                
                                if history_updated:
                                    save_json(HISTORY_FILE, history)
                                
                                st.session_state[f"editing_user_{idx}"] = False
                                st.success(f"{edit_name}님의 정보가 수정되고 관련 기록이 업데이트되었습니다!")
                                st.rerun()
                        
                        if cancel_col.form_submit_button("❌ 취소"):
                            st.session_state[f"editing_user_{idx}"] = False
                            st.rerun()
                else:
                    # Display Row - Reduced spacing (padding)
                    # Adjusted column ratios to give more space to buttons
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1.5, 1.5, 2, 0.6, 0.6])
                    
                    col1.write(f"**{u['name']}**")
                    col2.write(u['car_type'])
                    col3.write(u.get('car_number', '-'))
                    col4.write(u.get('car_details', '-'))
                    # Calculate Last Parked Date dynamically from history
                    last_parked_date = "-"
                    # We iterate through history to find the latest date this user parked
                    # History is sorted by date usually, but let's be safe
                    user_dates = []
                    for h in history:
                        # Check if user is in admin or tower list
                        # History items are strings like "Name (Car) Time"
                        # We match by checking if user name is at the start
                        for item in h["admin"] + h["tower"]:
                            if item.startswith(u["name"]):
                                user_dates.append(h["date"])
                    
                    if user_dates:
                        last_parked_date = max(user_dates)
                    
                    col5.write(last_parked_date)
                    
                    if col6.button("수정", key=f"edit_btn_{idx}"):
                        st.session_state[f"editing_user_{idx}"] = True
                        st.rerun()
                        
                    if col7.button("삭제", key=f"del_user_{idx}"):
                        users.remove(u)
                        save_json(USERS_FILE, users)
                        st.rerun()
                    
                    # Reduced margin for separator
                    st.markdown("<hr style='margin: 4px 0; border: 0; border-top: 1px solid #e8e8ed;'>", unsafe_allow_html=True)
        else:
            st.info("등록된 직원이 없습니다.")
    
    # ============================================
    # TAB 3: History
    # ============================================
    with tab3:
        st.markdown("### 배정 히스토리")
        
        # Manual Entry Button
        if st.button("수동 배정 추가"):
            st.session_state["adding_manual_history"] = True
        
        # Manual Entry Form with Multiselect
        if st.session_state.get("adding_manual_history", False):
            with st.form("manual_history_form"):
                st.markdown("#### 수동 배정 추가")
                
                manual_date = st.date_input("날짜 선택", value=datetime.now().date())
                
                # Create staff options list
                staff_options = [f"{u['name']} ({u['car_type']})" for u in users]
                
                st.markdown("**배정 내역 선택** (등록된 직원 중 선택)")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**🏢 관리실**")
                    manual_admin = st.multiselect("관리실 배정", staff_options, key="manual_admin_select")
                
                with col2:
                    st.markdown("**🅿️ 타워**")
                    manual_tower = st.multiselect("타워 배정", staff_options, key="manual_tower_select")
                
                with col3:
                    st.markdown("**⏳ 대기**")
                    manual_wait = st.multiselect("대기 인원", staff_options, key="manual_wait_select")
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("저장", type="primary"):
                        date_str = str(manual_date)
                        
                        # Check if date already exists
                        existing_idx = next((i for i, h in enumerate(history) if h["date"] == date_str), None)
                        
                        if existing_idx is not None:
                            st.error(f"{date_str} 날짜의 배정이 이미 존재합니다. 기존 배정을 수정하거나 삭제해주세요.")
                        else:
                            new_entry = {
                                "date": date_str,
                                "admin": manual_admin,
                                "tower": manual_tower,
                                "wait": manual_wait
                            }
                            history.append(new_entry)
                            history.sort(key=lambda x: x["date"])
                            save_json(HISTORY_FILE, history)
                            st.session_state["adding_manual_history"] = False
                            st.success(f"{date_str} 배정이 추가되었습니다!")
                            st.rerun()
                
                with col_cancel:
                    if st.form_submit_button("취소"):
                        st.session_state["adding_manual_history"] = False
                        st.rerun()
        
        st.divider()
        
        # Date Filter
        if history:
            st.markdown("#### 날짜 필터")
            
            col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 1])
            
            with col_filter1:
                all_dates = sorted([datetime.strptime(h["date"], "%Y-%m-%d").date() for h in history], reverse=True)
                if all_dates:
                    start_date = st.date_input("시작 날짜", value=all_dates[-1])
            
            with col_filter2:
                if all_dates:
                    end_date = st.date_input("종료 날짜", value=all_dates[0])
            
            with col_filter3:
                if st.button("필터 적용"):
                    st.session_state["filter_applied"] = True
                    st.session_state["filter_start"] = str(start_date)
                    st.session_state["filter_end"] = str(end_date)
                    st.rerun()
            
            if st.session_state.get("filter_applied", False):
                if st.button("필터 해제"):
                    st.session_state["filter_applied"] = False
                    st.rerun()
            
            st.divider()
        
        # Display History
        if history:
            # Apply filter if set
            filtered_history = history
            if st.session_state.get("filter_applied", False):
                filter_start = st.session_state.get("filter_start")
                filter_end = st.session_state.get("filter_end")
                filtered_history = [h for h in history if filter_start <= h["date"] <= filter_end]
            
            if not filtered_history:
                st.info("선택한 기간에 배정 내역이 없습니다.")
            else:
                st.markdown(f"#### 배정 내역 ({len(filtered_history)}건)")
                
                for idx, h in enumerate(reversed(filtered_history)):
                    with st.expander(f"📅 {h['date']}", expanded=False):
                        # Edit/Delete buttons - HORIZONTAL
                        # Adjusted columns to give buttons enough width to not wrap
                        col_edit, col_del, col_spacer = st.columns([1.5, 1.5, 7])
                        with col_edit:
                            if st.button("수정", key=f"edit_hist_{h['date']}", use_container_width=True):
                                st.session_state[f"editing_hist_{h['date']}"] = True
                                st.rerun()
                        with col_del:
                            if st.button("삭제", key=f"del_hist_{h['date']}", use_container_width=True):
                                st.session_state[f"confirm_del_hist_{h['date']}"] = True
                                st.rerun()
                        
                        # Delete confirmation
                        if st.session_state.get(f"confirm_del_hist_{h['date']}", False):
                            st.warning(f"{h['date']} 배정을 삭제하시겠습니까?")
                            col_yes, col_no = st.columns(2)
                            with col_yes:
                                if st.button("예", key=f"confirm_yes_{h['date']}"):
                                    history.remove(h)
                                    save_json(HISTORY_FILE, history)
                                    st.session_state[f"confirm_del_hist_{h['date']}"] = False
                                    st.success("삭제되었습니다!")
                                    st.rerun()
                            with col_no:
                                if st.button("아니오", key=f"confirm_no_{h['date']}"):
                                    st.session_state[f"confirm_del_hist_{h['date']}"] = False
                                    st.rerun()
                        
                        # Edit form with Multiselect
                        if st.session_state.get(f"editing_hist_{h['date']}", False):
                            with st.form(f"edit_hist_form_{h['date']}"):
                                st.markdown("##### 배정 수정")
                                
                                # Create staff options list
                                staff_options = [f"{u['name']} ({u['car_type']})" for u in users]
                                
                                # Helper function to extract base name from history format
                                def extract_base_name(name_str):
                                    # Format: "Name (CarType) Time" or "Name (CarType) 수동입력"
                                    # Extract "Name (CarType)" part
                                    parts = name_str.rsplit(' ', 1)  # Split from right
                                    if len(parts) == 2:
                                        last_part = parts[1]
                                        if ':' in last_part or last_part == '수동입력':
                                            return parts[0]  # Return "Name (CarType)"
                                    return name_str  # Return as-is if no time found
                                
                                # Extract base names and filter valid options
                                admin_defaults = [extract_base_name(item) for item in h["admin"]]
                                admin_defaults = [item for item in admin_defaults if item in staff_options]
                                
                                tower_defaults = [extract_base_name(item) for item in h["tower"]]
                                tower_defaults = [item for item in tower_defaults if item in staff_options]
                                
                                wait_defaults = [extract_base_name(item) for item in h["wait"]]
                                wait_defaults = [item for item in wait_defaults if item in staff_options]
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.markdown("**🏢 관리실**")
                                    edit_admin = st.multiselect("관리실", staff_options, default=admin_defaults, key=f"edit_admin_{h['date']}", label_visibility="collapsed")
                                
                                with col2:
                                    st.markdown("**🅿️ 타워**")
                                    edit_tower = st.multiselect("타워", staff_options, default=tower_defaults, key=f"edit_tower_{h['date']}", label_visibility="collapsed")
                                
                                with col3:
                                    st.markdown("**⏳ 대기**")
                                    edit_wait = st.multiselect("대기", staff_options, default=wait_defaults, key=f"edit_wait_{h['date']}", label_visibility="collapsed")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    submit_save = st.form_submit_button("저장", type="primary", use_container_width=True)
                                with col_cancel:
                                    submit_cancel = st.form_submit_button("취소", use_container_width=True)
                                
                                # Handle form submission outside the columns
                                if submit_save:
                                    # Save with "Name (CarType) 수동입력" format for edited entries
                                    h["admin"] = [f"{item} 수동입력" for item in edit_admin]
                                    h["tower"] = [f"{item} 수동입력" for item in edit_tower]
                                    h["wait"] = [f"{item} 수동입력" for item in edit_wait]
                                    save_json(HISTORY_FILE, history)
                                    st.session_state[f"editing_hist_{h['date']}"] = False
                                    st.success("저장되었습니다!")
                                    st.rerun()
                                
                                if submit_cancel:
                                    st.session_state[f"editing_hist_{h['date']}"] = False
                                    st.rerun()
                        else:
                            # Display current allocation
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown("**🏢 관리실**")
                                for item in h["admin"]:
                                    st.write(f"• {item}")
                                if not h["admin"]:
                                    st.caption("(배정 없음)")
                            with col2:
                                st.markdown("**🅿️ 타워**")
                                for item in h["tower"]:
                                    st.write(f"• {item}")
                                if not h["tower"]:
                                    st.caption("(배정 없음)")
                            with col3:
                                st.markdown("**⏳ 대기**")
                                for item in h["wait"]:
                                    st.write(f"• {item}")
                                if not h["wait"]:
                                    st.caption("(대기 없음)")
        else:
            st.info("히스토리가 없습니다.")
    
    # ============================================
    # TAB 4: Data Management
    # ============================================
    with tab4:
        st.markdown("### 데이터 관리")
        
        st.markdown("### 데이터 저장 확인 (GitHub)")
        
        if st.button("GitHub 저장 상태 확인하기"):
            with st.spinner("GitHub와 통신 중입니다..."):
                try:
                    gh_history = github_sync.load_from_github(HISTORY_FILE, [])
                    if gh_history is None:
                        st.error("GitHub 연결 실패! 데이터가 저장되지 않았을 수 있습니다.")
                    else:
                        local_count = len(history)
                        gh_count = len(gh_history)
                        
                        if local_count == gh_count:
                            if local_count > 0 and history[-1] == gh_history[-1]:
                                st.success("GitHub와 동기화 완료! (데이터 일치)")
                            else:
                                st.warning("데이터 개수는 같지만 내용이 다를 수 있습니다.")
                        elif local_count > gh_count:
                            st.warning("로컬 데이터가 더 많습니다. (저장되지 않은 데이터 존재)")
                        else: # local_count < gh_count
                            st.warning(f"GitHub 데이터가 더 많습니다. (로컬 {local_count}건 vs GitHub {gh_count}건)")
                            st.write("방금 저장했다면 10초 뒤에 다시 눌러보세요.")
                except Exception as e:
                    st.error(f"확인 중 오류 발생: {e}")
        
        st.divider()

        st.warning("⚠️ 위험 구역")
        
        if st.button("🗑️ 오늘 신청 내역 초기화", type="secondary"):
            st.session_state["confirm_reset"] = True
        
        if st.session_state.get("confirm_reset", False):
            st.error("⚠️ 정말로 오늘의 신청 내역을 초기화하시겠습니까?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 예, 초기화합니다", type="primary"):
                    if os.path.exists(REQUESTS_FILE):
                        os.remove(REQUESTS_FILE)
                    st.session_state["confirm_reset"] = False
                    st.success("✅ 신청 내역이 초기화되었습니다!")
                    st.rerun()
            with col2:
                if st.button("❌ 아니오, 취소합니다"):
                    st.session_state["confirm_reset"] = False
                    st.rerun()
        
        st.divider()
        
        # Current Applications
        st.markdown("#### 현재 신청 현황")
        
        if requests_data["applicants"]:
            st.markdown("**직원 신청**")
            for app in requests_data["applicants"]:
                name = app["name"] if isinstance(app, dict) else app
                col1, col2 = st.columns([5, 1])
                col1.write(name)
                if col2.button("X", key=f"del_app_{name}"):
                    requests_data["applicants"].remove(app)
                    save_json(REQUESTS_FILE, requests_data)
                    st.rerun()
        
        if requests_data["guests"]:
            st.markdown("**손님 신청**")
            for i, g in enumerate(requests_data["guests"]):
                col1, col2 = st.columns([5, 1])
                col1.write(f"{g['name']} - {g['researcher']}")
                if col2.button("X", key=f"del_guest_{i}"):
                    requests_data["guests"].pop(i)
                    save_json(REQUESTS_FILE, requests_data)
                    st.rerun()
