import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz # Required for timezone handling
import os
import textwrap

# --- Constants ---
USERS_FILE = "users.json"
REQUESTS_FILE = "requests.json"
HISTORY_FILE = "history.json"

# --- Custom CSS for Toss-Inspired Design ---
def local_css():
    st.markdown("""
    <style>
        /* Global Font & Colors - Toss Style */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        :root {
            --toss-blue: #3182f6;
            --toss-blue-hover: #1b64da;
            --toss-gray-50: #f9fafb;
            --toss-gray-100: #f2f4f6;
            --toss-gray-200: #e5e8eb;
            --toss-gray-300: #d1d6db;
            --toss-gray-400: #b0b8c1;
            --toss-gray-900: #191f28;
            --toss-green: #0bc471;
            --toss-orange: #ff6f0f;
            --toss-red: #f04452;
            --toss-purple: #8b5cf6;
        }
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            -webkit-font-smoothing: antialiased;
            color: var(--toss-gray-900);
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main Container */
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 0 !important;
        }
        
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1200px !important;
        }
        
        /* Action Cards - Toss Style */
        .action-card {
            background: white;
            border-radius: 24px;
            padding: 40px 32px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            border: 2px solid transparent;
        }
        
        .action-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
            border-color: var(--toss-blue);
        }
        
        .action-card-icon {
            font-size: 3rem;
            margin-bottom: 16px;
            display: block;
        }
        
        .action-card-title {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--toss-gray-900);
            margin-bottom: 8px;
        }
        
        .action-card-desc {
            font-size: 1rem;
            color: var(--toss-gray-400);
            line-height: 1.5;
        }
        
        /* Admin Link */
        .admin-link {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
        }
        
        /* Headers */
        h1 {
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
            color: var(--toss-gray-900) !important;
            text-align: center !important;
            margin-bottom: 0.5rem !important;
        }
        
        .subtitle {
            text-align: center;
            color: var(--toss-gray-900);
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }
        
        /* Buttons - Toss Style */
        .stButton > button {
            border-radius: 12px;
            font-weight: 600;
            font-size: 16px;
            border: none;
            padding: 14px 28px;
            transition: all 0.2s ease;
            letter-spacing: -0.01em;
            width: 100%;
        }
        
        .stButton > button[kind="primary"] {
            background-color: var(--toss-blue);
            color: white;
            border: none;
        }
        
        .stButton > button[kind="primary"]:hover {
            background-color: var(--toss-blue-hover);
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(49, 130, 246, 0.4);
        }
        
        .stButton > button[kind="secondary"] {
            background-color: var(--toss-gray-100);
            color: var(--toss-gray-900);
            border: none;
        }
        
        /* Forms */
        .stTextInput > div > div,
        .stSelectbox > div > div,
        .stTextArea > div > div {
            border-radius: 12px;
            border: 2px solid var(--toss-gray-200);
            background-color: white;
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div:focus-within,
        .stSelectbox > div > div:focus-within,
        .stTextArea > div > div:focus-within {
            border-color: var(--toss-blue);
            box-shadow: 0 0 0 3px rgba(49, 130, 246, 0.1);
        }
        
        /* Tabs - Clean Style */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: var(--toss-gray-100);
            border-radius: 12px;
            padding: 6px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 44px;
            background-color: transparent;
            border-radius: 8px;
            color: var(--toss-gray-900);
            font-weight: 600;
            font-size: 15px;
            padding: 0 20px;
            transition: all 0.2s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: white !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
        
        /* Success/Warning/Error */
        .stSuccess {
            background-color: rgba(11, 196, 113, 0.1);
            border-left: 4px solid var(--toss-green);
            border-radius: 12px;
            padding: 16px;
        }
        
        .stWarning {
            background-color: rgba(255, 111, 15, 0.1);
            border-left: 4px solid var(--toss-orange);
            border-radius: 12px;
            padding: 16px;
        }
        
        .stError {
            background-color: rgba(240, 68, 82, 0.1);
            border-left: 4px solid var(--toss-red);
            border-radius: 12px;
            padding: 16px;
        }
        
        .stInfo {
            background-color: rgba(49, 130, 246, 0.1);
            border-left: 4px solid var(--toss-blue);
            border-radius: 12px;
            padding: 16px;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: white;
            border-radius: 12px;
            border: 2px solid var(--toss-gray-200);
            font-weight: 600;
        }
        
        /* Modal/Container Cards */
        .element-container {
            background-color: white;
            border-radius: 16px;
            padding: 24px;
        }
    </style>
    "guests": [],
    "sante_opt_out": False
})

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

# Date Check
if requests_data["target_date"] != str(target_date):
    requests_data = {
        "target_date": str(target_date),
        "applicants": [],
        "guests": [],
        "sante_opt_out": False
    }
    save_json(REQUESTS_FILE, requests_data)



# ============================================
# MAIN PAGE
# ============================================
if st.session_state.page == "main":
    # Header
    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    day_of_week = day_names[target_date.weekday()]
    
    st.title("플랩하우스 주차")
    st.markdown(f'<p class="subtitle">{target_date} ({day_of_week}) 주차 신청 중입니다.</p>', unsafe_allow_html=True)
    
    # ============================================
    # 3 ACTION CARDS - BUTTONS AS CARDS
    # ============================================
    
    # Inject CSS for Card Buttons (Secondary Buttons on Main Page)
    # Dynamic Colors based on State
    # Staff Card: Blue if form is open
    staff_bg = "var(--toss-blue)" if st.session_state.show_staff_form else "white"
    staff_text = "white" if st.session_state.show_staff_form else "var(--toss-gray-900)"
    staff_border = "transparent"
    
    # Guest Card: Blue if form is open
    guest_bg = "var(--toss-blue)" if st.session_state.show_guest_form else "white"
    guest_text = "white" if st.session_state.show_guest_form else "var(--toss-gray-900)"
    guest_border = "transparent"
    
    # Sante Card: Blue if 'Do' (opt_out=False), Red if 'Don't' (opt_out=True)
    if requests_data["sante_opt_out"]:
        # Don't (Opt-out = True) -> Red
        sante_bg = "var(--toss-red)"
        sante_text = "white"
        sante_border = "transparent"
    else:
        # Do (Opt-out = False) -> Blue
        sante_bg = "var(--toss-blue)"
        sante_text = "white"
        sante_border = "transparent"
    
    st.markdown(f"""
    <style>
    /* Target ALL Secondary Buttons on Main Page (The 3 Cards) */
    .stButton > button[kind="secondary"] {{
        background-color: white;
        border: 2px solid transparent;
        border-radius: 24px;
        height: 180px !important;
        white-space: pre; /* Force no wrapping for the title */
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 0 10px; /* Reduced padding to fit long text */
    }}
    
    .stButton > button[kind="secondary"]:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        border-color: var(--toss-blue);
        background-color: white;
        color: inherit;
    }}
    
    /* Inner Paragraph Styling - Base style for description (2nd line) */
    /* The first line is overridden by ::first-line below */
    
    /* First Line Styling (Title) - Larger and Bolder */
    .stButton > button[kind="secondary"] p::first-line {{
        font-size: 22px;
        font-weight: 800;
        line-height: 2.0;
    }}
    
    /* Reset font size for subsequent lines (Description) */
    .stButton > button[kind="secondary"] p {{
        font-size: 13px !important; /* Reduced size */
        font-weight: 400 !important; /* Normal weight */
        color: #191f28 !important; /* Black color */
        line-height: 1.4 !important;
        display: block !important;
        width: 100% !important;
        margin: 0 !important;
    }}
    
    /* Center Align Metrics */
    div[data-testid="stMetric"] {{
        text-align: center;
        justify-content: center;
    }}
    
    div[data-testid="stMetricLabel"] {{
        justify-content: center;
    }}
    
    div[data-testid="stMetricValue"] {{
        justify-content: center;
    }}
    
    /* Column-specific overrides for Colors */
    /* Staff Card (Column 1) */
    div[data-testid="column"]:nth-of-type(1) .stButton > button[kind="secondary"] {{
        background-color: {staff_bg} !important;
        color: {staff_text} !important;
        border-color: {staff_border} !important;
    }}
    
    /* Guest Card (Column 2) */
    div[data-testid="column"]:nth-of-type(2) .stButton > button[kind="secondary"] {{
        background-color: {guest_bg} !important;
        color: {guest_text} !important;
        border-color: {guest_border} !important;
    }}
    
    /* Sante Card (Column 3) */
    div[data-testid="column"]:nth-of-type(3) .stButton > button[kind="secondary"] {{
        background-color: {sante_bg} !important;
        color: {sante_text} !important;
        border-color: {sante_border} !important;
    }}
    
    /* Hover overrides for colored states */
    div[data-testid="column"]:nth-of-type(1) .stButton > button[kind="secondary"]:hover {{
        background-color: {staff_bg} !important;
        color: {staff_text} !important;
        opacity: 0.9;
    }}
    div[data-testid="column"]:nth-of-type(2) .stButton > button[kind="secondary"]:hover {{
        background-color: {guest_bg} !important;
        color: {guest_text} !important;
        opacity: 0.9;
    }}
    div[data-testid="column"]:nth-of-type(3) .stButton > button[kind="secondary"]:hover {{
        background-color: {sante_bg} !important;
        color: {sante_text} !important;
        opacity: 0.9;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Create 3 columns
    card_col1, card_col2, card_col3 = st.columns(3)
    
    # Card 1: Staff Application
    with card_col1:
        btn_text = "내일 주차 신청\n\n리서처 주차 신청을 진행합니다"
        if st.button(btn_text, key="card_staff", use_container_width=True, type="secondary"):
            st.session_state.show_staff_form = not st.session_state.show_staff_form
            st.session_state.show_guest_form = False
            st.rerun()
    
    # Card 2: Guest Application
    with card_col2:
        btn_text = "내일 외부인 주차 신청\n\n방문 손님의 주차를 등록합니다"
        if st.button(btn_text, key="card_guest", use_container_width=True, type="secondary"):
            st.session_state.show_guest_form = not st.session_state.show_guest_form
            st.session_state.show_staff_form = False
            st.rerun()
    
    # Card 3: Sante Option
    with card_col3:
        current_sante = requests_data["sante_opt_out"]
        sante_title = "상떼 주차 함" if not current_sante else "상떼 주차 안 함"
        sante_desc = "타워 2대 사용 가능" if not current_sante else "타워 3대 사용 가능"
        
        btn_text = f"{sante_title}\n\n{sante_desc}"
        
        if st.button(btn_text, key="card_sante", use_container_width=True, type="secondary"):
            requests_data["sante_opt_out"] = not current_sante
            save_json(REQUESTS_FILE, requests_data)
            st.rerun()
    
    # Forms appear right after the cards (before status)
    
    # Staff Form (if active)
    if st.session_state.show_staff_form:
        with st.container():
            st.markdown("### 직원 주차 신청")
            
            if not users:
                st.error("등록된 직원이 없습니다. 관리자 페이지에서 직원을 먼저 등록해주세요.")
            else:
                user_map = {f"{u['name']} ({u['car_type']})": u['name'] for u in users}
                user_options = ["선택해주세요"] + list(user_map.keys())
                
                selected_option = st.selectbox("이름 선택", user_options, key="staff_selector")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("신청하기", type="primary", use_container_width=True):
                        if selected_option == "선택해주세요":
                            st.error("이름을 선택해주세요.")
                        else:
                            name = user_map[selected_option]
                            if any(a["name"] == name for a in requests_data["applicants"]):
                                st.error("이미 신청되었습니다.")
                            else:
                                requests_data["applicants"].append({
                                    "name": name,
                                    "timestamp": datetime.now().isoformat()
                                })
                                save_json(REQUESTS_FILE, requests_data)
                                st.success(f"✅ {name}님의 주차 신청이 완료되었습니다!")
                                st.session_state.show_staff_form = False
                                st.rerun()
                
                with col2:
                    if st.button("취소", use_container_width=True, type="primary"):
                        st.session_state.show_staff_form = False
                        st.rerun()
    
    # Guest Form (if active)
    if st.session_state.show_guest_form:
        with st.container():
            st.markdown("### 외부인 주차 신청")
            
            g_car = st.radio("차종", ["SEDAN", "SUV"], horizontal=True, key="guest_car_type")
            
            if g_car == "SUV":
                st.caption("ℹ️ SUV는 타워 주차가 불가능합니다.")
                valid_locs = ["관리실(ADMIN)"]
            else:
                valid_locs = ["관리실(ADMIN)", "타워(TOWER)", "상관없음(ANY)"]
            
            g_loc = st.radio("주차 희망 위치", valid_locs, horizontal=True)
            
            col1, col2 = st.columns(2)
            g_name = col1.text_input("손님 성함/정보 (필수)")
            g_researcher = col2.text_input("등록 리서처 (필수)")
            
            g_reason = st.text_input("방문 목적 (필수)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("등록하기", type="primary", use_container_width=True):
                    if not g_name or not g_researcher or not g_reason:
                        st.error("모든 필수 정보를 입력해주세요.")
                    else:
                        new_guest = {
                            "name": g_name,
                            "car_type": g_car,
                            "location": g_loc,
                            "reason": g_reason,
                            "researcher": g_researcher,
                            "timestamp": datetime.now().isoformat()
                        }
                        requests_data["guests"].append(new_guest)
                        save_json(REQUESTS_FILE, requests_data)
                        st.success(f"✅ {g_name}님의 외부인 주차가 등록되었습니다!")
                        st.session_state.show_guest_form = False
                        st.rerun()
            
            with col2:
                if st.button("취소", use_container_width=True, type="primary"):
                    st.session_state.show_guest_form = False
                    st.rerun()
    
    # Status Summary - Below the forms
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
        if st.button("⚙️ 관리화면", type="primary", use_container_width=True):
            st.session_state.page = "admin"
            st.rerun()

# ============================================
# ADMIN PAGE
# ============================================

else:
    # Back Button (Top Right)
    # Back Button (Top Right)
    col_spacer, col_back = st.columns([6, 1.5]) # Adjusted for button width
    with col_back:
        if st.button("🏠 메인으로", type="secondary", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()

    st.title("⚙️ 관리자 페이지")
    
    # Test Mode Toggle
    test_mode = st.toggle("🧪 테스트 모드 (시간 제한 무시)", value=False)
    if test_mode:
        st.info("테스트 모드가 켜졌습니다. 모든 기능을 언제든 사용할 수 있습니다.")
    
    st.divider()
    
    # Tabs for Admin Functions
    tab1, tab2, tab3, tab4 = st.tabs(["📊 배정 결과", "👥 직원 관리", "📜 히스토리", "🗑️ 데이터 관리"])
    
    # ============================================
    # TAB 1: Allocation Results
    # ============================================
    with tab1:
        st.markdown("### 배정 결과")
        
        today_str = str(datetime.now().date())
        history_today = next((h for h in history if h["date"] == today_str), None)
        
        if history_today:
            st.success(f"✅ {today_str} 배정 결과가 확정되었습니다.")
            
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
                st.markdown(f"#### 🏢 관리실 ({admin_occupied}/{admin_capacity})")
                for item in admin_list:
                    st.success(f"**{item}**", icon="✅")
            with c2:
                st.markdown(f"#### 🅿️ 타워 ({tower_occupied}/{tower_capacity})")
                for item in tower_list:
                    st.info(f"**{item}**", icon="🅿️")
            with c3:
                wait_count = len(wait_list)
                st.markdown(f"#### ⏳ 대기 ({wait_count})")
                for item in wait_list:
                    st.warning(f"**{item}**", icon="⏳")
            
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
            
            st.markdown("#### 📤 슬랙 메시지 (복사용)")
            st.code(slack_msg, language="markdown")
                    
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
                
                st.success("✅ 배정이 완료되었습니다!")
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
        with st.expander("➕ 새 직원 추가"):
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
                        st.success(f"✅ {new_name}님이 추가되었습니다!")
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
                                st.success(f"✅ {edit_name}님의 정보가 수정되고 관련 기록이 업데이트되었습니다!")
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
                    
                    if col6.button("✏️", key=f"edit_btn_{idx}"):
                        st.session_state[f"editing_user_{idx}"] = True
                        st.rerun()
                        
                    if col7.button("🗑️", key=f"del_user_{idx}"):
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
        if st.button("➕ 수동 배정 추가"):
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
                    if st.form_submit_button("💾 저장", type="primary"):
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
                            st.success(f"✅ {date_str} 배정이 추가되었습니다!")
                            st.rerun()
                
                with col_cancel:
                    if st.form_submit_button("❌ 취소"):
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
                if st.button("🔍 필터 적용"):
                    st.session_state["filter_applied"] = True
                    st.session_state["filter_start"] = str(start_date)
                    st.session_state["filter_end"] = str(end_date)
                    st.rerun()
            
            if st.session_state.get("filter_applied", False):
                if st.button("❌ 필터 해제"):
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
                            if st.button("✏️ 수정", key=f"edit_hist_{h['date']}", use_container_width=True):
                                st.session_state[f"editing_hist_{h['date']}"] = True
                                st.rerun()
                        with col_del:
                            if st.button("🗑️ 삭제", key=f"del_hist_{h['date']}", use_container_width=True):
                                st.session_state[f"confirm_del_hist_{h['date']}"] = True
                                st.rerun()
                        
                        # Delete confirmation
                        if st.session_state.get(f"confirm_del_hist_{h['date']}", False):
                            st.warning(f"⚠️ {h['date']} 배정을 삭제하시겠습니까?")
                            col_yes, col_no = st.columns(2)
                            with col_yes:
                                if st.button("✅ 예", key=f"confirm_yes_{h['date']}"):
                                    history.remove(h)
                                    save_json(HISTORY_FILE, history)
                                    st.session_state[f"confirm_del_hist_{h['date']}"] = False
                                    st.success("✅ 삭제되었습니다!")
                                    st.rerun()
                            with col_no:
                                if st.button("❌ 아니오", key=f"confirm_no_{h['date']}"):
                                    st.session_state[f"confirm_del_hist_{h['date']}"] = False
                                    st.rerun()
                        
                        # Edit form with Multiselect
                        if st.session_state.get(f"editing_hist_{h['date']}", False):
                            with st.form(f"edit_hist_form_{h['date']}"):
                                st.markdown("##### 배정 수정")
                                
                                # Create staff options list
                                staff_options = [f"{u['name']} ({u['car_type']})" for u in users]
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.markdown("**🏢 관리실**")
                                    edit_admin = st.multiselect("관리실", staff_options, default=h["admin"], key=f"edit_admin_{h['date']}")
                                
                                with col2:
                                    st.markdown("**🅿️ 타워**")
                                    edit_tower = st.multiselect("타워", staff_options, default=h["tower"], key=f"edit_tower_{h['date']}")
                                
                                with col3:
                                    st.markdown("**⏳ 대기**")
                                    edit_wait = st.multiselect("대기", staff_options, default=h["wait"], key=f"edit_wait_{h['date']}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 저장", type="primary"):
                                        h["admin"] = edit_admin
                                        h["tower"] = edit_tower
                                        h["wait"] = edit_wait
                                        save_json(HISTORY_FILE, history)
                                        st.session_state[f"editing_hist_{h['date']}"] = False
                                        st.success("✅ 저장되었습니다!")
                                        st.rerun()
                                with col_cancel:
                                    if st.form_submit_button("❌ 취소"):
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
