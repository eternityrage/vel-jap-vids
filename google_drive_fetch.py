"""
Google Drive Video Fetcher - Velocity Japanese
Fetches Japanese learning videos from Google Drive folder:
https://drive.google.com/drive/folders/1o2ntZzxWTogxmK43rPt9Hx1kEzMjLdRf

Supports:
- Checking published_videos.json to prioritize unpublished videos
- Weighted random repost mode: when all videos have been posted, automatically
  picks a random video with fewer past posts so posting never stops.
"""
import os
import json
import sys
import random
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.http import MediaIoBaseDownload

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Default folder from user request
DEFAULT_FOLDER_ID = "1o2ntZzxWTogxmK43rPt9Hx1kEzMjLdRf"
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", DEFAULT_FOLDER_ID)
GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
LOCAL_INPUT_DIR = os.getenv("LOCAL_INPUT_DIR", "Videos")
PUBLISHED_LOG = "published_videos.json"


def get_published_videos():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return [item.get('video_name', '') for item in data]
            except json.JSONDecodeError:
                return []
    return []


def get_published_history():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    history = get_published_history()
    counts = {}
    for entry in history:
        video_name = entry.get('video_name', '')
        if video_name:
            counts[video_name] = counts.get(video_name, 0) + 1
    return counts


def get_drive_service():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

        if not GOOGLE_SERVICE_ACCOUNT_KEY:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY environment variable is not set")

        # Case 1: Local file path
        if os.path.exists(GOOGLE_SERVICE_ACCOUNT_KEY):
            creds = service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_KEY, scopes=SCOPES
            )
            service = build('drive', 'v3', credentials=creds)
            print("[drive] Google Drive initialized with Service Account file")
            return service

        # Case 2: Raw JSON string provided in env var / secret
        raw_key = GOOGLE_SERVICE_ACCOUNT_KEY.strip()
        if raw_key.startswith('{') and raw_key.endswith('}'):
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
            temp_file.write(raw_key)
            temp_file.close()

            try:
                creds = service_account.Credentials.from_service_account_file(
                    temp_file.name, scopes=SCOPES
                )
                service = build('drive', 'v3', credentials=creds)
                print("[drive] Google Drive initialized with Service Account JSON secret")
                return service
            finally:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
        else:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY is neither an existing file path nor a valid JSON string")

    except ImportError:
        print("[drive] Installing required Google Drive libraries...")
        import subprocess
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "google-auth", "google-auth-oauthlib", "google-auth-httplib2", "google-api-python-client"
        ])
        return get_drive_service()
    except Exception as e:
        print(f"[drive] Error initializing Google Drive: {e}")
        return None


def list_drive_videos(service):
    if not service:
        return []

    folder_id = GOOGLE_DRIVE_FOLDER_ID or DEFAULT_FOLDER_ID
    try:
        query = f"'{folder_id}' in parents and trashed=false"
        video_mime_types = [
            "video/mp4",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-matroska"
        ]

        videos = []
        for mime_type in video_mime_types:
            query_with_mime = f"{query} and mimeType contains '{mime_type}'"
            results = service.files().list(
                q=query_with_mime,
                fields="files(id, name, size, mimeType)",
                spaces='drive'
            ).execute()

            videos.extend(results.get('files', []))

        # Sort alphabetically by name
        videos.sort(key=lambda x: x.get('name', ''))
        return videos
    except Exception as e:
        print(f"[drive] Google Drive API error: {e}")
        return []


def download_video(service, file_info, local_path):
    try:
        request = service.files().get_media(fileId=file_info['id'])
        with open(local_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"  Download progress: {int(status.progress() * 100)}%")

        print(f"[drive] Downloaded: {file_info['name']}")
        return True
    except Exception as e:
        print(f"[drive] Failed to download {file_info['name']}: {e}")
        return False


def fetch_one_video_from_drive(allow_repost=False):
    Path(LOCAL_INPUT_DIR).mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("FETCHING VIDEO FROM GOOGLE DRIVE - VELOCITY JAPANESE")
    print(f"Folder ID: {GOOGLE_DRIVE_FOLDER_ID}")
    print("=" * 60)

    published = get_published_videos()
    print(f"Already published count: {len(published)}")

    service = get_drive_service()
    if not service:
        print("[drive] Could not connect to Google Drive service")
        return None

    videos = list_drive_videos(service)
    if not videos:
        print("[drive] No video files found in Google Drive folder.")
        return None

    print(f"[drive] Found {len(videos)} video(s) in Drive folder.")

    download_attempts = 0
    download_failures = 0
    all_are_published = True

    # 1. Look for unpublished video first
    for video_info in videos:
        video_name = video_info['name']
        if video_name in published:
            continue

        all_are_published = False
        download_attempts += 1
        local_path = os.path.join(LOCAL_INPUT_DIR, video_name)
        if download_video(service, video_info, local_path):
            print(f"\n[drive] Selected new video: {video_name}")
            return local_path
        else:
            download_failures += 1
            print("[drive] Download failed, trying next video...")

    if download_attempts > 0 and download_failures == download_attempts:
        print("[drive] Failed to download any new videos. Check permissions/quota.")
        return None

    # 2. Repost mode (when all videos are published)
    if all_are_published:
        if not allow_repost:
            print("[drive] All videos have already been published (new video search only).")
            return None

        print("\n[drive] REPOST MODE: All videos published. Selecting weighted random video...")
        repost_counts = get_repost_counts()

        video_choices = []
        weights = []
        for video_info in videos:
            vname = video_info['name']
            count = repost_counts.get(vname, 0)
            # Videos posted fewer times have much higher weight
            weight = max(1, 1000 // (3 ** min(count, 6)))
            video_choices.append(video_info)
            weights.append(weight)

        selected_video = random.choices(video_choices, weights=weights, k=1)[0]
        vname = selected_video['name']
        post_count = repost_counts.get(vname, 0)
        print(f"[drive] Selected for repost (previously posted {post_count}x): {vname}")

        local_path = os.path.join(LOCAL_INPUT_DIR, vname)
        if download_video(service, selected_video, local_path):
            return local_path
        else:
            print("[drive] Failed to download repost video.")
            return None

    return None
