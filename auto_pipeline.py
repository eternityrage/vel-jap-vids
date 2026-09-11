"""
Main Automation Pipeline for GitHub Actions - Velocity Japanese
1. Fetch ONE video from Google Drive (Folder ID: 1o2ntZzxWTogxmK43rPt9Hx1kEzMjLdRf)
2. Process with FFmpeg (upscale to 1080x1920, audio normalization, loop if <10s)
3. Upload to Facebook Page 'Velocity Japanese' (Reel + Pinned Comment with website link)

FALLBACK: If all videos have been posted, selects a random video for reposting
(weighted random: videos posted fewer times get higher priority).
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()


def run_pipeline():
    print("\n" + "=" * 60)
    print("STARTING AUTOMATION PIPELINE - VELOCITY JAPANESE")
    print("=" * 60 + "\n")

    # Step 1: Try fetching a NEW video from Google Drive
    print("STEP 1: Fetching video from Google Drive...")
    from google_drive_fetch import fetch_one_video_from_drive

    downloaded = fetch_one_video_from_drive(allow_repost=False)

    if not downloaded:
        print("\n[pipeline] No new videos in Google Drive")
        print("[pipeline] REPOST MODE: Fetching random published video for repost...\n")

        downloaded = fetch_one_video_from_drive(allow_repost=True)

        if not downloaded:
            print("\n[pipeline] No videos available to post. Pipeline complete.")
            print("[pipeline] Check Google Drive folder credentials or add new videos.")
            return

        print("\n[pipeline] Repost Mode: Video downloaded\n")

    print("\nStep 1 complete: Video ready for processing\n")

    # Step 2: Process video with FFmpeg
    print("STEP 2: Processing video (upscaling + audio normalization)...")
    from process_videos import process_single_video

    processed_video = process_single_video(downloaded)

    if not processed_video or not os.path.exists(processed_video):
        print("\n[pipeline] Video processing failed!")
        sys.exit(1)

    print("\nStep 2 complete: Video processed successfully\n")

    # Step 3: Upload to Facebook Page (Velocity Japanese)
    print("STEP 3: Uploading to social media platforms...")
    print("   Target: Facebook Page 'Velocity Japanese' (Reels, Story, Pinned Comment)")
    print("\n" + "=" * 60 + "\n")

    from daily_publisher import main as publish_video
    sys.argv = ["daily_publisher.py", processed_video]
    publish_video()

    print("\n" + "=" * 60)
    print("AUTOMATION PIPELINE COMPLETE - VELOCITY JAPANESE")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
