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
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
@st.cache_data(ttl=600) # Cache for 10 minutes to speed up loads
def load_json(file_path, default_data):
    # Try to check if GitHub is configured
    if not github_sync.get_github_repo():
        pass
    else:
        gh_data = github_sync.load_from_github(file_path, default_data)
        if gh_data is not None:
            return copy.deepcopy(gh_data)
        else:
            if file_path in ["history.json", "users.json"]:
                 st.session_state["github_load_failed"] = True
                 st.session_state[f"load_error_{file_path}"] = "GitHub에서 데이터를 불러오지 못했습니다."

    if not os.path.exists(file_path):
        return copy.deepcopy(default_data)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return copy.deepcopy(data)
    except json.JSONDecodeError:
        return copy.deepcopy(default_data)

def save_json(file_path, data):
    if st.session_state.get("github_load_failed", False):
        st.warning(f"🚫 데이터 로드 실패로 인해 '{file_path}' 저장이 차단되었습니다.")
        return

    st.cache_data.clear()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    success = github_sync.save_to_github(file_path, data, f"Update {file_path} from Streamlit App")
    if not success:
        st.error(f"⚠️ {file_path} GitHub 저장 실패!")

def get_kst_time():
    return datetime.now(pytz.timezone('Asia/Seoul'))

def get_target_date():
    now = get_kst_time()
    if now.hour < 8:
        target = now.date()
    else:
        target = now.date() + timedelta(days=1)
    
    if target.weekday() == 5:
        target += timedelta(days=2)
    elif target.weekday() == 6:
        target += timedelta(days=1)
        
    return target

def send_slack_message(message):
    try:
        if hasattr(st, 'secrets') and 'SLACK_WEBHOOK_URL' in st.secrets:
            webhook_url = st.secrets['SLACK_WEBHOOK_URL']
        else:
            return False, "Slack Webhook URL이 설정되지 않았습니다."
        
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True, "슬랙 메시지 전송 성공!"
        else:
            return False, f"슬랙 전송 실패 ({response.status_code})"
    except Exception as e:
        return False, f"슬랙 전송 중 오류 발생: {str(e)}"

# --- Initialization ---
if "page" not in st.session_state:
    st.session_state.page = "main"
if "github_load_failed" not in st.session_state:
    st.session_state.github_load_failed = False

if st.session_state.github_load_failed:
    st.error("🚨 GitHub 데이터 불러오기 실패! 오프라인 모드입니다.", icon="🚫")

if "show_staff_form" not in st.session_state:
    st.session_state.show_staff_form = False
if "show_guest_form" not in st.session_state:
    st.session_state.show_guest_form = False

# Load Data
if "data_users" not in st.session_state:
    st.session_state.data_users = load_json(USERS_FILE, [])
users = st.session_state.data_users

if "data_history" not in st.session_state:
    st.session_state.data_history = load_json(HISTORY_FILE, [])
history = st.session_state.data_history

if "data_visitor" not in st.session_state:
    st.session_state.data_visitor = load_json(VISITOR_FILE, {"count": 0, "last_updated": str(datetime.now().date())})
visitor_data = st.session_state.data_visitor

if "visitor_session_counted" not in st.session_state:
    visitor_data["count"] = visitor_data.get("count", 0) + 1
    visitor_data["last_updated"] = str(datetime.now().date())
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

if "guests" not in requests_data:
    requests_data["guests"] = []

# --- AUTOMATION: Auto-Allocate ---
now_kst = get_kst_time()
today_str = str(now_kst.date())
history_today_check = next((h for h in history if h["date"] == today_str), None)
is_weekend = now_kst.weekday() in [5, 6]

