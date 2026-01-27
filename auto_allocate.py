#!/usr/bin/env python3
"""
Automated Parking Allocation Script
Runs daily via GitHub Actions to allocate parking and send Slack notification

MAJOR IMPROVEMENTS (2026-01-22):
- Added environment validation
- Replaced os.system() with subprocess for reliable git operations
- Added Slack retry mechanism
- Added slack_notified flag to history entries
- Added comprehensive logging
- Added error handling and recovery
"""

import json
import os
import sys
import subprocess
import time
from datetime import datetime, timedelta
import pytz
import requests

# File paths (GitHub Actions runs from repo root)
USERS_FILE = "users.json"
REQUESTS_FILE = "requests.json"
HISTORY_FILE = "history.json"

def load_json(file_path, default_data):
    """Load JSON data from file with error handling."""
    if not os.path.exists(file_path):
        print(f"⚠️ File not found: {file_path}, using default data")
        return default_data
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"✅ Loaded {file_path}")
            return data
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error in {file_path}: {e}")
        return default_data
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return default_data

def save_json(file_path, data):
    """Save JSON data to file with error handling."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Saved {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving {file_path}: {e}")
        return False

def get_kst_time():
    """Get current time in KST timezone."""
    return datetime.now(pytz.timezone('Asia/Seoul'))

def get_target_date():
    """
    Get target date for parking allocation.
    - If before 9 AM: today
    - If after 9 AM: tomorrow
    - Skip weekends
    """
    now = get_kst_time()
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

def validate_environment():
    """
    Validate that all required environment variables are set.
    Returns: (success: bool, message: str)
    """
    print("\n" + "="*50)
    print("🔍 ENVIRONMENT VALIDATION")
    print("="*50)
    
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL is not set!")
        return False, "SLACK_WEBHOOK_URL environment variable is missing"
    
    if not webhook_url.startswith('https://hooks.slack.com/'):
        print(f"❌ Invalid SLACK_WEBHOOK_URL format: {webhook_url[:30]}...")
        return False, "SLACK_WEBHOOK_URL does not appear to be a valid Slack webhook"
    
    print(f"✅ SLACK_WEBHOOK_URL is set: {webhook_url[:40]}...")
    
    # Check file existence
    for file_path in [USERS_FILE, REQUESTS_FILE, HISTORY_FILE]:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"⚠️ {file_path} does not exist (will use defaults)")
    
    print("="*50 + "\n")
    return True, "Environment validation passed"

def send_slack_message(message, timeout=10):
    """
    Send a message to Slack using webhook URL.
    Returns: (success: bool, message: str)
    """
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return False, "SLACK_WEBHOOK_URL not set in environment"
    
    try:
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            return True, "Slack message sent successfully"
        else:
            return False, f"Failed with status code: {response.status_code}, body: {response.text[:100]}"
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except Exception as e:
        return False, f"Error: {str(e)}"

def send_slack_with_retry(message, max_retries=3, retry_delay=5):
    """
    Send Slack message with retry mechanism.
    Returns: bool (success)
    """
    print(f"\n📤 Sending Slack notification (max {max_retries} attempts)...")
    print(f"Message preview (first 200 chars):\n{message[:200]}...\n")
    
    for attempt in range(1, max_retries + 1):
        print(f"Attempt {attempt}/{max_retries}...", end=" ")
        success, msg = send_slack_message(message)
        
        if success:
            print(f"✅ {msg}")
            return True
        else:
            print(f"❌ {msg}")
            if attempt < max_retries:
                print(f"   Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
    
    print(f"❌ All {max_retries} attempts failed!")
    return False

def safe_git_pull():
    """
    Safely perform git pull using subprocess.
    Returns: bool (success)
    """
    print("\n" + "="*50)
    print("📂 FETCHING LATEST DATA FROM GITHUB")
    print("="*50)
    
    try:
        # Configure git
        result = subprocess.run(
            ['git', 'config', 'pull.rebase', 'false'],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        print("✅ Git config set")
        
        # Pull latest changes
        result = subprocess.run(
            ['git', 'pull'],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        print(f"✅ Git pull successful:")
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        print("="*50 + "\n")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Git pull timeout!")
        print("="*50 + "\n")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Git pull failed!")
        print(f"   Exit code: {e.returncode}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        print("="*50 + "\n")
        return False
    except FileNotFoundError:
        print("❌ Git command not found!")
        print("   (This is normal in some CI environments)")
        print("="*50 + "\n")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during git pull: {e}")
        print("="*50 + "\n")
        return False

def log_execution_state():
    """Log detailed execution state for debugging."""
    now_kst = get_kst_time()
    target_date = get_target_date()
    
    print("\n" + "="*50)
    print("🚀 AUTO ALLOCATION EXECUTION")
    print("="*50)
    print(f"Current Time (KST): {now_kst.strftime('%Y-%m-%d %H:%M:%S %A')}")
    print(f"Target Date: {target_date} ({['월','화','수','목','금','토','일'][target_date.weekday()]})")
    print(f"")
    print(f"Environment:")
    print(f"  SLACK_WEBHOOK_URL: {'✅ Set' if os.environ.get('SLACK_WEBHOOK_URL') else '❌ Not Set'}")
    print(f"")
    print(f"Files:")
    print(f"  {USERS_FILE}: {'✅' if os.path.exists(USERS_FILE) else '❌'}")
    print(f"  {REQUESTS_FILE}: {'✅' if os.path.exists(REQUESTS_FILE) else '❌'}")
    print(f"  {HISTORY_FILE}: {'✅' if os.path.exists(HISTORY_FILE) else '❌'}")
    print("="*50 + "\n")

def safe_git_commit_push(commit_message):
    """
    Safely commit and push changes to GitHub.
    Returns: bool (success)
    """
    print("\n💾 Committing changes to GitHub...")
    
    try:
        # Configure git user
        subprocess.run(['git', 'config', 'user.name', 'GitHub Actions Bot'], check=True, timeout=5)
        subprocess.run(['git', 'config', 'user.email', 'actions@github.com'], check=True, timeout=5)
        
        # Add files
        subprocess.run(['git', 'add', HISTORY_FILE, USERS_FILE, REQUESTS_FILE], check=True, timeout=10)
        
        # Commit
        result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            # No changes to commit is okay
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                print("ℹ️ No changes to commit")
                return True
            else:
                print(f"❌ Commit failed: {result.stderr}")
                return False
        
        # Push
        result = subprocess.run(['git', 'push'], capture_output=True, text=True, check=True, timeout=30)
        print("✅ Changes committed and pushed to GitHub")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Git operation timeout!")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e.stderr if e.stderr else str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during git commit/push: {e}")
        return False

def main():
    """Main execution function."""
    log_execution_state()
    
    # Step 1: Validate environment
    success, msg = validate_environment()
    if not success:
        print(f"\n❌ FATAL ERROR: {msg}")
        sys.exit(1)
    
    # Step 2: Check if today is weekend (skip execution)
    now_kst = get_kst_time()
    if now_kst.weekday() in [5, 6]:  # Saturday or Sunday
        print(f"😴 It's {now_kst.strftime('%A')}. Skipping auto-allocation.")
        print("   (Weekend applications will accumulate for Monday)")
        return
    
    # Step 2.5: DUPLICATE EXECUTION PREVENTION
    # Load history early to check if today's allocation already exists
    print("\n" + "="*50)
    print("🔍 CHECKING FOR DUPLICATE EXECUTION")
    print("="*50)
    
    history_preliminary = load_json(HISTORY_FILE, [])
    target_date_str = str(get_target_date())
    existing_entry = next((h for h in history_preliminary if h["date"] == target_date_str), None)
    
    if existing_entry and existing_entry.get("slack_notified", False):
        print(f"✅ Allocation for {target_date_str} already exists and notification was sent.")
        print("   This is likely a duplicate execution from multiple triggers.")
        print("   Exiting gracefully to prevent duplicate processing.")
        print("="*50 + "\n")
        return
    
    print(f"✅ No duplicate detected. Proceeding with allocation for {target_date_str}.")
    print("="*50 + "\n")
    
    # Step 3: Wait until 08:01 KST if running early
    target_hour = 8
    target_minute = 1
    
    if now_kst.hour < target_hour or (now_kst.hour == target_hour and now_kst.minute < target_minute):
        target_time = now_kst.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        wait_seconds = (target_time - now_kst).total_seconds()
        
        if wait_seconds > 0:
            print(f"\n⏳ Running early. Waiting {wait_seconds:.0f} seconds until {target_hour}:{target_minute:02d} KST...")
            while wait_seconds > 60:
                time.sleep(60)
                wait_seconds -= 60
                print(f"   ... {wait_seconds / 60:.0f} minutes remaining")
            time.sleep(wait_seconds)
            print("⏰ It's time! Starting allocation.\n")
    
    # Step 4: Fetch latest data from GitHub
    if not safe_git_pull():
        error_msg = "⚠️ **긴급: GitHub 데이터 동기화 실패**\n\n자동 배정을 진행할 수 없습니다!\n수동으로 배정해주세요."
        send_slack_with_retry(error_msg)
        print("\n❌ FATAL ERROR: Git pull failed. Cannot proceed with allocation.")
        sys.exit(1)
    
    # Step 5: Reload data after git pull
    print("📂 Loading data files...")
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
    
    # Debug: Log request data
    print(f"\n📋 Request Data Summary:")
    print(f"   target_date: {requests_data.get('target_date')}")
    print(f"   applicants: {len(requests_data.get('applicants', []))} entries")
    print(f"   guests: {len(requests_data.get('guests', []))} entries")
    print(f"   sante_opt_out: {requests_data.get('sante_opt_out')}")
    
    if requests_data.get('applicants'):
        print(f"\n   📝 Applicants detail:")
        for i, app in enumerate(requests_data['applicants']):
            print(f"      [{i+1}] {app}")
    
    if requests_data.get('guests'):
        print(f"\n   🎫 Guests detail:")
        for i, g in enumerate(requests_data['guests']):
            print(f"      [{i+1}] {g}")
    print()
    
    # Step 6: Check if already allocated
    history_today = next((h for h in history if h["date"] == today_str), None)
    if history_today:
        # Check if Slack notification was sent
        if not history_today.get("slack_notified", True):
            print(f"⚠️ Allocation for {today_str} exists, but Slack notification was not sent.")
            print("   Attempting to resend notification...")
            
            # Reconstruct Slack message from history
            day_names = ["월", "화", "수", "목", "금", "토", "일"]
            target_weekday = day_names[target_date.weekday()]
            
            admin_capacity = 1
            tower_capacity = 3 if requests_data.get("sante_opt_out") else 2
            admin_occupied = len(history_today.get("admin", []))
            tower_occupied = len(history_today.get("tower", []))
            
            def strip_time(name_str):
                parts = name_str.rsplit(' ', 1)
                if len(parts) == 2 and (':' in parts[1] or parts[1] == '수동입력'):
                    return parts[0]
                return name_str
            
            slack_msg = f"""📅 **{today_str} ({target_weekday}) 주차 배정 결과** (재전송)

