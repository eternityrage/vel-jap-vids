"""
YouTube Shorts Upload Module (Optional)
"""
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)


def upload_to_youtube(video_path, title, description, tags=None, category_id='27'):
    client_id = os.getenv('YT_CLIENT_ID')
    refresh_token = os.getenv('YT_REFRESH_TOKEN')

    if not client_id or not refresh_token:
        return {'status': 'skipped', 'reason': 'Missing YouTube credentials'}

    print("[youtube] YouTube upload placeholder")
    return {'status': 'skipped', 'reason': 'YouTube credentials check only'}
