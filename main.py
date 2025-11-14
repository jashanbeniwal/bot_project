import os
import asyncio
import logging
from pyrogram import Client, filters
from utils.database import init_db, get_or_create_user
from handlers import video, audio, document, url, bulk, settings
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(levelname)s - %(message)s')

# Application wide asyncio queue for background tasks (bulk processing queue)
job_queue = asyncio.Queue()

app = Client(
    "media_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="."
)

# initialize DB and tables
@app.on_message(filters.command("start") & filters.private)
async def start(_, msg):
    await get_or_create_user(msg.from_user.id)
    await msg.reply_text("Hello! I'm your Media Tool Bot. Send a video, audio, document or URL to start.")

# Mount handlers - they internally register filters with `app`
video.register_handlers(app, job_queue)
audio.register_handlers(app, job_queue)
document.register_handlers(app, job_queue)
url.register_handlers(app, job_queue)
bulk.register_handlers(app, job_queue)
settings.register_handlers(app)

async def periodic_worker():
    # background worker checking job_queue and processing
    while True:
        job = await job_queue.get()
        try:
            await job()  # job is a coroutine
        except Exception as e:
            logging.exception("Job failed: %s", e)
        job_queue.task_done()

async def run():
    await init_db()
    # start background worker
    loop = asyncio.get_running_loop()
    loop.create_task(periodic_worker())
    await app.start()
    logging.info("Bot started")
    await idle()  # keep running
    await app.stop()

if __name__ == "__main__":
    # Use asyncio.run to control the lifecycle
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logging.info("Stopping...")
