import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import random

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

# YTDL options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'nocheckcertificate': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'cookiefile': '/path/to/cookies/file',  # Replace with your cookies file path
    'verbose': True,
    'extract_flat': 'in_playlist',
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    },
    
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


# Command to play a YouTube playlist or video
@bot.command(name='play', help='Plays a YouTube playlist or video link')

async def play(ctx, *, url: str):
    global music_queue, is_playing
    
    if not ctx.voice_client:
        await ctx.invoke(join)

    try:
        await ctx.send("Fetching audio, please wait...")

        # Extract audio URLs from the playlist or video
        data = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ytdl.extract_info(url, download=False)
        )

        if 'entries' in data:  # Playlist detected
            for entry in data['entries']:
                if entry and 'url' in entry:
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
        current_song_url = music_queue.pop(0)

        try:
            # Extract the audio URL using yt-dlp
            info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ytdl.extract_info(current_song_url, download=False)
            )

            # Get the audio URL from the extracted info
            audio_url = info.get('url')
            if not audio_url:
                await ctx.send("Could not extract audio URL.")
                is_playing = False
                return await play_next(ctx)

            # Play the audio
            source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
            ctx.voice_client.play(
                source,
                after=lambda _: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
            )
            await ctx.send(f"Now playing: {info.get('title', 'Unknown track')}")

        except Exception as e:
            await ctx.send(f"An error occurred while playing: {str(e)}")
            is_playing = False
            return await play_next(ctx)
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

#Shuffles the current playlist
@bot.command(name='shuffle', help='Shuffles the current music queue')
async def shuffle(ctx):
    global music_queue

    if len(music_queue) > 1:
        random.shuffle(music_queue)
        await ctx.send("The music queue has been shuffled!")
    elif len(music_queue) == 1:
        await ctx.send("There's only one song in the queue, no need to shuffle.")
    else:
        await ctx.send("The queue is empty, nothing to shuffle.")

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
TOKEN = "Add your bot token"  # Replace with your bot token
bot.run(TOKEN)
