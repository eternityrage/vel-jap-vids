"""
Instagram Graph API Upload (Reels & Stories)
"""
import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)


def upload_to_instagram(video_path, caption, is_story=False):
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN') or os.getenv('IG_ACCESS_TOKEN')
    account_id = os.getenv('INSTAGRAM_ACCOUNT_ID') or os.getenv('IG_USER_ID')

    if not access_token or not account_id:
        return {'status': 'skipped', 'reason': 'Missing Instagram credentials'}

    print(f"[instagram] Uploading to Instagram (is_story={is_story})...")
    # Instagram requires a public URL or container-based upload
    return {'status': 'skipped', 'reason': 'Direct file upload requires public video URL or hosting'}
