"""
Daily Publisher - Velocity Japanese
Generates AI/Fallback Japanese learning titles and descriptions.
Uploads to Facebook Page 'Velocity Japanese' (Reels + Pinned Comment + Story).
Optionally posts to Instagram & Threads if credentials are present.
"""
import os
import json
import glob
import random
import requests
import shutil
import sys
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

try:
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
except ImportError:
    upload_to_facebook = None
    upload_to_facebook_story = None

try:
    from upload.upload_instagram import upload_to_instagram
except ImportError:
    upload_to_instagram = None

try:
    from upload.upload_threads import upload_to_threads
except ImportError:
    upload_to_threads = None

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

PAGE_NAME = "Velocity Japanese"
WEBSITE_URL = "https://velocityjapanese.com"

# Comprehensive Fallback Titles and Descriptions for Japanese Learning
FALLBACK_TITLES = [
    "5 Essential Daily Japanese Phrases Every Beginner Must Know! 🇯🇵",
    "How Native Japanese Speakers Really Say 'Hello' & 'Goodbye'",
    "The Most Useful Japanese Restaurant Phrases for Ordering Food 🍜",
    "Japanese Slang & Casual Words You Won't Find in Textbooks! 💬",
    "Master Japanese Pronunciation: Easy Tips for Natural Sounding Japanese",
    "Super Useful Japanese Travel Phrases for Your Next Trip to Tokyo ✈️",
    "Polite vs Casual Japanese: When to Use 'Desu' and 'Masu' Explained",
    "How to Count in Japanese: Numbers & Counter Words Made Simple 🔢",
    "Common Japanese Expressions You Hear in Every Anime 🎌",
    "Essential Japanese Shopping Phrases: Asking Prices & Trying Clothes 🛍️",
    "Daily Japanese Conversation Hacks to Boost Your Fluency Fast 🚀",
    "Easy Japanese Grammar: How the Particles は (wa) and が (ga) Really Work",
    "Top Japanese Idioms (Yojijukugo) That Will Impress Native Speakers",
    "Train Station & Commuter Japanese: How to Navigate Japan Like a Pro 🚆",
    "How to Apologize Politely in Japanese: Sumimasen vs Gomennasai 🙏",
    "Emergency Japanese Phrases Everyone Should Know for Safety 🚨",
    "Japanese Morning Routine Phrases: From Waking Up to Heading Out ☀️",
    "Cute & Expressive Japanese Sound Effects (Onomatopoeia) Decoded ✨",
    "Essential Japanese Greetings for Business and Everyday Life 🤝",
    "Saying 'Thank You' in Japanese: Arigatou vs Doumo vs Kanshashimasu 🌸",
]

