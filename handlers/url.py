import os
import asyncio
from pyrogram import filters
from utils.buttons import mk_buttons
from yt_dlp import YoutubeDL

def register_handlers(app, job_queue):
    @app.on_message(filters.regex(r"^https?://") & filters.private)
    async def on_url(_, msg):
        kb = mk_buttons([[("Download", f"url_dl:{msg.message_id}")], [("Unshorten", f"url_unshort:{msg.message_id}")]])
        await msg.reply_text("URL options:", reply_markup=kb)

    @app.on_callback_query(filters.regex(r"url_dl:(\d+)"))
    async def cb_url_dl(c, cb):
        msg_id = int(cb.data.split(":")[1])
        orig = await cb.message.chat.get_messages(msg_id)
        url = orig.text.strip()
        await cb.message.edit_text("Downloading via yt-dlp...")
        # basic yt-dlp download to /tmp
        opts = {
            'outtmpl': 'tmp/%(id)s.%(ext)s',
            'quiet': True,
        }
        loop = asyncio.get_event_loop()
        def run_ytdl():
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info
        info = await loop.run_in_executor(None, run_ytdl)
        # find file
        path = None
        if info:
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                path = filename
        # fallback: search tmp
        for f in os.listdir("tmp"):
            if os.path.isfile(os.path.join("tmp", f)):
                path = os.path.join("tmp", f)
                break
        if path:
            await cb.message.reply_document(path)
        else:
            await cb.message.edit_text("Download failed.")
