#!/usr/bin/env python3
"""
Automated Parking Allocation Script
Runs daily via GitHub Actions to allocate parking and send Slack notification
"""

import json
import os
from datetime import datetime, timedelta
import pytz
import requests

# File paths (GitHub Actions runs from repo root)
USERS_FILE = "users.json"
REQUESTS_FILE = "requests.json"
HISTORY_FILE = "history.json"

def load_json(file_path, default_data):
    if not os.path.exists(file_path):
        return default_data
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default_data

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_kst_time():
    return datetime.now(pytz.timezone('Asia/Seoul'))

def get_target_date():
    now = get_kst_time()
    if now.hour < 8:
        target = now.date()
    else:
        target = now.date() + timedelta(days=1)
    
    # Weekend Skip Logic
    if target.weekday() == 5:  # Saturday
        target += timedelta(days=2)
    elif target.weekday() == 6:  # Sunday
        target += timedelta(days=1)
    
    return target

def send_slack_message(message):
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return False, "SLACK_WEBHOOK_URL not set in environment"
    
    try:
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True, "Slack message sent successfully"
        else:
            return False, f"Failed with status code: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    print("🚀 Starting automated parking allocation...")
    
    # Load data
    users = load_json(USERS_FILE, [])
    history = load_json(HISTORY_FILE, [])
    requests_data = load_json(REQUESTS_FILE, {
        "target_date": "",
        "applicants": [],
        "guests": [],
        "sante_opt_out": False
    })
    
    target_date = get_target_date()
    today_str = str(target_date)
    
    print(f"📅 Target date: {today_str}")
    
    # Check if already allocated
    history_today = next((h for h in history if h["date"] == today_str), None)
    if history_today:
        print(f"✅ Allocation for {today_str} already exists. Skipping.")
        return
    
    # Check if there are applicants
    if not requests_data.get("applicants") and not requests_data.get("guests"):
        print("ℹ️ No applicants found. Skipping allocation.")
        return
    
    print(f"👥 Found {len(requests_data.get('applicants', []))} staff applicants")
    print(f"🎫 Found {len(requests_data.get('guests', []))} guest applicants")
    
    # Allocation logic (simplified version)
    admin_slots = 1
    tower_slots = 3 if requests_data.get("sante_opt_out") else 2
    
    candidates = []
    
    # Collect staff candidates
    for app in requests_data.get("applicants", []):
        if isinstance(app, str):
            u_name = app
            ts = datetime.min
            u_time = "00:00"
        else:
            u_name = app["name"]
            ts = datetime.fromisoformat(app["timestamp"])
            u_time = ts.strftime("%H:%M")
        
        user_obj = next((u for u in users if u["name"] == u_name), None)
        if user_obj:
            candidates.append({
                "type": "staff",
                "name": u_name,
                "car_type": user_obj["car_type"],
                "last_parked": user_obj.get("last_parked_date", ""),
                "timestamp": ts,
                "display_name": f"{u_name} ({user_obj['car_type']}) {u_time}"
            })
    
    # Sort by last_parked, then timestamp
    candidates.sort(key=lambda x: (
        datetime.fromisoformat(x["last_parked"]) if x["last_parked"] else datetime.min,
        x["timestamp"]
    ))
    
    # Allocate
    result_admin = []
    result_tower = []
    result_wait = []
    
    for c in candidates:
        if c["car_type"] == "SUV":
            if len(result_admin) < admin_slots:
                result_admin.append(c["display_name"])
            else:
                result_wait.append(c["display_name"])
        else:  # SEDAN
            if len(result_tower) < tower_slots:
                result_tower.append(c["display_name"])
            elif len(result_admin) < admin_slots:
                result_admin.append(c["display_name"])
            else:
                result_wait.append(c["display_name"])
    
    # Update last_parked_date for allocated staff
    for name in result_admin + result_tower:
        base_name = name.split(" (")[0]
        for u in users:
            if u["name"] == base_name:
                u["last_parked_date"] = today_str
    
    save_json(USERS_FILE, users)
    
    # Save to history
    history_entry = {
        "date": today_str,
        "admin": result_admin,
        "tower": result_tower,
        "wait": result_wait
    }
    
    history = [h for h in history if h["date"] != today_str]
    history.append(history_entry)
    history.sort(key=lambda x: x["date"], reverse=True)
    save_json(HISTORY_FILE, history)
    
    print(f"✅ Allocation completed:")
    print(f"   🏢 Admin: {len(result_admin)}/{admin_slots}")
    print(f"   🅿️ Tower: {len(result_tower)}/{tower_slots}")
    print(f"   ⏳ Wait: {len(result_wait)}")
    
    # Prepare Slack message
    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    target_weekday = day_names[target_date.weekday()]
    
    admin_capacity = 1
    tower_capacity = tower_slots
    admin_occupied = len(result_admin)
    tower_occupied = len(result_tower)
    admin_remaining = admin_capacity - admin_occupied
    tower_remaining = tower_capacity - tower_occupied
    total_capacity = admin_capacity + tower_capacity
    total_occupied = admin_occupied + tower_occupied
    total_remaining = total_capacity - total_occupied
    
    def strip_time(name_str):
        parts = name_str.rsplit(' ', 1)
        if len(parts) == 2 and (':' in parts[1] or parts[1] == '수동입력'):
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
    print("📤 Sending Slack notification...")
    success, msg = send_slack_message(slack_msg)
    
    if success:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")
    
    print("🎉 Automation completed!")

if __name__ == "__main__":
    main()
