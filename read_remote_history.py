import subprocess
import json

try:
    # Fetch just to be sure we have the objects (we did this earlier, but good to be safe)
    # subprocess.run(["git", "fetch", "origin"], check=True) 
    
    # Read the file from origin/main
    result = subprocess.run(["git", "show", "origin/main:history.json"], capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        # Write just the dates to a file
        with open("debug_history.txt", "w", encoding="utf-8") as f:
            for item in data[:5]:
                f.write(f"Date: {item.get('date')} - Created: {item.get('created_at', 'N/A')}\n")
    else:
        with open("debug_history.txt", "w", encoding="utf-8") as f:
            f.write(f"Error: {result.stderr}")

except Exception as e:
    print(f"Exception: {e}")
