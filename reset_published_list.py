"""
Reset Published Videos Log
Archives the current published_videos.json with timestamp and starts a fresh log.
"""
import os
import shutil
from datetime import datetime

LOG_FILE = "published_videos.json"

if os.path.exists(LOG_FILE):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"published_videos_backup_{timestamp}.json"
    shutil.copy(LOG_FILE, backup_file)
    print(f"Backed up {LOG_FILE} -> {backup_file}")
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("[]\n")
    print(f"Reset {LOG_FILE} to empty list.")
else:
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("[]\n")
    print(f"Created fresh {LOG_FILE}.")
