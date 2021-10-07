#!/bin/env python3

from __future__ import unicode_literals
from datetime import datetime
import os
import random
from yt_dlp import YoutubeDL, utils
import discord
from discord.ext import commands, tasks
import glob
import time
import asyncio
import sys
from dotenv import Dotenv

# make the current working directory always the directory of the python script
os.chdir(os.path.dirname(sys.argv[0]))

CWD = os.getcwd()
dotenv = Dotenv(f'{CWD}/.env')
CHANNEL = dotenv.get('CHANNEL_ID')  # maybe leave these out of class
TOKEN = dotenv.get('DISCORD_TOKEN')  # this one and below


class discord_bot(discord.Client):
    CHANNEL = int(CHANNEL)  # do something with this
    QUEUE = []  # should stay
    VOICE_CHANNEL = None  # should stay
    NOW_PLAYING = None
    LOOP = False
    DOWNLOADING = False  # should stay

    def startup(self):
        try:
            os.makedirs("Songs")
        except FileExistsError as e:
            print(e)
        self.cwd = os.getcwd()
        _ = open(f'{self.cwd}/comments', 'a+')
        return f'{self.cwd}/Songs'

    def clear_all_songs(self):
        for song in glob.glob(rf'{self.SONG_FOLDER_PATH}/*'):
            try:
                print(f'11 REMOVING {song}')
                os.remove(song)
            except Exception as e:
                print(f'Error {e} -> Song: {song}')

    async def on_ready(self):
        print('Logged on as self.user')
        (f'{self.user} is connected!')
        #  MOVE STARTUP TO HERE
        self.SONG_FOLDER_PATH = self.startup()
        self.ydl_opts = {
            'format': 'worstaudio',
            'outtmpl': rf'{self.SONG_FOLDER_PATH}/%(title)s.%(ext)s',
            'noplaylist':True,
            'max_downloads': 5,
            'throttled_rate': '100K',
        }
        self.clear_all_songs()  # move this to run on startup
        await self.get_channel(CHANNEL).send('give me beats.')
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening, name="mukiz"))

    @staticmethod
    def pretty_song_name(path):
        """
        Takes in a filepath (for now a linux path, replace / with \\ if you want
        to use windows. Returns the name of whatever file is found. Probably
        should rewrite this to use os to get file name.
        """
        index1 = path.rfind('.')
        b = os.path.basename(os.path.normpath(path))[0:index1]
        index = b.rfind(r'.')
        return f'`{b[0:index]}`'

    def get_jcole_beat(self, url):
        self.DOWNLOADING = True
        self.ydl_opts['noplaylist'] = False
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([url])
                for song in glob.glob(rf'{self.SONG_FOLDER_PATH}/*.webm'):
                    if song not in self.QUEUE:
                        self.QUEUE.append(song)
                for song in glob.glob(rf'{self.SONG_FOLDER_PATH}/*.m4a'):
                    if song not in self.QUEUE:
                        self.QUEUE.append(song)
        except utils.MaxDownloadsReached:
            for song in glob.glob(rf'{self.SONG_FOLDER_PATH}/*.webm'):
                if song not in self.QUEUE:
                    self.QUEUE.append(song)
            for song in glob.glob(rf'{self.SONG_FOLDER_PATH}/*.m4a'):
                if song not in self.QUEUE:
                    self.QUEUE.append(song)

            print(self.QUEUE)
        except Exception as e:
            print(e)
            self.DOWNLOADING = False
            raise Exception(f'Error while downloading song: {e}')
        return self.QUEUE[-1]

    def get_from_song_name(self, *args):
        self.DOWNLOADING = True
        print(args)
        self.ydl_opts['noplaylist'] = True
        with YoutubeDL(self.ydl_opts) as ydl:
            try:
                ydl.extract_info(f'ytsearch:{args}', download=True)
                for song in glob.glob(rf'{self.SONG_FOLDER_PATH}/*.webm'):
                    if song not in self.QUEUE:
                        self.QUEUE.append(song)
                        return self.QUEUE[-1]
                for song in glob.glob(rf'{self.SONG_FOLDER_PATH}/*.m4a'):
                    if song not in self.QUEUE:
                        self.QUEUE.append(song)
                        return self.QUEUE[-1]
            except Exception as e:
                print(e)
                self.DOWNLOADING = False
                raise Exception(f'Error while downloading song from title: {e}')

    def play_music(self, song=None, index=None):
        self.DOWNLOADING = False
        if song:
            try:
                self.VOICE_CHANNEL.play(discord.FFmpegPCMAudio(source=song))
                song = self.pretty_song_name(song)
                self.NOW_PLAYING = song
            except Exception as e:
                raise e
        elif index:
            try:
                if self.QUEUE:
                    self.VOICE_CHANNEL.play(discord.FFmpegPCMAudio(source=self.QUEUE[index]))
                    self.NOW_PLAYING = self.pretty_song_name(self.QUEUE[index])
                    return True
                else:
                    return
            except discord.errors.ClientException as e:
                if e == 'Already playing audio.':
                    return "Song added to queue"
            except Exception as e:
                raise e

    @tasks.loop(minutes=5)
    async def dc(self):
        if not self.VOICE_CHANNEL:
            return
        if not self.VOICE_CHANNEL.is_connected():
            return
        start = time.time()
        while (time.time() - start < 300):
            if not self.VOICE_CHANNEL.is_playing() and not \
                    self.VOICE_CHANNEL.is_paused() and not self.DOWNLOADING:
                await asyncio.sleep(10)
            else:
                start = time.time()
                await asyncio.sleep(10)
        try:
            print('leaving server')
            await self.VOICE_CHANNEL.disconnect()
            await self.get_channel(self.CHANNEL).send('Bye Bye.')
        except Exception as e:
            print(e)

    @tasks.loop(seconds=10)
    async def next_song(self):
        start = time.time()
        sys.stdout.flush()
        while not self.VOICE_CHANNEL:
            await asyncio.sleep(1)
            start = time.time()
        while (time.time() - start < 2):
            if not self.VOICE_CHANNEL.is_playing():
                await asyncio.sleep(1)
                if self.VOICE_CHANNEL.is_paused() or self.DOWNLOADING:
                    start = time.time()
            else:
                await asyncio.sleep(1)
                start = time.time()
        try:
            if not self.LOOP:
                song = self.QUEUE.pop(0)
                print(f'14 REMOVING {song}')
                self.play_music(index=0)
                if self.QUEUE:
                    await self.get_channel(self.CHANNEL).send(
                        f'🎶  **Now playing**:  {self.NOW_PLAYING}')
                else:
                    await self.get_channel(self.CHANNEL).send(
                        f'🎶  **Nothing to play right now**')
                os.remove(song)
            else:
                self.play_music(index=0)
                if self.VOICE_CHANNEL.is_playing():
                    print('DEBUG: 1')
                    await self.get_channel(self.CHANNEL).send(
                        f'🎶  **Now playing**:  {self.NOW_PLAYING}')
        except Exception as e:
            print(e)

    @commands.command(aliases=['PLAY'], help="- Does the big play, joins the channel you're in, does other stuff also")
    async def play(self, ctx, *args):
        if ctx.message.channel.id != self.CHANNEL:
            return await ctx.send(
                f'You can only send stuff to the music channel: <#{self.CHANNEL}>')
        try:
            voice_channel = ctx.author.voice.channel
        except AttributeError:
            return await self.get_channel(self.CHANNEL).send(
                'Connect to a voice chat you stuped.')

        try:
            self.VOICE_CHANNEL = await voice_channel.connect()
        except discord.errors.ClientException:
            pass  # already connected

        if len(args) == 1:
            if args[0].isnumeric():  # try to play sond at index args[0]
                self.play_music(index=int(args[0]))
                await ctx.send(f'🎶  **Now playing**:  {self.NOW_PLAYING}')
            else:  # must be a url, try to play it
                song = None
                try:
                    song = self.get_jcole_beat(args[0])
                    if song is None:
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
                if not self.VOICE_CHANNEL.is_playing() and len(self.QUEUE) == 1:
                    try:
                        self.play_music(song=song)
                    except Exception as e:
                        print(f'1: Error {e}')
                    return await ctx.send(
                        f'🎶  **Now playing**:  {self.NOW_PLAYING}')
                else:
                    self.play_music(index=0)
                    return await ctx.send(
                        f'🎶  **Song added to queue**: {self.pretty_song_name(song)}')
        if args:
            song = None
            try:
                song = self.get_from_song_name(*args)
                if song is None:
                    raise Exception('`Some unknown error occurred when searching for a song by title`')
                if not self.VOICE_CHANNEL.is_playing() and len(self.QUEUE) == 1:
                    try:
                        self.play_music(song=song)
                    except Exception as e:
                        print(f'10: Error {e}')
                    return await ctx.send(
                        f'🎶  **Now playing**:  {self.NOW_PLAYING}')
                else:
                    self.play_music(index=0)
                    return await ctx.send(
                        f'🎶  **Song added to queue**: {self.pretty_song_name(song)}')

            except Exception as e:
                await ctx.send(f'Error `{e}`')

        if not args:
            self.play_music(index=0)
            await ctx.send(f'🎶  **Now playing**:  {self.NOW_PLAYING}')
            await ctx.send(f"`If that said None then don't worry about that`")

    @commands.command(aliases=['fs'], help="- What do you mean? it's in the name of the command")
    async def skip(self, ctx, *args):
        if ctx.message.channel.id != self.CHANNEL:
            return await ctx.send(f'You can only send stuff to the music channel: <#{self.CHANNEL}>')
        try:
            if self.VOICE_CHANNEL.is_playing():
                self.VOICE_CHANNEL.stop()
                if self.LOOP:
                    self.QUEUE.pop(0)
                    return await ctx.send(f"Yeah so I didn't actually figure out how to handle this, i think that skipping with loop turned on actually breaks everything so... if the bot is still working then that is amazing.")
                song_to_remove = self.QUEUE.pop(0)
                if self.play_music(index=0) is None:
                    print(f'0 REMOVING {song_to_remove}')
                    os.remove(song_to_remove)
                    return await ctx.send(f'🎶  **Nothing to play right now**')
                await ctx.send(f'🎶  **Now playing**:  {self.NOW_PLAYING}')
                await asyncio.sleep(1)
                print(f'1 REMOVING {song_to_remove}')
                os.remove(song_to_remove)
            else:
                pass
        except Exception as e:
            print(e)

    @commands.command(name='pause', help="- Hiroshima but to the current song")
    async def pause(self, ctx, *args):
        if ctx.message.channel.id != self.CHANNEL:
            return await ctx.send(f'You can only send stuff to the music channel: <#{self.CHANNEL}>')
        await ctx.send('Pausing...')
        await self.VOICE_CHANNEL.pause()

    @commands.command(name='resume', help="- all this does is tries to resume the music but so much can break")
    async def resume(self, ctx, *args):
        await ctx.send('Viola, the music has returned')
        await self.VOICE_CHANNEL.resume()

    @commands.command(name='queue', help="- Prints an insanely ugly version of the queue")
    async def queue(self, ctx, *args):
        if ctx.message.channel.id != self.CHANNEL:
            return await ctx.send(f'You can only send stuff to the music channel: <#{self.CHANNEL}>')
        entire_queue = ""
        for index, song in enumerate(self.QUEUE):
            if index == 0:
                entire_queue = entire_queue + f"🎶  **NOW PLAYING** - {self.pretty_song_name(song)}\n"
            elif index < 10:
                entire_queue = entire_queue + f"**{index}**. - {self.pretty_song_name(song)}\n"
            else:
                pass
        if entire_queue == "":
            entire_queue = 'No songs in the queue right now...'
        await ctx.send(entire_queue)

    @commands.command(name='shuffle', help='- Gives the queue a good mixin')
    async def shuffle(self, ctx,):
        if ctx.message.channel.id != self.CHANNEL:
            return await ctx.send(f'You can only send stuff to the music channel: <#{self.CHANNEL}>')
        else:
            return await ctx.send('I broke it initially so for now it does nothing. May or may not ever fix it.')
        """
        try:
            random.shuffle(self.QUEUE)
            await ctx.send(f'Successfully shuffled.')
            print(QUEUE)
        except Exception as e:
            await ctx.send(e)
        """

    @commands.command(name='playing', help="- Prints the current song being played")
    async def playing(self, ctx, *args):
        if ctx.message.channel.id != self.CHANNEL:
            return await ctx.send(f'You can only send stuff to the music channel: <#{self.CHANNEL}>')
        if len(self.QUEUE) > 0:
            return await ctx.send(f'🎶  **Now playing**:  {self.NOW_PLAYING}')
        return await ctx.send(f'Nothing is being played right now, what you are hearing is your loud breathing. Please quiet it down.')


    @commands.command(name='move', help="- Moves a song from position x to position y")
    async def move(self, ctx, x: int, y: int):
        if ctx.message.channel.id != self.CHANNEL:
            return await ctx.send(f'You can only send stuff to the music channel: <#{self.CHANNEL}>')
        try:
            self.QUEUE.insert(y, self.QUEUE.pop(x))
            await ctx.send(f'Successfully moved song to position {y}...')
        except Exception as e:
            await ctx.send(e)

    @commands.command(name='remove', help="- gets rid of a song at whatever position you put, i'm getting bored of typing these though and I'm pretty sure no one is ever going to even read these")
    async def remove(self, ctx, x: int):
        if ctx.message.channel.id != self.CHANNEL:
            return await ctx.send(f'You can only send stuff to the music channel: <#{self.CHANNEL}>')
        try:
            x = int(x)
            if x > 0 and x < len(self.QUEUE):
                song_to_remove = self.QUEUE.pop(x)
                print(f'2 REMOVING {song_to_remove}')
                os.remove(song_to_remove)
                await ctx.send(f'Successfully removed index {x}')
        except Exception as e:
            await ctx.send(f'You dumb, idk figure this out on your own... use this error message to figure out what you did so terribly wrong: {e}')

    @commands.command(name='clear', help="- makes the queue go boom")
    async def clear(self, ctx):
        if ctx.message.channel.id != self.CHANNEL:
            return await ctx.send(f'You can only send stuff to the music channel: <#{self.CHANNEL}>')
        for song in glob.glob(rf'{self.SONG_FOLDER_PATH}/*'):
            try:
                os.remove(song)
                print(f'10 REMOVING {song}')
            except Exception as e:
                print(f'Error {e} -> Song: {song}')
        QUEUE = []
        await ctx.send('💥⚠️  **QUEUE EMPTIED**  ⚠️💥')

    @commands.command(name='loop', help="- why")
    async def loop(self, ctx):
        if ctx.message.channel.id != self.CHANNEL:
            return await ctx.send(f'You can only send stuff to the music channel: <#{self.CHANNEL}>')
        self.LOOP = not self.LOOP
        if self.LOOP:
            await ctx.send('🤪 🤪  ***GET DIZZY HAHA*** 🤪🤪')
        else:
            await ctx.send('**Loop disabled**')

    @commands.command(name='leave', help="- makey bot go bye bye 😔")
    async def leave(self, ctx):
        if ctx.message.channel.id != self.CHANNEL:
            return await ctx.send(f'You can only send stuff to the music channel: <#{self.CHANNEL}>')
        await self.VOICE_CHANNEL.disconnect()

    @commands.command(name='comment', help="- you can leave me a comment about what to add or if something went wrong")
    async def comment(self, ctx, *args):
        if args:
            with open(f'{self.CWD}/comments', 'a') as file:
                file.write(f'{datetime.now().strftime("[%Y/%m/%d][%H:%M]-")} {ctx.message.author.name}: {" ".join(args)}\n')
            file.close()

    @commands.command(name='viewComments', help='shows all of the comments made so far')
    async def view_comments(self, ctx, *args):
        text = []
        to_return = ""
        with open(f'{self.CWD}/comments' ,'r') as file:
            text.append(file.read().strip().split('\n'))
        text = text[0]
        if len(text) > 5:
            to_return = "\n".join(text[-5:])
        else:
            to_return = '\n'.join(text)
        if to_return:
            await ctx.send(to_return)

# dc.start()
# jcole = commands.Bot(command_prefix= '!')
# next_song.start()
# jcole.run(TOKEN)
