from __future__ import unicode_literals
import os
import youtube_dl
import discord
from discord.ext import commands, tasks
import glob
import time
import asyncio

def startup():
    try:
        os.makedirs("Songs")
    except FileExistsError as e:
        print(e)
    QUEUE = []
    return os.getcwd() + rf'\Songs'

def clear_all_songs():
    for song in glob.glob(rf'{SONG_FOLDER_PATH}\*'):
        try:
            print(f'3 REMOVING {song}')
            os.remove(song)
        except Exception as e:
            print(f'Error {e} -> Song: {song}')

SONG_FOLDER_PATH = startup()
clear_all_songs()

TOKEN = 'TOKEN HERE'
QUEUE = []
VOICE_CHANNEL = None
NOW_PLAYING = None
CHANNEL = 543874559074369611
LOOP = False
PAUSE = False

ydl_opts = {
    'format': 'worstaudio',
    'outtmpl': rf'{SONG_FOLDER_PATH}\%(title)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        }],
    'noplaylist':True,}

jcole = commands.Bot(command_prefix= '!')

def pretty_song_name(path):
    b = os.path.basename(os.path.normpath(path))[0:-3]
    index = b.rfind(r'\\')
    return f'`{b[0:index]}`'

def get_jcole_beat(url):
    global QUEUE
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl._ies = [ydl.get_info_extractor('Youtube')]
        try:
            ydl.download([url])
            for song in glob.glob(rf'{SONG_FOLDER_PATH}\*.mp3'):
                if song not in QUEUE:
                    QUEUE.append(song)
                    return QUEUE[-1]
        except youtube_dl.utils.DownloadError:
            raise Exception('You stupid stupid idiot stupid boy, that is not even a correct youtube url you stupid dumb dumby.')
        except Exception as e:
            raise Exception(f'IDK {e}')

def play_music(vc, song=None, index=None):
    global QUEUE, NOW_PLAYING
    if song:
        try:
            vc.play(discord.FFmpegPCMAudio(
                executable=r"C:\ProgramData\chocolatey\bin\ffmpeg.exe", 
                source=song)
                )
            song = pretty_song_name(song)
            NOW_PLAYING = song
        except Exception as e:
            raise e
    if index != None:
        try:
            if QUEUE:
                vc.play(discord.FFmpegPCMAudio(
                    executable=r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
                     source=QUEUE[index])
                    )
                NOW_PLAYING = pretty_song_name(QUEUE[index])
                return True
            else:
                return
        except discord.errors.ClientException as e:
            if e == 'Already playing audio.':
                return "Song added to queue"

@tasks.loop(seconds=10)
async def next_song():
    global VOICE_CHANNEL, QUEUE, NOW_PLAYING, LOOP, CHANNEL, PAUSE
    start = time.time()
    while not VOICE_CHANNEL:
        await asyncio.sleep(1)
        start = time.time()
    while (time.time() - start < 2):
        if not VOICE_CHANNEL.is_playing():
            await asyncio.sleep(1)
            if PAUSE:
                start = time.time()
        else:
            await asyncio.sleep(1)
            start = time.time()
    try:
        if not LOOP:
            song = QUEUE.pop(0)
            print(f'4 REMOVING {song}')
            play_music(VOICE_CHANNEL, index=0)
            await jcole.get_channel(CHANNEL).send(
                f'🎶  **Now playing**:  {NOW_PLAYING}'
                )
            os.remove(song)
        else:
            play_music(VOICE_CHANNEL, index=0)
            if VOICE_CHANNEL.is_playing():
                await jcole.get_channel(CHANNEL).send(
                    f'🎶  **Now playing**:  {NOW_PLAYING}'
                    )
    except Exception as e:
        print(e)

@jcole.command(name='play', help = "- Does the big play, joins the channel you're in, does other stuff also")
async def play(ctx, *args):
    global VOICE_CHANNEL, NOW_PLAYING, QUEUE, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    try:
        voice_channel = ctx.author.voice.channel
    except AttributeError:
        return await jcole.get_channel(CHANNEL).send('Connect to a voice chat you stuped.')

    try:
        VOICE_CHANNEL = await voice_channel.connect()
    except discord.errors.ClientException:
        pass # already connected

    if len(args) == 1:
        if args[0].isnumeric(): # try to play sond at index args[0]
            play_music(VOICE_CHANNEL, index=int(args[0]))
            await ctx.send(f'🎶  **Now playing**:  {NOW_PLAYING}')
        else: # must be a url, try to play it
            song = None
            try:
                song = get_jcole_beat(args[0])
                if song == None:
                    raise Exception("eh something went wrong but I genuinely don't know why, probably because a duplicate song was added... I didn't figure out how to do that")
                print(f'from get_jcole_beat -> {song}')
            except Exception as e:
                await ctx.send(e)
                return
            try:
                print(song)
            except Exception as e:
                await ctx.send(e)
                return
            if not VOICE_CHANNEL.is_playing() and len(QUEUE) == 1:
                play_music(VOICE_CHANNEL, song=song)
                await ctx.send(f'🎶  **Now playing**:  {NOW_PLAYING}')
            else:
                play_music(VOICE_CHANNEL, index=0)
                await ctx.send(f'🎶  **Song added to queue**: {pretty_song_name(song)}')
                
    if not args:
        play_music(VOICE_CHANNEL, index=0)
        await ctx.send(f'🎶  **Now playing**:  {NOW_PLAYING}')
        await ctx.send(f"`If that said None then don't worry about that`")

