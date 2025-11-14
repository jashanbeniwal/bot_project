import os
import asyncio
from pyrogram import filters
from pyrogram.types import Message
from utils.buttons import mk_buttons
from utils.helpers import user_temp_dir
from utils.ffmpeg import run_ffmpeg
from utils.database import get_or_create_user

# Register handlers using a function to keep main.py clean
def register_handlers(app, job_queue):
    @app.on_message(filters.video & filters.private)
    async def on_video(client: app.__class__, message: Message):
        user_id = message.from_user.id
        await get_or_create_user(user_id)
        # present inline menu with features
        kb = mk_buttons([
            [("Remove Audio", f"v_remove_audio:{message.message_id}"), ("Extract Audio", f"v_extract_audio:{message.message_id}")],
            [("Trim", f"v_trim:{message.message_id}"), ("Convert", f"v_convert:{message.message_id}")],
            [("GIF", f"v_gif:{message.message_id}"), ("Screenshots", f"v_screenshots:{message.message_id}")],
            [("More…", f"v_more:{message.message_id}")]
        ])
        await message.reply_text("Choose a video action:", reply_markup=kb)

    # Callback handlers
    @app.on_callback_query(filters.regex(r"v_remove_audio:(\d+)"))
    async def cb_remove_audio(c, cb):
        orig_msg_id = int(cb.data.split(":")[1])
        # get original message by id in same chat
        try:
            orig = await cb.message.chat.get_messages(orig_msg_id)
        except Exception:
            await cb.answer("Original message not found", show_alert=True)
            return
        # download video
        user_id = cb.from_user.id
        async with user_temp_dir(user_id) as tmp:
            in_path = os.path.join(tmp, "in_video")
            await orig.download(file_name=in_path)
            out_path = os.path.join(tmp, "out.mp4")
            # ffmpeg: copy video stream, drop audio
            cmd = f"-y -i {in_path} -c copy -an {out_path}"
            await cb.message.edit_text("Removing audio...")
            rc = await run_ffmpeg(cmd)
            if rc == 0 and os.path.exists(out_path):
                await cb.message.reply_document(out_path, caption="Audio removed")
                await cb.message.delete()
            else:
                await cb.answer("Failed to remove audio", show_alert=True)

    @app.on_callback_query(filters.regex(r"v_extract_audio:(\d+)"))
    async def cb_extract_audio(c, cb):
        orig_msg_id = int(cb.data.split(":")[1])
        orig = await cb.message.chat.get_messages(orig_msg_id)
        user_id = cb.from_user.id
        async with user_temp_dir(user_id) as tmp:
            in_path = os.path.join(tmp, "in_video")
            await orig.download(file_name=in_path)
            out_path = os.path.join(tmp, "audio.mp3")
            # extract best audio & convert to mp3
            cmd = f"-y -i {in_path} -vn -acodec libmp3lame -q:a 2 {out_path}"
            await cb.message.edit_text("Extracting audio...")
            rc = await run_ffmpeg(cmd)
            if rc == 0 and os.path.exists(out_path):
                await cb.message.reply_audio(out_path, caption="Extracted audio")
                await cb.message.delete()
            else:
                await cb.answer("Failed to extract audio", show_alert=True)

    @app.on_callback_query(filters.regex(r"v_trim:(\d+)"))
    async def cb_trim(c, cb):
        # simple trim flow: ask user to reply with start-end seconds
        orig_msg_id = int(cb.data.split(":")[1])
        await cb.message.edit_text("Reply to this message with `start_seconds end_seconds` (e.g. `12 45`) to trim.")
        # Wait for response (simplified)
        def check(m):
            return m.from_user.id == cb.from_user.id and m.chat.id == cb.message.chat.id and m.text
        try:
            resp = await app.listen(cb.message.chat.id, check=check, timeout=60)
        except asyncio.TimeoutError:
            await cb.message.edit_text("Timeout waiting for trim times.")
            return
        parts = resp.text.strip().split()
        if len(parts) < 2:
            await resp.reply_text("Invalid. Provide start and end seconds.")
            return
        start, end = parts[0], parts[1]
        orig = await cb.message.chat.get_messages(orig_msg_id)
        user_id = cb.from_user.id
        async with user_temp_dir(user_id) as tmp:
            in_path = os.path.join(tmp, "in.mp4")
            await orig.download(file_name=in_path)
            out_path = os.path.join(tmp, "trim.mp4")
            cmd = f"-y -i {in_path} -ss {start} -to {end} -c copy {out_path}"
            await resp.reply_text("Trimming...")
            rc = await run_ffmpeg(cmd)
            if rc == 0 and os.path.exists(out_path):
                await resp.reply_video(out_path)
            else:
                await resp.reply_text("Trim failed.")

    @app.on_callback_query(filters.regex(r"v_convert:(\d+)"))
    async def cb_convert(c, cb):
        orig_msg_id = int(cb.data.split(":")[1])
        orig = await cb.message.chat.get_messages(orig_msg_id)
        await cb.message.edit_text("Choose format:")
        kb = mk_buttons([[("MP4", f"v_conv_do:{orig_msg_id}:mp4"), ("MKV", f"v_conv_do:{orig_msg_id}:mkv")]])
        await cb.message.edit_reply_markup(reply_markup=kb)

    @app.on_callback_query(filters.regex(r"v_conv_do:(\d+):([a-z0-9]+)"))
    async def cb_conv_do(c, cb):
        parts = cb.data.split(":")
        orig_msg_id = int(parts[1]); fmt = parts[2]
        orig = await cb.message.chat.get_messages(orig_msg_id)
        user_id = cb.from_user.id
        async with user_temp_dir(user_id) as tmp:
            in_path = os.path.join(tmp, "in")
            await orig.download(file_name=in_path)
            out_path = os.path.join(tmp, f"out.{fmt}")
            cmd = f"-y -i {in_path} -c:v libx264 -preset fast -c:a aac -b:a 128k {out_path}"
            await cb.message.edit_text(f"Converting to {fmt}...")
            rc = await run_ffmpeg(cmd)
            if rc == 0 and os.path.exists(out_path):
                await cb.message.reply_document(out_path, caption=f"Converted to {fmt}")
            else:
                await cb.answer("Convert failed", show_alert=True)

    @app.on_callback_query(filters.regex(r"v_gif:(\d+)"))
    async def cb_gif(c, cb):
        orig_msg_id = int(cb.data.split(":")[1])
        orig = await cb.message.chat.get_messages(orig_msg_id)
        user_id = cb.from_user.id
        async with user_temp_dir(user_id) as tmp:
            in_path = os.path.join(tmp, "in.mp4")
            await orig.download(file_name=in_path)
            out_path = os.path.join(tmp, "out.gif")
            # convert to gif (basic)
            cmd = f"-y -i {in_path} -vf fps=12,scale=640:-1:flags=lanczos -loop 0 {out_path}"
            await cb.message.edit_text("Converting to GIF...")
            rc = await run_ffmpeg(cmd)
            if rc == 0 and os.path.exists(out_path):
                await cb.message.reply_document(out_path, caption="GIF")
            else:
                await cb.answer("GIF conversion failed", show_alert=True)

    @app.on_callback_query(filters.regex(r"v_screenshots:(\d+)"))
    async def cb_screenshots(c, cb):
        # produce N screenshots evenly spaced
        orig_msg_id = int(cb.data.split(":")[1])
        orig = await cb.message.chat.get_messages(orig_msg_id)
        await cb.message.edit_text("Reply with number of screenshots (eg. 3)")
        try:
            resp = await app.listen(cb.message.chat.id, timeout=30)
        except asyncio.TimeoutError:
            await cb.message.edit_text("Timeout.")
            return
        try:
            n = int(resp.text.strip())
        except:
            await resp.reply_text("Invalid number.")
            return
        user_id = cb.from_user.id
        async with user_temp_dir(user_id) as tmp:
            in_path = os.path.join(tmp, "in.mp4")
            await orig.download(file_name=in_path)
            # get duration using ffprobe (quick way using ffmpeg - we will approximate)
            # here we generate shots at 10%,30%,60% etc. (simple)
            out_files = []
            for i in range(n):
                t = (i+1) * 10  # crude sample times in seconds — you can compute duration
                outf = os.path.join(tmp, f"shot_{i}.jpg")
                cmd = f"-y -ss {t} -i {in_path} -frames:v 1 {outf}"
                await run_ffmpeg(cmd)
                if os.path.exists(outf):
                    out_files.append(outf)
            if out_files:
                for f in out_files:
                    await cb.message.reply_photo(f)
            else:
                await cb.answer("Screenshots failed", show_alert=True)

    # v_more placeholder menu
    @app.on_callback_query(filters.regex(r"v_more:(\d+)"))
    async def cb_more(c, cb):
        await cb.message.edit_text("More features coming. Use /settings to customize default behaviour.")