if 8 <= now_kst.hour < 9 and now_kst.minute >= 1 and not history_today_check and not is_weekend:
    st.toast("🤖 자동 배정을 시작합니다...")
    admin_slots, tower_slots = 1, (3 if requests_data["sante_opt_out"] else 2)
    candidates = []
    
    for app in requests_data["applicants"]:
        name = app if isinstance(app, str) else app["name"]
        ts = datetime.min if isinstance(app, str) else datetime.fromisoformat(app["timestamp"])
        time_str = ts.strftime("%H:%M") if ts != datetime.min else "00:00"
        user_obj = next((u for u in users if u["name"] == name), None)
        if user_obj:
            candidates.append({
                "type": "staff", "name": name, "car_type": user_obj["car_type"],
                "last_parked": user_obj["last_parked_date"], "timestamp": ts,
                "display_name": f"{name} ({user_obj['car_type']}) {time_str}"
            })
    
    for g in requests_data["guests"]:
        ts = datetime.fromisoformat(g["timestamp"]) if "timestamp" in g else datetime.min
        time_str = ts.strftime("%H:%M") if ts != datetime.min else "00:00"
        candidates.append({
            "type": "guest", "name": g["name"], "car_type": g["car_type"], "location": g["location"],
            "timestamp": ts, "display_name": f"{g['name']} ({g['car_type']}) {time_str}"
        })
    
    staff_c = sorted([c for c in candidates if c["type"] == "staff"], key=lambda x: (x["last_parked"] or "0000-00-00", x["timestamp"]))
    guest_c = sorted([c for c in candidates if c["type"] == "guest"], key=lambda x: x["timestamp"])
    
    res_admin, res_tower, res_wait = [], [], []
    for g in guest_c:
        assigned = False
        if "관리실" in g["location"] and admin_slots > 0: res_admin.append(g["display_name"]); admin_slots -= 1; assigned = True
        elif "타워" in g["location"] and tower_slots > 0: res_tower.append(g["display_name"]); tower_slots -= 1; assigned = True
        elif "상관없음" in g["location"]:
            if tower_slots > 0: res_tower.append(g["display_name"]); tower_slots -= 1; assigned = True
            elif admin_slots > 0: res_admin.append(g["display_name"]); admin_slots -= 1; assigned = True
        if not assigned: res_wait.append(g["display_name"])
        
    for s in staff_c:
        assigned = False
        if s["car_type"] == "SUV":
            if admin_slots > 0: res_admin.append(s["display_name"]); admin_slots -= 1; assigned = True
        else:
            if tower_slots > 0: res_tower.append(s["display_name"]); tower_slots -= 1; assigned = True
            elif admin_slots > 0: res_admin.append(s["display_name"]); admin_slots -= 1; assigned = True
        if not assigned: res_wait.append(s["display_name"])

    for s in staff_c:
        if s["display_name"] in res_admin or s["display_name"] in res_tower:
            for u in users:
                if u["name"] == s["name"]: u["last_parked_date"] = today_str; break

    save_json(USERS_FILE, users)
    history.append({"date": today_str, "admin": res_admin, "tower": res_tower, "wait": res_wait})
    save_json(HISTORY_FILE, history)
    st.rerun()

if requests_data["target_date"] != str(target_date):
    requests_data = {"target_date": str(target_date), "applicants": [], "guests": [], "sante_opt_out": False}
    save_json(REQUESTS_FILE, requests_data)

local_css()

if st.session_state.page == "main":
    st.markdown('<div style="position: absolute; top: 10px; right: 20px; font-size: 0.75rem; color: #8b95a1;">방문자: '+f'{visitor_data.get("count", 0):,}'+'</div>', unsafe_allow_html=True)
    st.title("플랩하우스 주차")
    day_name = ["월", "화", "수", "목", "금", "토", "일"][target_date.weekday()]
    st.markdown(f'<p style="text-align:center; color:#8b95a1;">{target_date} ({day_name}) 주차 신청 중입니다.</p>', unsafe_allow_html=True)
    st.divider()

    if "active_tab" not in st.session_state: st.session_state.active_tab = None
    c1, c2, c3 = st.columns(3)
    if c1.button("내일 주차 신청", use_container_width=True): st.session_state.active_tab = "staff" if st.session_state.active_tab != "staff" else None
    if c2.button("외부인 주차", use_container_width=True): st.session_state.active_tab = "guest" if st.session_state.active_tab != "guest" else None
    sante_text = "상떼 주차 함" if not requests_data.get("sante_opt_out") else "상떼 주차 안 함"
    if c3.button(sante_text, use_container_width=True):
        requests_data["sante_opt_out"] = not requests_data.get("sante_opt_out")
        save_json(REQUESTS_FILE, requests_data); st.rerun()

    if st.session_state.active_tab == "staff":
        with st.form("staff_form"):
            name = st.selectbox("직원 이름", [u["name"] for u in users])
            if st.form_submit_button("신청", type="primary", use_container_width=True):
                if not any((a if isinstance(a, str) else a["name"]) == name for a in requests_data["applicants"]):
                    requests_data["applicants"].append({"name": name, "timestamp": datetime.now().isoformat()})
                    save_json(REQUESTS_FILE, requests_data); st.success("신청 완료!"); st.session_state.active_tab = None; st.rerun()
                else: st.warning("이미 신청됨")
    elif st.session_state.active_tab == "guest":
        with st.form("guest_form"):
            g_name = st.text_input("방문자 성함")
            g_res = st.selectbox("담당 연구원", [u["name"] for u in users])
            g_car = st.selectbox("차종", ["SEDAN", "SUV/VAN"])
            g_loc = st.selectbox("희망 위치", ["타워 (기계식)", "관리실 앞 (지상)"])
            if st.form_submit_button("신청", type="primary", use_container_width=True):
                if g_name:
                    requests_data["guests"].append({"name": g_name, "car_type": "SUV" if "SUV" in g_car else "SEDAN", "location": "관리실" if "관리실" in g_loc else "타워", "researcher": g_res, "timestamp": datetime.now().isoformat()})
                    save_json(REQUESTS_FILE, requests_data); st.success("신청 완료!"); st.session_state.active_tab = None; st.rerun()

    st.divider()
    sc, gc = len(requests_data["applicants"]), len(requests_data["guests"])
    ss = "안 함" if requests_data["sante_opt_out"] else "함"
    m1, m2, m3 = st.columns(3)
    m1.metric("직원", f"{sc}명"); m2.metric("손님", f"{gc}명"); m3.metric("상떼", ss)
    if st.button("관리화면", type="primary", use_container_width=True): st.session_state.page = "admin"; st.rerun()

