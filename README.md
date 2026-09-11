# vel-jap-vids 🇯🇵

Automated Japanese Video Publishing Pipeline for **Velocity Japanese**.

This repository automatically fetches Japanese learning videos from Google Drive, enhances them with FFmpeg (1080x1920 vertical video + audio loudness normalization), generates Japanese learning titles and descriptions via Pollinations AI (with rich fallback captions), and posts them as Facebook Reels with a pinned comment linking to [velocityjapanese.com](https://velocityjapanese.com).

## 🚀 Key Features

- **Google Drive Integration**: Fetches video files from Google Drive folder `1o2ntZzxWTogxmK43rPt9Hx1kEzMjLdRf` using Google Service Account.
- **Auto Repost Fallback**: Once all videos from Google Drive have been published, the system automatically transitions into a weighted random repost mode prioritizing videos with the fewest previous posts.
- **FFmpeg Enhancement**:
  - Automatically loops videos of 6 seconds or less 2 times to ~12 seconds (6s + 6s = 12s).
  - Scales to 1080x1920 with high quality Lanczos filter and sharpening.
  - Normalizes audio loudness for crisp voice clarity.
- **Pollinations AI Japanese Captions**: Generates bilingual titles and descriptions for Japanese learners with vocabulary, grammar tips, and engagement calls-to-action.
- **Facebook Reels & Pinned Comment**:
  - Posts Reel to Facebook Page **Velocity Japanese** via Facebook Graph API v21.0.
  - Automatically posts and pins the top comment:
    ```
    🌐 Learn more at our website: https://velocityjapanese.com
    Visit velocityjapanese.com for daily Japanese lessons!
    ```
  - Posts to Facebook Story.
- **Automated Workflow**: Runs 3x daily via GitHub Actions schedule (`0 3 * * *`, `0 11 * * *`, `0 19 * * *`) and on-demand via `workflow_dispatch`.
- **Skip CI Commit**: Automatically commits and pushes `published_videos.json` back to GitHub.

---

## 🔑 GitHub Actions Secrets

Add the following secrets to repository **Settings -> Secrets and variables -> Actions**:

| Secret Name | Description | Default / Example |
|---|---|---|
| `GOOGLE_DRIVE_FOLDER_ID` | Google Drive folder ID | `1o2ntZzxWTogxmK43rPt9Hx1kEzMjLdRf` |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Google Service Account JSON string | `{"type": "service_account", ...}` |
| `FACEBOOK_PAGE_ID` | Facebook Page ID for Velocity Japanese | e.g. `1000832145...` |
| `FACEBOOK_ACCESS_TOKEN` | Page Access Token with `pages_read_engagement`, `pages_manage_posts` | `EAA...` |
| `POLLINATIONS_API_KEY` | Pollinations AI API Key | `sk_...` |

---

## 🛠️ Local Development & Testing

1. Clone repository:
   ```bash
   git clone https://github.com/eternityrage/vel-jap-vids.git
   cd vel-jap-vids
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` from `.env.example`:
   ```bash
   cp .env.example .env
   # Add your Google Drive and Facebook Page credentials
   ```

4. Run pipeline:
   ```bash
   python auto_pipeline.py
   ```
