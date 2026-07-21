import os
import re
import tempfile
from pathlib import Path

import requests
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Put your new bot token here or set BOT_TOKEN in Pydroid environment
BOT_TOKEN = os.getenv("8926384344:AAHodT2wOaUfOdGxQWYoSxKRky-C1M2R5BA")

# Optional Terabox cookie.
# Some Terabox links work better with a valid cookie.
TERABOX_COOKIE = os.getenv("TERABOX_COOKIE", "")

DOWNLOAD_ROOT = Path(tempfile.gettempdir()) / "tg_downloader_bot"
DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)


def is_terabox_url(url: str) -> bool:
    url = url.lower()
    return any(domain in url for domain in ("terabox", "1024tera", "teraboxapp", "terabox.app"))


def safe_filename(name: str, default: str = "download") -> str:
    name = name.strip() or default
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name[:180]


async def send_downloaded_file(update: Update, file_path: Path, as_video: bool = False):
    with file_path.open("rb") as fp:
        if as_video and file_path.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}:
            await update.message.reply_video(fp)
        else:
            await update.message.reply_document(fp)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a YouTube, Instagram Reel/Post, or Terabox URL."
    )


async def download_from_terabox(update: Update, url: str):
    # Package docs: from TeraboxDL import TeraboxDL
    from TeraboxDL import TeraboxDL

    await update.message.reply_text("📦 Terabox link detect hua. Info nikal raha hoon...")

    terabox = TeraboxDL(TERABOX_COOKIE)
    file_info = terabox.get_file_info(url, direct_url=True)

    if not isinstance(file_info, dict) or "error" in file_info:
        err = file_info.get("error", "Terabox file info not found") if isinstance(file_info, dict) else "Terabox error"
        await update.message.reply_text(f"❌ Terabox error:\n{err}")
        return

    download_url = file_info.get("download_link")
    file_name = safe_filename(file_info.get("file_name", "terabox_file"))
    if not download_url:
        await update.message.reply_text("❌ Terabox download link nahi mila.")
        return

    suffix = Path(file_name).suffix or ".mp4"
    temp_path = DOWNLOAD_ROOT / f"{file_name if file_name.endswith(suffix) else file_name + suffix}"

    await update.message.reply_text("⏳ Terabox file download ho rahi hai...")

    with requests.get(download_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with temp_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)

    await update.message.reply_text("📤 Sending file...")
    await send_downloaded_file(update, temp_path, as_video=True)

    try:
        temp_path.unlink(missing_ok=True)
    except Exception:
        pass


async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = (update.message.text or "").strip()
    if not url:
        return

    try:
        if is_terabox_url(url):
            await download_from_terabox(update, url)
            return

        await update.message.reply_text("⏳ Downloading...")

        ydl_opts = {
    "format": "bv*+ba/b",
    "merge_output_format": "mp4",
    "outtmpl": "%(title)s.%(ext)s",
    "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = Path(ydl.prepare_filename(info))

        await update.message.reply_text("📤 Sending file...")
        await send_downloaded_file(update, filename, as_video=True)

        try:
            filename.unlink(missing_ok=True)
        except Exception:
            pass

    except Exception as e:
        await update.message.reply_text(f"❌ Error:\n{e}")


app = Application.builder().token("8926384344:AAHodT2wOaUfOdGxQWYoSxKRky-C1M2R5BA").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

print("Bot Running...")
app.run_polling()
