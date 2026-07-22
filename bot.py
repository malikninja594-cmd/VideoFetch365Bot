import telebot
import yt_dlp
import os

# Apna Telegram Bot Token yahan dalein (BotFather se milega)
BOT_TOKEN = '8926384344:AAHodT2wOaUfOdGxQWYoSxKRky-C1M2R5BA'
bot = telebot.TeleBot("8926384344:AAHodT2wOaUfOdGxQWYoSxKRky-C1M2R5BA")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Hello! Main ek Video Downloader Bot hoon.\n\n"
        "Mujhe **YouTube** ya **Instagram** ka video/reel link bhejein, "
        "aur main use download karke aapko bhej dunga."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    # Check karein ki message mein URL hai ya nahi
    if not url.startswith("http://") and not url.startswith("https://"):
        bot.reply_to(message, "⚠️ Kripya ek valid YouTube ya Instagram ka link bhejein.")
        return

    bot.reply_to(message, "⏳ Video download ho rahi hai, kripya thoda intezaar karein...")

    try:
        # yt-dlp ki settings
        ydl_opts = {
            'format': 'best', # Best quality download karega
            'outtmpl': 'downloaded_video_%(id)s.%(ext)s', # File ka naam
            'max_filesize': 50000000, # Telegram bot ki limit 50MB hoti hai
            'noplaylist': True,
            'quiet': True
        }

        # Video download karna
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Telegram par video send karna
        with open(filename, 'rb') as video_file:
            bot.send_video(message.chat.id, video_file, caption="🎬 Yeh lijiye aapki video!")

        # Send hone ke baad local file ko delete kar dena taaki space bache
        os.remove(filename)

    except yt_dlp.utils.DownloadError as e:
        bot.reply_to(message, "❌ Download fail ho gaya. Ho sakta hai video **50MB se badi** ho, private ho, ya link invalid ho.")
        print(f"Download Error: {e}")
    except Exception as e:
        bot.reply_to(message, "❌ Ek error aagaya. Kripya baad mein try karein.")
        print(f"Error: {e}")

# Bot ko lagatar chalane ke liye
print("Bot is running...")
bot.infinity_polling()