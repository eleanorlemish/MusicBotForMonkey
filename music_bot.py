import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

# YTDL options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(title)s.%(ext)s',
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'cookiefile': '/path/to/youtube_cookies.txt',  # Path to your cookies file
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    },
    'lazy_extractors': True,
}

ffmpeg_options = {
    'options': '-vn',  # Disable video processing
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Music queue
music_queue = []
is_playing = False

# Command to join a voice channel
@bot.command(name='join', help='Bot joins the voice channel')
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await channel.connect()
        else:
            await ctx.send("I am already in a voice channel.")
    else:
        await ctx.send("You are not connected to a voice channel.")

# Command to play a YouTube playlist
@bot.command(name='play', help='Plays a YouTube playlist link')
async def play(ctx, *, url: str):
    global music_queue, is_playing

    if not ctx.voice_client:
        await ctx.invoke(join)

    try:
        # Extract playlist or video data
        await ctx.send("Fetching playlist, please wait...")
        data = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ytdl.extract_info(url, download=False)
        )

        if 'entries' in data:  # Playlist detected
            for entry in data['entries']:
                if entry:
                    music_queue.append(entry['url'])
            await ctx.send(f"Added {len(data['entries'])} tracks to the queue.")
        else:  # Single video
            music_queue.append(data['url'])
            await ctx.send(f"Added to queue: {data['title']}")

        if not is_playing:
            await play_next(ctx)

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# Function to play the next song in the queue
async def play_next(ctx):
    global music_queue, is_playing

    if music_queue:
        is_playing = True
        current_song = music_queue.pop(0)

        source = discord.FFmpegPCMAudio(
            current_song,
            **ffmpeg_options
        )
        ctx.voice_client.play(
            source,
            after=lambda _: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        )
        await ctx.send(f"Now playing: {current_song}")
    else:
        is_playing = False
        await ctx.send("The queue is empty.")

# Command to skip the current song
@bot.command(name='skip', help='Skips the current song')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipping the current song...")
    else:
        await ctx.send("No music is currently playing.")

# Command to stop and clear the queue
@bot.command(name='stop', help='Stops the music and clears the queue')
async def stop(ctx):
    global music_queue, is_playing
    if ctx.voice_client:
        ctx.voice_client.stop()
        music_queue = []
        is_playing = False
        await ctx.voice_client.disconnect()
        await ctx.send("Stopped the music and cleared the queue.")
    else:
        await ctx.send("I'm not in a voice channel.")

# Run the bot
TOKEN = "Put Token Here"  # Replace with your bot token
bot.run(TOKEN)