🅿️ **주차 공간 현황**
• 전체: {admin_occupied + tower_occupied}/{admin_capacity + tower_capacity}
• 관리실: {admin_occupied}/{admin_capacity}
• 타워: {tower_occupied}/{tower_capacity}

🏢 **관리실 배정**"""
            
            if history_today.get("admin"):
                for name in history_today["admin"]:
                    slack_msg += f"\n• {strip_time(name)}"
            else:
                slack_msg += "\n• (배정 없음)"
            
            slack_msg += "\n\n🅿️ **타워 배정**"
            if history_today.get("tower"):
                for name in history_today["tower"]:
                    slack_msg += f"\n• {strip_time(name)}"
            else:
                slack_msg += "\n• (배정 없음)"
            
            if history_today.get("wait"):
                slack_msg += "\n\n⏳ **대기 인원**"
                for name in history_today["wait"]:
                    slack_msg += f"\n• {strip_time(name)}"
            
            if send_slack_with_retry(slack_msg):
                history_today["slack_notified"] = True
                save_json(HISTORY_FILE, history)
                safe_git_commit_push(f"Update: Slack notification sent for {today_str}")
                print(f"✅ Slack notification resent successfully!")
            else:
                print(f"❌ Failed to resend Slack notification!")
            
            return
        else:
            print(f"✅ Allocation for {today_str} already exists and notification was sent. Skipping.")
            return
    
    # Step 7: Check if there are applicants
    if not requests_data.get("applicants") and not requests_data.get("guests"):
        print("ℹ️ No applicants found. Skipping allocation.")
        return
    
    print(f"\n👥 Found {len(requests_data.get('applicants', []))} staff applicants")
    print(f"🎫 Found {len(requests_data.get('guests', []))} guest applicants")
    
    # Step 8: Allocation logic
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
                    dt_kst = dt_raw.astimezone(pytz.timezone('Asia/Seoul'))
                else:
                    dt_kst = dt_raw + timedelta(hours=9)
                ts = dt_kst.replace(tzinfo=None)
            except:
                ts = datetime.min
            
            u_time = ts.strftime("%H:%M")
        
        user_obj = next((u for u in users if u["name"] == u_name), None)
        
        if user_obj:
            c_type = user_obj["car_type"]
            l_parked = user_obj.get("last_parked_date") or ""
        else:
            c_type = "SEDAN"
            l_parked = "1900-01-01"
        
        candidates.append({
            "type": "staff",
            "name": u_name,
            "car_type": c_type,
            "last_parked": l_parked,
            "timestamp": ts,
            "display_name": f"{u_name} ({c_type}) {u_time}"
        })
        print(f"  ✅ Staff: {u_name} ({c_type}) - last_parked: {l_parked}, time: {u_time}")
    
    # Collect guest candidates
    for g in requests_data.get("guests", []):
        if "timestamp" in g:
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
            "location": g.get("location", ["상관없음"]),
            "timestamp": ts,
            "display_name": f"{g['name']} ({g['car_type']}) {time_str}"
        })
        print(f"  ✅ Guest: {g['name']} ({g['car_type']}) - location: {g.get('location', 'N/A')}, time: {time_str}")
    
    # Sort candidates
    staff_c = [c for c in candidates if c["type"] == "staff"]
    guest_c = [c for c in candidates if c["type"] == "guest"]
    
    staff_c.sort(key=lambda x: (
        x["last_parked"] if x["last_parked"] else "1900-01-01",
        x["timestamp"]
    ))
    guest_c.sort(key=lambda x: x["timestamp"])
    
    # Allocate
    result_admin = []
    result_tower = []
    result_wait = []
    
    # 1. Guests first (high priority)
    for g in guest_c:
        assigned = False
        loc = g.get("location", ["상관없음"])
        
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
        else:
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
    
    # 2. Staff second
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
    
    # Update last_parked_date for allocated staff
    for name in result_admin + result_tower:
        base_name = name.split(" (")[0]
        for u in users:
            if u["name"] == base_name:
                u["last_parked_date"] = today_str
    
    save_json(USERS_FILE, users)
    
    # Save to history with slack_notified flag
    history_entry = {
        "date": today_str,
        "admin": result_admin,
        "tower": result_tower,
        "wait": result_wait,
        "slack_notified": False,
        "created_at": datetime.now(pytz.timezone('Asia/Seoul')).isoformat()
    }
    
    # Remove existing entry and add new one
    history = [h for h in history if h["date"] != today_str]
    history.append(history_entry)
    history.sort(key=lambda x: x["date"], reverse=True)
    save_json(HISTORY_FILE, history)
    
    admin_capacity = 1
    tower_capacity = 3 if requests_data.get("sante_opt_out") else 2
    
    print(f"\n✅ Allocation completed:")
    print(f"   🏢 Admin: {len(result_admin)}/{admin_capacity}")
    print(f"   🅿️ Tower: {len(result_tower)}/{tower_capacity}")
    print(f"   ⏳ Wait: {len(result_wait)}")
    
    # Prepare Slack message
    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    target_weekday = day_names[target_date.weekday()]
    
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
    
    # Send to Slack with retry
    if send_slack_with_retry(slack_msg):
        # Update history with successful notification
        history_entry["slack_notified"] = True
        # Update the history list (find and update the entry we just added)
        for h in history:
            if h["date"] == today_str:
                h["slack_notified"] = True
                break
        save_json(HISTORY_FILE, history)
        print("\n✅ Slack notification sent and recorded!")
    else:
        print("\n❌ All Slack notification attempts failed!")
        print("   slack_notified flag remains False in history.")
        print("   Notification can be retried on next run.")
    
    # Reset requests for next day
    print("\n🧹 Resetting requests for next day...")
    requests_data["applicants"] = []
    requests_data["guests"] = []
    save_json(REQUESTS_FILE, requests_data)
    
    # Commit changes to GitHub
    if not safe_git_commit_push(f"Auto-update: Parking allocation for {today_str}"):
        print("⚠️ Warning: Failed to commit changes to GitHub")
        print("   (Allocation is saved locally, but may not sync)")
    
    print("\n🎉 Automation completed successfully!")
    print("="*50 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to send error notification to Slack
        try:
            error_msg = f"⚠️ **자동 배정 스크립트 실행 중 오류 발생**\n\n오류: {str(e)}\n\n수동으로 배정해주세요!"
            send_slack_with_retry(error_msg)
        except:
            pass
        
        sys.exit(1)
