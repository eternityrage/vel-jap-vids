"""
Facebook Reels & Stories Upload - Velocity Japanese
Uploads vertical Reels to Facebook Page and automatically posts a pinned comment
with website link (https://velocityjapanese.com) inspired by vel_jp.
"""
import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

WEBSITE_URL = "https://velocityjapanese.com"


def _post_pinned_comment(video_id, description, access_token, page_id):
    """
    Post a pinned comment on the Facebook Reel with the Velocity Japanese website link.
    Inspired by kreggsmimax/vel_jp pinned comment pattern.
    """
    pinned_message = (
        f"{description}\n\n"
        f"🌐 Learn more at our website: {WEBSITE_URL}\n"
        f"Visit velocityjapanese.com for daily Japanese lessons!"
    )
    print(f"[facebook] Posting pinned comment with website ({WEBSITE_URL})...")
    max_retries = 5
    comment_id = None

    for attempt in range(max_retries):
        try:
            comment_url = f"https://graph.facebook.com/v21.0/{video_id}/comments"
            comment_data = {
                'access_token': access_token,
                'message': pinned_message
            }
            res_comment = requests.post(comment_url, data=comment_data, timeout=30)
            if res_comment.status_code == 200:
                resp = res_comment.json()
                comment_id = resp.get('id')
                if comment_id:
                    print(f"[facebook] Comment posted! ID: {comment_id}")
                    break
            elif res_comment.status_code == 404 and attempt < max_retries - 1:
                wait = (attempt + 1) * 10
                print(f"[facebook] Video not ready for comments yet, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"[facebook] Comment post attempt failed: {res_comment.text}")
        except Exception as e:
            print(f"[facebook] Comment post error: {e}")
            break

    if comment_id:
        try:
            pin_url = f"https://graph.facebook.com/v21.0/{comment_id}"
            pin_data = {
                'access_token': access_token,
                'is_pinned': 'true'
            }
            res_pin = requests.post(pin_url, data=pin_data, timeout=15)
            if res_pin.status_code == 200:
                print("[facebook] Comment pinned successfully to top of Reel!")
            else:
                print(f"[facebook] Pin response: {res_pin.text}")
        except Exception as e:
            print(f"[facebook] Pin error: {e}")


def upload_to_facebook(video_path, description, title="Velocity Japanese"):
    print("\n" + "=" * 60)
    print("FACEBOOK UPLOAD STARTING - VELOCITY JAPANESE")
    print("=" * 60)

    access_token = os.getenv('FACEBOOK_ACCESS_TOKEN') or os.getenv('FB_ACCESS_TOKEN')
    page_id = os.getenv('FACEBOOK_PAGE_ID') or os.getenv('FB_PAGE_ID')

    def mask(s): return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else ("PLACEHOLDER" if s else "MISSING")
    print(f"[facebook] Page ID: {page_id}")
    print(f"[facebook] Access Token: {mask(access_token)}")

    if not access_token:
        print("[facebook] Skipping Facebook upload - FACEBOOK_ACCESS_TOKEN not set")
        return {'status': 'skipped', 'reason': 'Missing FACEBOOK_ACCESS_TOKEN', 'platform': 'facebook'}

    if not page_id:
        print("[facebook] Skipping Facebook upload - FACEBOOK_PAGE_ID not set")
        return {'status': 'skipped', 'reason': 'Missing FACEBOOK_PAGE_ID', 'platform': 'facebook'}

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        error_msg = f"Video file not found: {video_path}"
        print(f"[facebook] {error_msg}")
        raise FileNotFoundError(error_msg)

    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[facebook] Video file: {video_path} ({file_size_mb:.2f} MB)")
    print("[facebook] Uploading to Facebook Reels (3-step Graph API v21.0)...")

    fb_description = (
        f"{description}\n\n"
        f"🌐 Learn Japanese with Velocity Japanese: {WEBSITE_URL}"
    )

    try:
        file_size = video_path_obj.stat().st_size

        # Step 1: Initialize
        print("[facebook] Step 1: Initiating upload session...")
        start_url = f"https://graph.facebook.com/v21.0/{page_id}/video_reels"
        start_data = {
            'access_token': access_token,
            'upload_phase': 'start',
            'file_size': file_size
        }
        res_start = requests.post(start_url, data=start_data, timeout=30)
        if res_start.status_code != 200:
            print(f"[facebook] Start Phase Error: {res_start.text}")
            raise Exception(f"Start Phase Failed: {res_start.text}")

        start_json = res_start.json()
        video_id = start_json.get('video_id')
        upload_url = start_json.get('upload_url')

        if not video_id:
            raise Exception(f"No video_id returned: {start_json}")

        # Step 2: Transfer binary chunk
        print("[facebook] Step 2: Transferring file to Facebook servers...")
        headers = {
            'Authorization': f'OAuth {access_token}',
            'offset': '0',
            'file_size': str(file_size)
        }
        with open(video_path, 'rb') as f:
            res_transfer = requests.post(upload_url, headers=headers, data=f, timeout=600)

        if res_transfer.status_code != 200:
            print(f"[facebook] Transfer Phase Error: {res_transfer.text}")
            raise Exception(f"Transfer Phase Failed: {res_transfer.text}")

        # Step 3: Finish and publish
        print("[facebook] Step 3: Publishing Reel...")
        finish_url = f"https://graph.facebook.com/v21.0/{page_id}/video_reels"
        finish_data = {
            'access_token': access_token,
            'upload_phase': 'finish',
            'video_id': video_id,
            'description': fb_description,
            'video_state': 'PUBLISHED'
        }
        res_finish = requests.post(finish_url, data=finish_data, timeout=60)

        if res_finish.status_code == 200 and res_finish.json().get('success'):
            print(f"[facebook] SUCCESS! Reel uploaded to Facebook!")
            print(f"[facebook] Video ID: {video_id}")
            print(f"[facebook] Post URL: https://facebook.com/{video_id}")

            # Pinned comment with website link
            _post_pinned_comment(video_id, description, access_token, page_id)

            return {
                'id': video_id,
                'platform': 'facebook',
                'status': 'success',
                'url': f"https://facebook.com/{video_id}"
            }
        else:
            print(f"[facebook] Finish Phase Error: {res_finish.text}")
            raise Exception(f"Finish Phase Failed: {res_finish.text}")

    except Exception as e:
        print(f"[facebook] Facebook Reel Error: {e}")
        raise


def upload_to_facebook_story(video_path):
    print("\n" + "=" * 60)
    print("FACEBOOK STORY UPLOAD STARTING - VELOCITY JAPANESE")
    print("=" * 60)

    access_token = os.getenv('FACEBOOK_ACCESS_TOKEN') or os.getenv('FB_ACCESS_TOKEN')
    page_id = os.getenv('FACEBOOK_PAGE_ID') or os.getenv('FB_PAGE_ID')

    if not access_token or not page_id:
        print("[facebook] Skipping Story upload - Missing credentials")
        return {'status': 'skipped', 'reason': 'Missing credentials', 'platform': 'facebook_story'}

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"[facebook] Video not found: {video_path}")

    try:
        file_size = video_path_obj.stat().st_size
        start_url = f"https://graph.facebook.com/v21.0/{page_id}/video_stories"
        start_data = {
            'access_token': access_token,
            'upload_phase': 'start',
            'file_size': file_size
        }
        res_start = requests.post(start_url, data=start_data, timeout=30)
        if res_start.status_code != 200:
            raise Exception(f"Story start failed: {res_start.text}")

        start_json = res_start.json()
        upload_session_id = start_json.get('upload_session_id')
        video_id = start_json.get('video_id')
        upload_url = start_json.get('upload_url')

        if upload_url:
            headers = {
                'Authorization': f'OAuth {access_token}',
                'offset': '0',
                'file_size': str(file_size)
            }
            with open(video_path, 'rb') as f:
                res_transfer = requests.post(upload_url, headers=headers, data=f, timeout=600)
            if res_transfer.status_code != 200:
                raise Exception(f"Story transfer failed: {res_transfer.text}")

            finish_url = f"https://graph.facebook.com/v21.0/{page_id}/video_stories"
            finish_data = {
                'access_token': access_token,
                'upload_phase': 'finish',
                'video_id': video_id
            }
            if upload_session_id:
                finish_data['upload_session_id'] = upload_session_id
            res_finish = requests.post(finish_url, data=finish_data, timeout=60)
            if res_finish.status_code == 200 or res_finish.json().get('success'):
                print(f"[facebook] SUCCESS! Story uploaded (Video ID: {video_id})")
                return {'id': video_id, 'platform': 'facebook_story', 'status': 'success'}
            else:
                raise Exception(f"Story finish failed: {res_finish.text}")

        return {'status': 'skipped', 'reason': 'No upload URL returned'}
    except Exception as e:
        print(f"[facebook] Story error: {e}")
        return {'status': 'failed', 'error': str(e)}
