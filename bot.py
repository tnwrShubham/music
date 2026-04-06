import asyncio
import os
import subprocess
from highrise import BaseBot, User, Position

song_queue = []
is_playing = False

ICECAST_PASSWORD = "yourpassword"
ICECAST_MOUNT = "/stream"
STREAM_URL = "https://musicbot-production-4746.up.railway.app:8000/stream"

class MusicBot(BaseBot):

    async def on_start(self, session_metadata):
        print("Bot started!")

    async def on_user_join(self, user: User, position: Position):
        await self.highrise.chat(f"👋 Welcome @{user.username}! Type !help for commands.")

    async def on_chat(self, user: User, message: str):
        global is_playing
        msg = message.strip().lower()

        if msg == "!help":
            await self.highrise.chat(
                "🎵 Commands:\n"
                "!sr [song] - request a song\n"
                "!skip - skip current song\n"
                "!np - now playing\n"
                "!queue - show queue\n"
                "!listen - get stream link"
            )

        elif msg == "!listen":
            await self.highrise.chat(f"🎧 Stream: {STREAM_URL}")

        elif msg.startswith("!sr "):
            song_name = message.strip()[4:]
            song_queue.append((song_name, user.username))
            await self.highrise.chat(f"🎶 Added: {song_name} by @{user.username}")
            if not is_playing:
                asyncio.create_task(self.play_next())

        elif msg == "!skip":
            if is_playing and hasattr(self, 'ffmpeg_proc') and self.ffmpeg_proc:
                self.ffmpeg_proc.terminate()
                await self.highrise.chat("⏭️ Skipped!")
            else:
                await self.highrise.chat("❌ Nothing playing.")

        elif msg == "!np":
            if is_playing and hasattr(self, 'current_song'):
                await self.highrise.chat(f"▶️ Now playing: {self.current_song}")
            else:
                await self.highrise.chat("❌ Nothing playing.")

        elif msg == "!queue":
            if not song_queue:
                await self.highrise.chat("Queue is empty!")
            else:
                lines = [f"#{i} {s} - @{r}" for i, (s, r) in enumerate(song_queue[:5], 1)]
                await self.highrise.chat("🎵 Queue:\n" + "\n".join(lines))

    async def play_next(self):
        global is_playing
        if not song_queue:
            is_playing = False
            await self.highrise.chat("✅ Queue finished!")
            return

        is_playing = True
        self.current_song, requester = song_queue.pop(0)
        await self.highrise.chat(f"▶️ Now playing: {self.current_song} (@{requester})")

        try:
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp", "-x", "--audio-format", "mp3",
                "-o", "/tmp/song.mp3",
                f"ytsearch1:{self.current_song}",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
        except Exception:
            await self.highrise.chat(f"❌ Failed to download: {self.current_song}")
            await self.play_next()
            return

        try:
            self.ffmpeg_proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-re", "-i", "/tmp/song.mp3",
                "-f", "mp3", "-content_type", "audio/mpeg",
                f"icecast://source:{ICECAST_PASSWORD}@localhost:8000{ICECAST_MOUNT}",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await self.ffmpeg_proc.wait()
        except Exception:
            await self.highrise.chat("❌ Stream error.")

        try:
            os.remove("/tmp/song.mp3")
        except:
            pass

        await self.play_next()


if __name__ == "__main__":
    from highrise.__main__ import main, BotDefinition
    room_id = "62f3ce65de2ae5263fc7b757"
    bot_token = "2afcac2710768c9381a893c6ce8cc9cc0d360ed54a849948c188998d314dffd3"
    definitions = [BotDefinition(MusicBot(), room_id, bot_token)]
    asyncio.run(main(definitions))