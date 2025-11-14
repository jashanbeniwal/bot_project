import json
from pyrogram import filters
from utils.buttons import mk_buttons
from utils.database import read_settings, update_settings

def register_handlers(app):
    @app.on_message(filters.command("settings") & filters.private)
    async def settings_cmd(_, msg):
        s = await read_settings(msg.from_user.id)
        await msg.reply_text(f"Your settings:\n{s}\nUse /set to update (scaffold)")

    @app.on_message(filters.command("set") & filters.private)
    async def set_cmd(_, msg):
        # scaffold: expect JSON body with settings
        try:
            body = msg.text.partition(" ")[2]
            js = json.loads(body)
            await update_settings(msg.from_user.id, json.dumps(js))
            await msg.reply_text("Settings saved.")
        except Exception as e:
            await msg.reply_text("Provide valid JSON. Example:\n/set {\"upload_mode\":\"stream\",\"quality\":\"128k\"}")
