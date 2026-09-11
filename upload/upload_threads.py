"""
Threads Video Upload
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)


def upload_to_threads(video_path, text=""):
    access_token = os.getenv('THREADS_ACCESS_TOKEN')
    user_id = os.getenv('THREADS_USER_ID')

    if not access_token or not user_id:
        return {'status': 'skipped', 'reason': 'Missing Threads credentials'}

    print("[threads] Uploading video to Threads...")
    return {'status': 'skipped', 'reason': 'Direct video container flow requires public URL'}