@jcole.command(name='skip', help = "- What do you mean? it's in the name of the command")
async def skip(ctx, *args):
    global VOICE_CHANNEL, NOW_PLAYING, QUEUE, LOOP, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    try:
        if VOICE_CHANNEL.is_playing():
            VOICE_CHANNEL.stop()
            if LOOP:
                QUEUE.pop(0)
                return await ctx.send(f"Yeah so I didn't actually figure out how to handle this, i think that skipping with loop turned on actually breaks everything so... if the bot is still working then that is amazing.")
            song_to_remove = QUEUE.pop(0)
            print(f'0 REMOVING {song_to_remove}')
            if play_music(VOICE_CHANNEL, index=0) == None:
                os.remove(song_to_remove)
                return await ctx.send(f'🎶  **Nothing to play right now**')
            await ctx.send(f'🎶  **Now playing**:  {NOW_PLAYING}')
            os.remove(song_to_remove)
        else:
            pass
    except Exception as e:
        print(e)

@jcole.command(name='pause', help = "- Hiroshima but to the current song")
async def pause(ctx, *args):
    global VOICE_CHANNEL, CHANNEL, PAUSE
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    await ctx.send('Pausing...')
    PAUSE = True
    await VOICE_CHANNEL.pause()

@jcole.command(name='resume', help = "- all this does is tries to resume the music but so much can break")
async def resume(ctx, *args):
    global VOICE_CHANNEL, PAUSE
    await ctx.send('Viola, the music has returned')
    await VOICE_CHANNEL.resume()
    PAUSE = False
    
@jcole.command(name='queue', help = "- Prints an insanely ugly version of the queue")
async def queue(ctx, *args):
    global QUEUE, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    entire_queue = ""
    for index, song in enumerate(QUEUE):
        if index == 0:
            entire_queue = entire_queue + f"🎶  **NOW PLAYING** - {pretty_song_name(song)}\n"
        else:
            entire_queue = entire_queue + f"**{index}**. - {pretty_song_name(song)}\n"
    if entire_queue == "":
        entire_queue = 'No songs in the queue right now...'
    await ctx.send(entire_queue)

@jcole.command(name='playing', help = "- Prints the current song being played")
async def playing(ctx, *args):
    global QUEUE, NOW_PLAYING, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    if len(QUEUE) > 0:
        return await ctx.send(f'🎶  **Now playing**:  {NOW_PLAYING}')
    return await ctx.send(f'Nothing is being played right now, what you are hearing is your loud breathing. Please quiet it down.')

@jcole.command(name='move', help = "- Flips songs at position x and position y")
async def move(ctx, x: int, y: int):
    global QUEUE, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    try:
        QUEUE[x], QUEUE[y] = QUEUE[y], QUEUE[x]
        await ctx.send(f'Successfully swapped index {x} to {y} and vice versa...')
    except Exception as e:
        await ctx.send(e)

@jcole.command(name='remove', help = "- gets rid of a song at whatever position you put, i'm getting bored of typing these though and I'm pretty sure no one is ever going to even read these")
async def remove(ctx, x: int):
    global QUEUE, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    try:
        x = int(x)
        if x > 0 and x < len(QUEUE):
            song_to_remove = QUEUE.pop(x)
            os.remove(song_to_remove)
            await ctx.send(f'Successfully removed index {x}')
    except Exception as e:
        await ctx.send(f'You dumb, idk figure this out on your own... use this error message to figure out what you did so terribly wrong: {e}')

@jcole.command(name='clear', help = "- makes the queue go boom")
async def clear(ctx):
    global QUEUE, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    for song in glob.glob(rf'{SONG_FOLDER_PATH}\*.mp3'):
        try:
            os.remove(song)
        except Exception as e:
            print(f'Error {e} -> Song: {song}')
    QUEUE = []
    await ctx.send('💥⚠️  **QUEUE EMPTIED**  ⚠️💥')

@jcole.command(name='loop', help = "- why")
async def loop(ctx):
    global LOOP, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    LOOP = not LOOP
    if LOOP:
        await ctx.send('🤪 🤪  ***GET DIZZY HAHA*** 🤪🤪')
    else:
        await ctx.send('Why did i even make that a feature')

@jcole.command(name='leave', help = "- makey bot go bye bye 😔")
async def leave(ctx):
    global VOICE_CHANNEL, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    await VOICE_CHANNEL.disconnect()

@jcole.event
async def on_ready():
    print(f'{jcole.user} is connected!')

next_song.start()
jcole.run(TOKEN)
