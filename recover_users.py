#!/usr/bin/env python3
"""
Emergency Recovery Script: Rebuild last_parked_date from history.json
Run this once to sync users.json with actual history data.
"""

import json
from datetime import datetime

# Load files
with open("users.json", "r", encoding="utf-8") as f:
    users = json.load(f)

with open("history.json", "r", encoding="utf-8") as f:
    history = json.load(f)

# Build a map: name -> latest parking date
last_parked_map = {}

for entry in history:
    date = entry["date"]
    
    # Process all names from admin, tower, wait
    all_names = entry.get("admin", []) + entry.get("tower", []) + entry.get("wait", [])
    
    for name_entry in all_names:
        # Extract base name (remove car type and time)
        # Examples: "피치 (SUV) 21:57" -> "피치"
        #           "피치" -> "피치"
        base_name = name_entry.split(" (")[0].strip()
        
        # Update to latest date (proper datetime comparison)
        if base_name not in last_parked_map:
            last_parked_map[base_name] = date
        else:
            # Compare as datetime objects
            current_latest = datetime.strptime(last_parked_map[base_name], "%Y-%m-%d")
            new_date = datetime.strptime(date, "%Y-%m-%d")
            if new_date > current_latest:
                last_parked_map[base_name] = date

# Update users.json
for user in users:
    user_name = user["name"]
    if user_name in last_parked_map:
        user["last_parked_date"] = last_parked_map[user_name]
        print(f"✅ Updated {user_name}: {last_parked_map[user_name]}")
    else:
        user["last_parked_date"] = None
        print(f"ℹ️  No history for {user_name}, set to null")

# Save updated users.json
with open("users.json", "w", encoding="utf-8") as f:
    json.dump(users, f, ensure_ascii=False, indent=4)

print("\n✅ Recovery complete! users.json has been updated.")
print("⚠️  Please commit and push users.json to GitHub manually.")
