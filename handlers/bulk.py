from pyrogram import filters
from utils.buttons import mk_buttons

def register_handlers(app, job_queue):
    @app.on_message(filters.command("bulk") & filters.private)
    async def bulk_start(_, msg):
        await msg.reply_text("Bulk mode: send multiple files and then /done to process them (scaffold).")

    @app.on_message(filters.command("done") & filters.private)
    async def bulk_done(_, msg):
        await msg.reply_text("Queued bulk job (scaffold). Job queue will process files in background.")
        # TODO: complete implementation: collect user files, add a coroutine job to job_queue
