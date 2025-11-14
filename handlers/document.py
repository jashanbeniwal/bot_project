import os
import shutil
from pyrogram import filters
from utils.buttons import mk_buttons
from utils.helpers import user_temp_dir
import zipfile

def register_handlers(app, job_queue):
    @app.on_message(filters.document & filters.private)
    async def on_doc(_, msg):
        kb = mk_buttons([
            [("Rename", f"d_rename:{msg.message_id}"), ("Archive", f"d_archive:{msg.message_id}")],
            [("Extract Archive", f"d_extract:{msg.message_id}"), ("Format JSON", f"d_json:{msg.message_id}")]
        ])
        await msg.reply_text("Document options:", reply_markup=kb)

    @app.on_callback_query(filters.regex(r"d_rename:(\d+)"))
    async def cb_rename(c, cb):
        msg_id = int(cb.data.split(":")[1])
        await cb.message.edit_text("Reply with new filename (with extension).")
        try:
            resp = await app.listen(cb.message.chat.id, timeout=30)
        except:
            await cb.message.edit_text("Timeout.")
            return
        orig = await cb.message.chat.get_messages(msg_id)
        user_id = cb.from_user.id
        async with user_temp_dir(user_id) as tmp:
            in_path = os.path.join(tmp, "in")
            await orig.download(file_name=in_path)
            newname = resp.text.strip()
            out = os.path.join(tmp, newname)
            shutil.move(in_path, out)
            await resp.reply_document(out, caption=f"Renamed to {newname}")

    @app.on_callback_query(filters.regex(r"d_archive:(\d+)"))
    async def cb_archive(c, cb):
        msg_id = int(cb.data.split(":")[1])
        orig = await cb.message.chat.get_messages(msg_id)
        user_id = cb.from_user.id
        async with user_temp_dir(user_id) as tmp:
            in_path = os.path.join(tmp, "in")
            await orig.download(file_name=in_path)
            archive = os.path.join(tmp, "pack.zip")
            with zipfile.ZipFile(archive, "w") as zf:
                zf.write(in_path, os.path.basename(in_path))
            await cb.message.reply_document(archive, caption="Archive created")
