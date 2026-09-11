"""
Video Processor - Velocity Japanese
- Validates resolution & duration
- Scales/pads to vertical 1080x1920 (Lanczos high quality)
- Loops short videos (<10s) to ~12s for Instagram/Facebook Reels standards
- Audio normalization with loudnorm & dynaudnorm
- Optional watermark removal (REMOVE_WATERMARK=true/false)
"""
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

input_dir = os.getenv("LOCAL_INPUT_DIR", "Videos")
output_dir = "Processed_Videos"
Path(output_dir).mkdir(parents=True, exist_ok=True)

REMOVE_WATERMARK = os.getenv("REMOVE_WATERMARK", "false").lower() in ("true", "1", "yes")


def get_video_duration(video_path):
    cmd_probe = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
        res = subprocess.check_output(cmd_probe).decode("utf-8").strip()
        return float(res)
    except Exception as e:
        print(f"[processor] Could not get duration: {e}")
        return None


def process_single_video(video_path):
    if not os.path.exists(video_path):
        print(f"[processor] Error: Video not found: {video_path}")
        return None

    filename = os.path.basename(video_path)
    out_path = os.path.join(output_dir, filename)

    if os.path.exists(out_path):
        print(f"[processor] Skipping {filename} - already processed")
        return out_path

    duration = get_video_duration(video_path)
    needs_looping = duration is not None and duration < 10

    if needs_looping:
        print(f"[processor] Video duration {duration:.2f}s (< 10s) -> Looping once to ~{duration * 2:.1f}s")
    else:
        print(f"[processor] Video duration {duration:.2f}s -> No loop needed")

    # Probe resolution
    cmd_probe = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        video_path
    ]
    try:
        res = subprocess.check_output(cmd_probe).decode("utf-8").strip()
        width, height = map(int, res.split("x"))
    except Exception as e:
        print(f"[processor] Error getting resolution: {e}")
        width, height = 1080, 1920

    # Probe audio
    cmd_audio = [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
        video_path
    ]
    try:
        audio_check = subprocess.check_output(cmd_audio).decode("utf-8").strip()
        has_audio = bool(audio_check)
    except:
        has_audio = False

    print(f"[processor] Input video: {width}x{height}, Has audio: {has_audio}")

    # Build video filter
    delogo_filter = ""
    if REMOVE_WATERMARK:
        w_delogo = 180
        h_delogo = 80
        x_delogo = 1080 - w_delogo - 5
        y_delogo = 1920 - h_delogo - 5
        delogo_filter = f",delogo=x={x_delogo}:y={y_delogo}:w={w_delogo}:h={h_delogo}"

    if needs_looping:
        vf_filter = (
            f"[0:v]split[v0][v1];"
            f"[v0]scale=1080:1920:flags=lanczos,unsharp=5:5:1.0:5:5:0.0{delogo_filter}[s0];"
            f"[v1]scale=1080:1920:flags=lanczos,unsharp=5:5:1.0:5:5:0.0{delogo_filter}[s1];"
            f"[s0][s1]concat=n=2:v=1:a=0[v]"
        )
    else:
        vf_filter = f"[0:v]scale=1080:1920:flags=lanczos,unsharp=5:5:1.0:5:5:0.0{delogo_filter}[v]"

    if has_audio:
        if needs_looping:
            af_filter = "[0:a]aloop=loop=1:size=2e+09[a1];[a1]loudnorm=I=-16:TP=-1.5:LRA=11,dynaudnorm=50:3:0.5[a]"
        else:
            af_filter = "[0:a]loudnorm=I=-16:TP=-1.5:LRA=11,dynaudnorm=50:3:0.5[a]"

        cmd_ffmpeg = [
            "ffmpeg", "-y", "-i", video_path,
            "-filter_complex", f"{vf_filter};{af_filter}",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            out_path
        ]
    else:
        cmd_ffmpeg = [
            "ffmpeg", "-y", "-i", video_path,
            "-filter_complex", vf_filter,
            "-map", "[v]",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-an",
            out_path
        ]

    print(f"[processor] Running ffmpeg enhancement for {filename}...")
    result = subprocess.run(cmd_ffmpeg, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[processor] Enhanced video successfully saved -> {out_path}")
        return out_path
    else:
        print(f"[processor] FFmpeg failed with exit code {result.returncode}:")
        print(result.stderr[-500:])
        return None


def main():
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    if specific_video:
        res = process_single_video(specific_video)
        if not res:
            sys.exit(1)
    else:
        videos = [f for f in os.listdir(input_dir) if f.endswith(('.mp4', '.mov'))]
        for v in videos:
            process_single_video(os.path.join(input_dir, v))


if __name__ == "__main__":
    main()
