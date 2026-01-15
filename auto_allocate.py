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
    # If running at 08:00~08:59, we consider it "Today's" allocation time.
    if now.hour < 9:
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
    
    # CRITICAL FIX: Weekend accumulation for Monday
    # If today is Saturday or Sunday, do NOT run auto-allocation.
    # Friday's script already allocated for Friday.
    # We want Friday afternoon, Saturday, and Sunday applications to accumulate for Monday.
    today_str = str(target_date)
    
    # CRITICAL FIX: Weekend accumulation for Monday
    # If today is Saturday or Sunday, do NOT run auto-allocation.
    # Friday's script already allocated for Friday.
    # We want Friday afternoon, Saturday, and Sunday applications to accumulate for Monday.
    now_kst = get_kst_time()
    if now_kst.weekday() in [5, 6]: # 5 is Saturday, 6 is Sunday
        print(f"😴 It's {now_kst.strftime('%A')}. Skipping auto-allocation to allow Monday requests to accumulate.")
        return

    # PRECISION TIMING: Wait until 08:01 AM KST if running early
    # GitHub Actions runs early (e.g. 07:30-07:50), so we wait for exact timing.
    target_hour = 8
    target_minute = 1
    
    if now_kst.hour < target_hour or (now_kst.hour == target_hour and now_kst.minute < target_minute):
        import time
        target_time = now_kst.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        wait_seconds = (target_time - now_kst).total_seconds()
        
        if wait_seconds > 0:
            print(f"⏳ Running early. Waiting {wait_seconds:.0f} seconds until {target_hour}:{target_minute:02d} KST...")
            # Print periodically to keep CI alive and show progress
            while wait_seconds > 60:
                time.sleep(60)
                wait_seconds -= 60
                print(f"   ... {wait_seconds / 60:.0f} minutes remaining")
            time.sleep(wait_seconds)
            print("⏰ It's time! Starting allocation.")
            
    # CRITICAL FIX: Fetch latest data just before allocation
    # GitHub Actions checks out code early (e.g. 07:30). We must pull changes 
    # that happened while we were waiting (e.g. 07:55 requests).
    print("� Fetching latest data from GitHub...")
    try:
        os.system("git config pull.rebase false")
        os.system("git pull")
        print("✅ Data synchronized.")
    except Exception as e:
        print(f"⚠️ Git pull failed: {e}")

    # RELOAD DATA after pull
    print("📂 Reloading data files...")
    users = load_json(USERS_FILE, [])
    # History load skipped as we haven't modified it yet, but safe to reload if needed.
    # Requests is critical.
    requests_data = load_json(REQUESTS_FILE, {
        "target_date": "",
        "applicants": [],
        "guests": [],
        "sante_opt_out": False
    })
    
    # DEBUG: Log the state of requests_data after reload
    print(f"📂 Loaded requests_data:")
    print(f"   target_date: {requests_data.get('target_date')}")
    print(f"   applicants: {len(requests_data.get('applicants', []))} entries")
    print(f"   guests: {len(requests_data.get('guests', []))} entries")
    print(f"   sante_opt_out: {requests_data.get('sante_opt_out')}")
    
    # Print full applicants data for debugging
    if requests_data.get('applicants'):
        print(f"   Applicants detail:")
        for i, app in enumerate(requests_data['applicants']):
            print(f"     [{i+1}] {app}")
    if requests_data.get('guests'):
        print(f"   Guests detail:")
        for i, g in enumerate(requests_data['guests']):
            print(f"     [{i+1}] {g}")
    
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
            # KST ENFORCEMENT: Handle both Naive (old UTC) and Aware (new KST)
            try:
                dt_raw = datetime.fromisoformat(app["timestamp"])
                if dt_raw.tzinfo:
                    # Aware: Convert to KST
                    dt_kst = dt_raw.astimezone(pytz.timezone('Asia/Seoul'))
                else:
                    # Naive: Assume UTC, add 9 hours
                    dt_kst = dt_raw + timedelta(hours=9)
                
                # Make naive for safe sorting with datetime.min
                ts = dt_kst.replace(tzinfo=None)
            except:
                ts = datetime.min
            
            u_time = ts.strftime("%H:%M")
        
        user_obj = next((u for u in users if u["name"] == u_name), None)
        
        # FALLBACK: If user not found (e.g., '피르'), treat as new applicant with high priority
        if user_obj:
            c_type = user_obj["car_type"]
            # CRITICAL: Convert null/None to empty string for consistent sorting
            l_parked = user_obj.get("last_parked_date") or ""
        else:
            c_type = "SEDAN" # Default for unregistered
            l_parked = "1900-01-01" # High priority (never parked)
            
        candidates.append({
            "type": "staff",
            "name": u_name,
            "car_type": c_type,
            "last_parked": l_parked,
            "timestamp": ts,
            "display_name": f"{u_name} ({c_type}) {u_time}"
        })
        print(f"  ✅ Added staff candidate: {u_name} ({c_type}) - last_parked: {l_parked}, timestamp: {u_time}")

    for g in requests_data.get("guests", []):
        if "timestamp" in g:
            # KST ENFORCEMENT
            try:
                dt_raw = datetime.fromisoformat(g["timestamp"])
                if dt_raw.tzinfo:
                    dt_kst = dt_raw.astimezone(pytz.timezone('Asia/Seoul'))
                else:
                    dt_kst = dt_raw + timedelta(hours=9)
                ts = dt_kst.replace(tzinfo=None)
            except:
                ts = datetime.min
            time_str = ts.strftime("%H:%M")
        else:
            ts = datetime.min
            time_str = "00:00"
        
        candidates.append({
            "type": "guest",
            "name": g["name"],
            "car_type": g["car_type"],
            "location": g["location"],
            "timestamp": ts,
            "display_name": f"{g['name']} ({g['car_type']}) {time_str}"
        })
        print(f"  ✅ Added guest candidate: {g['name']} ({g['car_type']}) - location: {g.get('location', 'N/A')}, timestamp: {time_str}")
    
    
    # Sort
    staff_c = [c for c in candidates if c["type"] == "staff"]
    guest_c = [c for c in candidates if c["type"] == "guest"]
    
    # Sort staff by last_parked (empty/null is priority) then timestamp
    # CRITICAL: Match logic with app.py
    staff_c.sort(key=lambda x: (
        x["last_parked"] if x["last_parked"] else "1900-01-01",
        x["timestamp"]
    ))
    # Sort guests by timestamp
    guest_c.sort(key=lambda x: x["timestamp"])
    
    # Allocate
    result_admin = []
    result_tower = []
    result_wait = []
    
    # 1. GUESTS FIRST (High Priority)
    for g in guest_c:
        assigned = False
        # Simplified logic: Guests usually don't have location preference in automation script? 
        # Check if 'location' exists in g (it should if copied from app.py logic)
        loc = g.get("location", ["상관없음"]) # Default to any
        
        if "관리실" in loc:
            if admin_slots > 0:
                result_admin.append(g["display_name"])
                admin_slots -= 1
                assigned = True
        elif "타워" in loc:
            if tower_slots > 0:
                result_tower.append(g["display_name"])
                tower_slots -= 1
                assigned = True
        else: # "상관없음" or default
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

    # 2. STAFF SECOND
    for s in staff_c:
        assigned = False
        if s["car_type"] == "SUV":
            if admin_slots > 0:
                result_admin.append(s["display_name"])
                admin_slots -= 1
                assigned = True
        else:  # SEDAN
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
    print(f"   🏢 Admin: {len(result_admin)}/{1} (remaining: {admin_capacity - len(result_admin)})")
    print(f"   🅿️ Tower: {len(result_tower)}/{tower_capacity} (remaining: {tower_capacity - len(result_tower)})")
    print(f"   ⏳ Wait: {len(result_wait)}")
    print(f"   📋 Result details:")
    print(f"      Admin: {result_admin}")
    print(f"      Tower: {result_tower}")
    print(f"      Wait: {result_wait}")
    
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
    print(f"Message preview (first 200 chars): {slack_msg[:200]}...")
    success, msg = send_slack_message(slack_msg)
    
    if success:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")
    
    # Commit changes to GitHub
    print("💾 Committing changes to GitHub...")
    # Reset requests for next day
    print("🧹 Resetting requests for next day...")
    requests_data["applicants"] = []
    requests_data["guests"] = []
    # requests_data["target_date"] = str(target_date + timedelta(days=1)) # Optional
    save_json(REQUESTS_FILE, requests_data)
    
    # Commit changes to GitHub
    print("💾 Committing changes to GitHub...")
    try:
        os.system('git config user.name "GitHub Actions Bot"')
        os.system('git config user.email "actions@github.com"')
        # Add requests.json to the commit
        os.system('git add history.json users.json requests.json visitor_count.json')
        os.system(f'git commit -m "Auto-update: Parking allocation for {today_str}"')
        os.system('git push')
        print("✅ Changes committed to GitHub")
    except Exception as e:
        print(f"⚠️ Failed to commit to GitHub: {str(e)}")
    
    print("🎉 Automation completed!")

if __name__ == "__main__":
    main()