FALLBACK_DESCRIPTIONS = [
    "Mastering Japanese starts with small, daily steps! 🇯🇵 Today we're diving into essential conversational phrases that native speakers use all the time. Repeat each phrase aloud 3 times to lock in proper pronunciation and rhythm. With Velocity Japanese, learning feels natural and rewarding every single day! Drop a ❤️ in the comments if you practiced today. #japanese #learnjapanese #japaneselanguage #nihongo #velocityjapanese #japaneselessons #dailyjapanese #speakjapanese #studyjapanese #kanji",
    "Ever wondered how native speakers chat outside of strict textbooks? 🗣️ Today's lesson reveals real, natural everyday Japanese expressions that will immediately make you sound more fluent. Listen closely to the pitch accent and tone! Share this with a friend who is learning Japanese. #learnjapanese #japaneselesson #nihongo #japanesevocabulary #velocityjapanese #japanesepronunciation #japantravel #japanlover #japanesestudy",
    "Heading to a ramen shop or izakaya in Japan? 🍜 Here are the exact Japanese phrases you need to order your food effortlessly, ask for recommendations, and say 'Gochisousama deshita' like a local. Save this reel for your next trip to Japan! #japanesefood #japaneseculture #learnjapanese #velocityjapanese #traveljapan #tokyolife #japantrip #nihongo #japanesestudy #japanesegrammar",
    "Level up your conversational skills with authentic Japanese slang and casual phrases! 💬 Understanding how friends talk to each other in Japan is key to feeling connected to the culture. Which of these phrases was new to you? Let us know in the comments below! #japaneselessons #nihongo #japaneseslang #velocityjapanese #dailyjapanese #japanesecourse #learnjapaneseonline #japaneseanime #studyjapanese",
    "Pronunciation matters! 🎌 A few simple adjustments to your vowel length and rhythm will transform how easily native Japanese speakers understand you. Practice along with the video and notice the difference. Follow Velocity Japanese for daily Japanese lessons! #japanesepronunciation #learnjapanese #japanesephrase #velocityjapanese #japanesevocabulary #nihongobenkyou #japanesegrammar #studyjapanese",
    "Ready to travel to Japan with confidence? ✈️ From buying shinkansen tickets to checking into hotels, these travel Japanese phrases have got you covered. Bookmark this video so you can review before your trip! Like & follow Velocity Japanese for daily tips. #japantravel #tokyotravel #learnjapanese #japaneselesson #velocityjapanese #japanlife #visitjapan #nihongo #japanesestudent",
    "Understanding the difference between polite (keigo/teineigo) and casual (tameguchi) Japanese is crucial for making great impressions. 🌸 Here is a clear, simple breakdown so you always know when to use each form comfortably. What Japanese topic would you like us to cover next? #japanesegrammar #learnjapanese #keigo #velocityjapanese #japaneselessons #japaneselanguage #studyjapanese #nihongo #dailyjapanese",
    "Counting objects in Japanese can seem tricky with different counters, but this quick method makes it effortless! 🔢 Watch till the end to see the most common counters used in everyday life. Practice makes progress! #japanesecounters #japanesenumbers #learnjapanese #velocityjapanese #japanesevocabulary #nihongo #studynihongo #japaneselessons #japaneselearning",
    "Anime fans, this one is for you! 🎌 We break down the most popular Japanese catchphrases, battle cries, and emotional lines heard across iconic anime series—along with their real-world usage. Comment your favorite anime quote below! #animejapanese #learnjapanese #animelover #otaku #velocityjapanese #nihongo #japanesephrases #japaneseculture #japaneselesson",
    "Shopping in Shibuya or Ginza? 🛍️ Learn how to ask for your size, check colors, and ask about tax-free shopping without any stress. Tap the save button to keep these phrases handy. Follow Velocity Japanese for daily lessons! #japanshopping #learnjapanese #japaneselessons #velocityjapanese #nihongoclass #japantravel #shibuya #ginza #studyjapanese",
]


def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        if vname:
            counts[vname] = counts.get(vname, 0) + 1
    return counts


def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4, ensure_ascii=False)


def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")) + glob.glob(os.path.join(PROCESSED_DIR, "*.mov")))

    if specific_video:
        if os.path.exists(specific_video):
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"[publisher] Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"[publisher] Error: Specific video {name} not found")
            return None, None

    # Unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]
    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # Repost mode with weighted random selection
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"[publisher] All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None


