# random.exe

> A minimal YouTube video downloader with a clean interface, video previews, and download progress tracking.

`random.exe` is a self-hosted web application built with Python, Flask, JavaScript, and CSS. Paste a YouTube URL, preview the video information, and download the video directly through your browser.

## ✨ Features

- 🎬 Fetch video titles, thumbnails, durations, and channel names.
- ⬇️ Download videos in the best available video and audio quality.
- 📊 Track download progress in real time.
- 🔗 Support standard YouTube links, Shorts, live URLs, and shortened `youtu.be` links.
- 🍪 Optional YouTube cookies support for videos that require an authenticated session.
- 🖥️ Simple web interface powered by Flask and vanilla JavaScript.
- 🔒 Run locally on your own computer.

## 🧰 Requirements

Before getting started, make sure you have:

- [Python](https://www.python.org/downloads/) installed.
- [Git](https://git-scm.com/downloads) (optional, for cloning the repository).
- [FFmpeg](https://ffmpeg.org/download.html) recommended for merging separate video and audio streams.
- A Chromium-based browser, such as Chrome or Edge, if you need to export cookies.
- Your own `cookies.txt` file only if the videos you want to access require it.

## 🚀 Installation

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd YOUR_REPOSITORY_NAME
```

Alternatively, download the repository as a ZIP file and extract it.

### 2. Install the dependencies

Open a terminal inside the project folder and run:

```bash
python -m venv .venv
```

Activate the virtual environment.

**Windows:**

```powershell
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

Install the required Python packages:

```bash
python -m pip install flask yt-dlp
```

### 3. Set up cookies (optional)

Some videos may require authentication. If you encounter access errors, you can export your own YouTube cookies and place the resulting file in the project root.

See [How to Get Your Own `cookies.txt`](#-how-to-get-your-own-cookiestxt) below.

**Important:** You do not need to upload your cookies to GitHub or send them to anyone.

### 4. Start the application

Run:

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

Keep the terminal open while using the application.

## 🍪 How to Get Your Own `cookies.txt`

Only export cookies from your own browser session and account. Cookies can contain authentication credentials that may allow someone else to access your account.

### Step 1 — Install the extension

Install the **Get cookies.txt LOCALLY** extension from the official Chrome Web Store or the corresponding official browser extension store.

Search for:

`Get cookies.txt LOCALLY`

Check the extension's publisher and permissions before installing it. Avoid unofficial copies.

### Step 2 — Open YouTube

1. Open [YouTube](https://www.youtube.com/).
2. Sign in to your own account if authentication is needed.
3. Make sure YouTube is open in the same browser where you installed the extension.

### Step 3 — Export the cookies

1. While on YouTube, click the extension icon in your browser toolbar.
2. If necessary, open the extensions menu and select the cookie-export extension.
3. Follow its instructions to export cookies for the current YouTube site.
4. Save the exported file as `cookies.txt`.

The extension's exact interface may vary by version.

### Step 4 — Put the file in the project folder

Your local project should look something like this:

```text
random.exe/
├── app.py
├── app.js
├── style.css
├── templates/
│   └── index.html
├── cookies.txt          # Local only — never publish
└── .gitignore
```

The Flask application looks for `cookies.txt` in its working directory. If the file exists there, `yt-dlp` will use it automatically.

If YouTube still rejects the request, the cookies may be expired or the video may require another form of access. Exporting cookies does not guarantee that every video will work.

## 🔐 Keep Your Cookies Private

**Never commit `cookies.txt` to a public repository.** It may contain session cookies that can compromise your Google or YouTube account.

Create a `.gitignore` file in the project root and add:

```gitignore
# Authentication cookies — never publish
cookies.txt
*.cookies.txt

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Local environment files
.env
.env.*
!.env.example
```

If `cookies.txt` was already tracked by Git, adding it to `.gitignore` is not enough. Remove it from Git's tracking with:

```bash
git rm --cached cookies.txt
git add .gitignore
git commit -m "Stop tracking sensitive cookies"
```

This does not erase copies from earlier commits. If you already pushed real cookies publicly, treat them as compromised: revoke the affected sessions where possible, review your Google account security, and clean the repository's history before republishing.

**Never ask other users to send you their cookie files.** Each user should keep their own export on their own machine.

## 🗂️ Project Structure

| File | Purpose |
|---|---|
| `app.py` | Flask backend, video information extraction, download jobs, and progress endpoints |
| `app.js` | Frontend interactions, video preview, and progress updates |
| `style.css` | Application styling |
| `templates/index.html` | HTML page rendered by Flask |
| `cookies.txt` | Optional local authentication cookies; must remain private |
| `.gitignore` | Prevents sensitive and unnecessary files from being committed |

## 🛠️ Troubleshooting

**Video information cannot be fetched**
- Check that the URL is valid.
- Update `yt-dlp`:

  ```bash
  python -m pip install -U yt-dlp
  ```

- Some videos may be restricted or unavailable.

**Download fails or audio is missing**
- Install FFmpeg and ensure it is available in your system's PATH.
- Check the error displayed in the application or terminal.
- If authentication is required, verify that your local cookies are valid.

**The cookies file is not being detected**
- Make sure the filename is exactly `cookies.txt`.
- Place it in the directory from which you run `app.py`.
- Never solve this by uploading your personal cookies to a public repository.

## ⚠️ Disclaimer

This project is intended for personal use and educational purposes. Only download content you have permission to download, and respect copyright, applicable laws, and YouTube's terms of service.

This project is not affiliated with, endorsed by, or sponsored by YouTube or Google.

---

Made with Python, JavaScript, and a little bit of chaos.

**random.exe**
