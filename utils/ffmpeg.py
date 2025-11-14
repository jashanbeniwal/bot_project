import asyncio
import shlex
import os
from utils.helpers import read_stream_and_report

async def run_ffmpeg(cmd: str, input_path=None, output_path=None, progress_callback=None, timeout=None):
    """
    Run ffmpeg command asynchronously.
    cmd: full ffmpeg command string (not including 'ffmpeg')
    progress_callback: coroutine that accepts a single dict with progress info
    """
    full_cmd = ["ffmpeg", *shlex.split(cmd)]
    proc = await asyncio.create_subprocess_exec(
        *full_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE
    )

    # Read stderr to detect progress lines (ffmpeg writes progress to stderr)
    async def reader(stream):
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode(errors="ignore").strip()
            if progress_callback:
                await progress_callback(text)
        return

    readers = [reader(proc.stderr), reader(proc.stdout)]
    await asyncio.gather(*readers)
    await proc.wait()
    return proc.returncode