def generate_caption():
    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    if not api_key:
        chosen_title = random.choice(FALLBACK_TITLES)
        chosen_desc = random.choice(FALLBACK_DESCRIPTIONS)
        print("[publisher] Warning: POLLINATIONS_API_KEY not found. Using fallback Japanese captions.")
        return chosen_title, chosen_desc

    vibes = [
        "educational and energetic - focus on daily Japanese phrases, pronunciation, and vocabulary building",
        "fun and conversational - explain practical expressions used by native Japanese speakers",
        "travel & cultural - highlight how to use Japanese in everyday situations in Japan (restaurants, trains, shopping)",
        "motivational and inspiring - encourage learners that Japanese is accessible and fun to master daily",
        "quick tip & bite-sized - breakdown a specific grammar point or vocabulary nuance clearly",
    ]
    chosen_vibe = random.choice(vibes)

    format_example = '{"title": "<title>", "description": "<description>"}'
    prompt = (
        f"Write a completely unique, engaging, and captivating title and description for a short vertical video (Reel) "
        f"about learning Japanese for the Facebook page '{PAGE_NAME}'.\n"
        f"The channel helps English speakers master conversational Japanese, vocabulary, pronunciation, kanji, and cultural insights.\n"
        f"Tone/Vibe: {chosen_vibe}.\n"
        f"Requirements:\n"
        f"- The title should be punchy and enticing (including relevant emojis and Japanese characters when appropriate).\n"
        f"- The description should be 3-5 sentences long, encouraging, and clear.\n"
        f"- Include clear engagement calls to action (e.g. Save this reel for later, Comment your favorite phrase below, Follow {PAGE_NAME} for daily lessons).\n"
        f"- Include relevant hashtags in ALL LOWERCASE: #japanese #learnjapanese #japaneselanguage #nihongo #japaneselesson #velocityjapanese #kanji #japanesevocabulary #dailyjapanese #speakjapanese #studyjapanese #japantravel.\n"
        f"Return ONLY a valid JSON object in this exact format: {format_example}\n"
        f"Do not include any other markdown backticks or commentary."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
        title = result.get("title", random.choice(FALLBACK_TITLES))
        desc = result.get("description", random.choice(FALLBACK_DESCRIPTIONS))
        return title, desc
    except Exception as e:
        print(f"[publisher] Error generating caption with Pollinations AI: {e}")
        return random.choice(FALLBACK_TITLES), random.choice(FALLBACK_DESCRIPTIONS)


def main():
    print("=" * 60)
    print(f"DAILY AUTOMATION STARTING - {PAGE_NAME.upper()}")
    print("=" * 60)

    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("[publisher] No video found to publish. Exiting.")
        return

    print(f"[publisher] Selected Video: {video_name}")
    print("[publisher] Generating caption via Pollinations AI...")
    title, description = generate_caption()

    print(f"[publisher] Title: {title}")
    print(f"[publisher] Description:\n{description}")

    success_flags = {
        "facebook_reel": False,
        "facebook_story": False,
        "instagram_reel": False,
        "instagram_story": False,
        "threads": False,
    }

    # 1. Facebook Reel
    if upload_to_facebook:
        try:
            result = upload_to_facebook(video_path, description, title=title)
            if result and result.get('status') == 'skipped':
                print(f"[publisher] Facebook Reel: Skipped ({result.get('reason')})")
            elif result and result.get('status') == 'success':
                success_flags["facebook_reel"] = True
        except Exception as e:
            print(f"[publisher] Facebook Reel upload failed: {e}")
    else:
        print("[publisher] upload_to_facebook module not available")

    # 2. Facebook Story
    if upload_to_facebook_story:
        try:
            result = upload_to_facebook_story(video_path)
            if result and result.get('status') == 'skipped':
                print(f"[publisher] Facebook Story: Skipped ({result.get('reason')})")
            elif result and result.get('status') == 'success':
                success_flags["facebook_story"] = True
        except Exception as e:
            print(f"[publisher] Facebook Story upload failed: {e}")

    # 3. Instagram Reels & Stories
    if upload_to_instagram:
        combined_caption = f"{title}\n\n{description}\n\n🌐 Visit {WEBSITE_URL} for daily Japanese lessons!"
        try:
            res_ig = upload_to_instagram(video_path, combined_caption, is_story=False)
            if res_ig and res_ig.get('status') == 'success':
                success_flags["instagram_reel"] = True
        except Exception as e:
            print(f"[publisher] Instagram Reel upload failed: {e}")

        try:
            res_ig_story = upload_to_instagram(video_path, combined_caption, is_story=True)
            if res_ig_story and res_ig_story.get('status') == 'success':
                success_flags["instagram_story"] = True
        except Exception as e:
            print(f"[publisher] Instagram Story upload failed: {e}")

    # 4. Threads
    if upload_to_threads:
        try:
            th_text = f"{title}\n\n{description}\n\n🌐 {WEBSITE_URL}"
            res_th = upload_to_threads(video_path, text=th_text)
            if res_th and res_th.get('status') == 'success':
                success_flags["threads"] = True
        except Exception as e:
            print(f"[publisher] Threads upload failed: {e}")

    # Record publication in log
    if success_flags["facebook_reel"]:
        metadata = {
            "title": title,
            "description": description,
            "platforms": success_flags,
            "website": WEBSITE_URL
        }
        mark_as_published(video_name, metadata)
        print(f"\n[publisher] ✅ SUCCESS! Video published to Facebook Reel and marked in {PUBLISHED_LOG}")
        print("=" * 60)
        print(f"PUBLISHING PIPELINE COMPLETE - {PAGE_NAME}")
        print("=" * 60)
    else:
        print("\n" + "!" * 60)
        print("[publisher] ❌ FACEBOOK UPLOAD DID NOT SUCCEED!")
        print("[publisher] Video has NOT been marked as published.")
        print("[publisher] To publish to the Velocity Japanese Facebook page, ensure both:")
        print("  - FACEBOOK_PAGE_ID")
        print("  - FACEBOOK_ACCESS_TOKEN")
        print("are configured in GitHub Repository Secrets at:")
        print("  https://github.com/eternityrage/vel-jap-vids/settings/secrets/actions")
        print("!" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