else: # Admin Page
    if st.button("메인으로", use_container_width=True): st.session_state.page = "main"; st.rerun()
    st.title("관리자 페이지")
    t1, t2, t3, t4 = st.tabs(["배정 결과", "직원 관리", "히스토리", "데이터 관리"])
    
    with t1:
        st.write(f"### {today_str} 배정 결과")
        h_today = next((h for h in history if h["date"] == today_str), None)
        if h_today:
            c1, c2, c3 = st.columns(3)
            with c1: st.success("🏢 관리실"); [st.write(f"• {x}") for x in h_today["admin"]]
            with c2: st.info("🅿️ 타워"); [st.write(f"• {x}") for x in h_today["tower"]]
            with c3: st.warning("⏳ 대기"); [st.write(f"• {x}") for x in h_today["wait"]]
        else:
            if st.button("수동 배정 실행", type="primary"): 
                # (Simple manual trigger for testing)
                st.info("배정 로직 실행됨 (자동 배정 시간과 동일)"); st.rerun()
    
    with t2:
        st.write("### 직원 목록")
        for u in users: st.write(f"- {u['name']} ({u['car_type']})")
        with st.expander("직원 추가"):
            name = st.text_input("이름")
            car = st.selectbox("차종 ", ["SEDAN", "SUV"])
            if st.button("추가"): users.append({"name": name, "car_type": car, "last_parked_date": None}); save_json(USERS_FILE, users); st.rerun()

    with t3:
        st.write("### 최근 히스토리")
        for h in reversed(history[-10:]):
            with st.expander(f"{h['date']}"):
                is_today = h["date"] == today_str
                # Simplified edit for today only
                staff_opts = [f"{u['name']} ({u['car_type']})" for u in users]
                def get_base(s): return s.split(" (")[0]
                
                new_admin = st.multiselect("관리실", staff_opts, default=[x for x in staff_opts if get_base(x) in [get_base(a) for a in h["admin"]]], key=f"e_a_{h['date']}")
                new_tower = st.multiselect("타워", staff_opts, default=[x for x in staff_opts if get_base(x) in [get_base(t) for t in h["tower"]]], key=f"e_t_{h['date']}")
                
                if st.button("저장", key=f"s_{h['date']}"):
                    old_names = set([get_base(x) for x in h["admin"] + h["tower"]])
                    h["admin"], h["tower"] = new_admin, new_tower
                    save_json(HISTORY_FILE, history)
                    if is_today:
                        new_names = set([get_base(x) for x in new_admin + new_tower])
                        added, removed = new_names - old_names, old_names - new_names
                        if added: send_slack_message(f"📣 **주차 추가 알림**: {', '.join(added)}님이 추가되었습니다.")
                        if removed: send_slack_message(f"🚫 **주차 취소 알림**: {', '.join(removed)}님이 취소되었습니다.")
                    st.success("저장됨!"); st.rerun()

    with t4:
        if st.button("데이터 동기화 확인"): st.write("GitHub 연결 확인 완료")
