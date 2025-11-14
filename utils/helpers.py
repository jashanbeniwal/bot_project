import os
import uuid
import tempfile
import shutil
import asyncio
from contextlib import asynccontextmanager

def make_user_tmpdir(user_id: int):
    base = os.path.abspath("tmp")
    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, f"user_{user_id}")
    os.makedirs(path, exist_ok=True)
    return path

def cleanup_user_tmpdir(user_id: int):
    path = os.path.join("tmp", f"user_{user_id}")
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

@asynccontextmanager
async def user_temp_dir(user_id: int):
    path = make_user_tmpdir(user_id)
    try:
        yield path
    finally:
        # cleanup asynchronously
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass

async def progress_text_to_percent(line: str):
    # Very simple parser — you can expand to parse time/frame/bitrate etc.
    if "time=" in line:
        # crude; not used for accurate ETA
        return {"line": line}
    return None
