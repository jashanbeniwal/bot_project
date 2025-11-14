import os
import asyncio
from pyrogram import filters
from utils.buttons import mk_buttons
from utils.helpers import user_temp_dir
from utils.ffmpeg import run_ffmpeg

def register_handlers(app, job_queue):
    @app.on_message(filters.audio & filters.private)
    async def on_audio(_, msg):
        kb = mk_buttons([
            [("Convert", f"a_convert:{msg.message_id}"), ("Trim", f"a_trim:{msg.message_id}")],
            [("Slowed+Reverb", f"a_slow:{msg.message_id}"), ("8D", f"a_8d:{msg.message_id}")],
            [("More…", f"a_more:{msg.message_id}")]
        ])
        await msg.reply_text("Audio actions:", reply_markup=kb)

    @app.on_callback_query(filters.regex(r"a_convert:(\d+)"))
    async def cb_a_convert(c, cb):
        msg_id = int(cb.data.split(":")[1])
        orig = await cb.message.chat.get_messages(msg_id)
        await cb.message.edit_text("Choose output format")
        kb = mk_buttons([[("MP3", f"a_conv_do:{msg_id}:mp3"), ("WAV", f"a_conv_do:{msg_id}:wav")]])
        await cb.message.edit_reply_markup(reply_markup=kb)

    @app.on_callback_query(filters.regex(r"a_conv_do:(\d+):([a-z0-9]+)"))
    async def cb_a_conv_do(c, cb):
        parts = cb.data.split(":")
        msg_id = int(parts[1]); fmt = parts[2]
        orig = await cb.message.chat.get_messages(msg_id)
        user_id = cb.from_user.id
        from utils.helpers import user_temp_dir
        async with user_temp_dir(user_id) as tmp:
            in_path = os.path.join(tmp, "in")
            await orig.download(file_name=in_path)
            out_path = os.path.join(tmp, f"out.{fmt}")
            # basic convert
            cmd = f"-y -i {in_path} -vn -acodec pcm_s16le {out_path}" if fmt == "wav" else f"-y -i {in_path} -vn -acodec libmp3lame -q:a 2 {out_path}"
            await cb.message.edit_text("Converting...")
            rc = await run_ffmpeg(cmd)
            if rc == 0 and os.path.exists(out_path):
                await cb.message.reply_audio(out_path)
            else:
                await cb.answer("Conversion failed", show_alert=True)

    @app.on_callback_query(filters.regex(r"a_trim:(\d+)"))
    async def cb_a_trim(c, cb):
        msg_id = int(cb.data.split(":")[1])
        await cb.message.edit_text("Reply with `start end` seconds to trim.")
        try:
            resp = await app.listen(cb.message.chat.id, timeout=30)
        except asyncio.TimeoutError:
            await cb.message.edit_text("Timeout.")
            return
        parts = resp.text.strip().split()
        if len(parts) < 2:
            await resp.reply_text("Invalid.")
            return
        start, end = parts[0], parts[1]
        orig = await cb.message.chat.get_messages(msg_id)
        user_id = cb.from_user.id
        async with user_temp_dir(user_id) as tmp:
            in_path = os.path.join(tmp, "in")
            await orig.download(file_name=in_path)
            out_path = os.path.join(tmp, "out.mp3")
            cmd = f"-y -i {in_path} -ss {start} -to {end} -c copy {out_path}"
            await resp.reply_text("Trimming...")
            rc = await run_ffmpeg(cmd)
            if rc == 0 and os.path.exists(out_path):
                await resp.reply_audio(out_path)
            else:
                await resp.reply_text("Trim failed.")
