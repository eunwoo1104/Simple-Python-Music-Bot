import discord
import os
import shutil
import json
import time
import asyncio
import random
from discord.ext import commands
from utils import get_youtube
from utils import page
from utils import confirm


async def get_queue(guild_id):
    exists = os.path.isfile(f"music/{guild_id}.json")
    if not exists:
        shutil.copy("json_temp.json", f"music/{guild_id}.json")
    with open(f"music/{guild_id}.json", "r") as f:
        return json.load(f)


async def update_queue(guild_id, queue_json):
    with open(f"music/{guild_id}.json", "w") as f:
        json.dump(queue_json, f, indent=4)


async def queue_task(bot: commands.Bot, ctx: commands.Context, voice: discord.VoiceClient):
    while True:
        exists = os.path.isfile(f"music/{ctx.guild.id}.json")
        if not exists:
            await ctx.send(f"`{voice.channel}`에서 나갈께요.")
            await voice.disconnect(force=True)
            break
        queue = await get_queue(ctx.guild.id)
        if voice.is_playing() or voice.is_paused():
            await asyncio.sleep(1)
            continue
        elif not voice.is_playing() and len(queue.keys()) == 1 and queue["playing"]["loop"] is not True:
            await ctx.send(f"음악이 끝났어요. `{voice.channel}`에서 나갈께요.")
            await voice.disconnect(force=True)
            os.remove(f"music/{ctx.guild.id}.json")
            break
        vol = queue["playing"]["vol"]
        if queue["playing"]["loop"] is True:
            tgt_url = queue["playing"]["tgt_url"]
            voice.play(discord.FFmpegPCMAudio(tgt_url, before_options=get_youtube.before_args))
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = vol
            await asyncio.sleep(3)
            continue
        if queue["playing"]["random"]:
            queue_keys = [str(x) for x in queue.keys() if not x == "playing"]
            tgt_name = str(random.choice(queue_keys))
            tgt_queue = queue[tgt_name]
        else:
            tgt_name = list(queue.keys())[1]
            tgt_queue = queue[tgt_name]
        vid_url = tgt_queue["vid_url"]
        vid_title = tgt_queue["vid_title"]
        vid_author = tgt_queue["vid_author"]
        vid_channel_url = tgt_queue["vid_channel_url"]
        tgt_url = tgt_queue["tgt_url"]
        thumb = tgt_queue["thumb"]
        req_by = bot.get_user(int(tgt_queue["req_by"]))
        voice.play(discord.FFmpegPCMAudio(tgt_url, before_options=get_youtube.before_args))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = vol
        embed = discord.Embed(title="유튜브 음악 재생", color=discord.Colour.from_rgb(255, 0, 0))
        embed.add_field(name="재생 시작", value=f"업로더: [`{vid_author}`]({vid_channel_url})\n제목: [`{vid_title}`]({vid_url})",
                        inline=False)
        embed.add_field(name="요청자", value=f"{req_by.mention} (`{req_by}`)", inline=False)
        embed.set_image(url=str(thumb))
        queue["playing"]["vid_url"] = vid_url
        queue["playing"]["vid_title"] = vid_title
        queue["playing"]["vid_author"] = vid_author
        queue["playing"]["vid_channel_url"] = vid_channel_url
        queue["playing"]["thumb"] = thumb
        queue["playing"]["tgt_url"] = tgt_url
        queue["playing"]["req_by"] = tgt_queue["req_by"]
        await ctx.send(embed=embed)
        del queue[tgt_name]
        await update_queue(ctx.guild.id, queue)
        await asyncio.sleep(3)


async def check_voice(ctx: commands.Context, resume=False):
    voice = ctx.voice_client
    user_voice = ctx.message.author.voice
    if user_voice is None:
        await ctx.send(f"{ctx.author.mention} 먼저 음성 채널에 들어와주세요.")
        return False
    if voice is None:
        await ctx.send(f"{ctx.author.mention} 재생을 먼저 해주세요.")
        return False
    if not voice.is_playing():
        if resume is True:
            return True
        await ctx.send(f"{ctx.author.mention} 현재 재생중인 노래가 없습니다.")
        return None
    return True


loop = asyncio.get_event_loop()


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="재생", description="음악을 재생합니다.", aliases=["play", "p", "ㅔ", "대기", "queue", "q", "ㅂ"])
    async def play(self, ctx, *, url):
        msg = await ctx.send(
            f"잠시만 기다려주세요...\n팁: 만약에 너무 오랫동안 재생이 안된다면 `강제연결해제` 명령어를 사용해주세요.")
        embed = discord.Embed(title="유튜브 음악 재생", color=discord.Colour.from_rgb(255, 0, 0))
        user_voice = ctx.message.author.voice
        if user_voice is None:
            return await msg.edit(content=f"{ctx.author.mention} 먼저 음성 채널에 들어와주세요.")
        voice_channel = user_voice.channel
        if voice_channel is None or voice_channel is False:
            return await msg.edit(content=f"{ctx.author.mention} 먼저 음성 채널에 들어와주세요.")
        voice = ctx.voice_client
        if voice is None:
            await voice_channel.connect()
            voice = ctx.voice_client
        music_folder_exists = os.path.isdir("music")
        if not music_folder_exists:
            os.mkdir("music")
        exists = os.path.isfile(f"music/{ctx.guild.id}.json")
        if not voice.is_playing() and not voice.is_paused() and exists:
            os.remove(f"music/{ctx.guild.id}.json")
        search_res = await get_youtube.get_youtube(url)
        vid_url = search_res["webpage_url"]
        vid_title = search_res["title"]
        vid_author = search_res["uploader"]
        vid_channel_url = search_res["uploader_url"]
        tgt_url = search_res["formats"][0]["url"]
        thumb = search_res["thumbnail"]
        default_vol = 0.3
        embed.set_image(url=str(thumb))
        queue = await get_queue(ctx.guild.id)
        if voice.is_playing():
            current_time = time.strftime('%H%M%S', time.localtime(time.time()))
            queue[str(current_time)] = {}
            queue[str(current_time)]["vid_url"] = vid_url
            queue[str(current_time)]["vid_title"] = vid_title
            queue[str(current_time)]["vid_author"] = vid_author
            queue[str(current_time)]["vid_channel_url"] = vid_channel_url
            queue[str(current_time)]["thumb"] = thumb
            queue[str(current_time)]["tgt_url"] = tgt_url
            queue[str(current_time)]["req_by"] = ctx.author.id
            await update_queue(ctx.guild.id, queue)
            embed.add_field(name="재생 목록에 추가됨",
                            value=f"업로더: [`{vid_author}`]({vid_channel_url})\n제목: [`{vid_title}`]({vid_url})",
                            inline=False)
            embed.add_field(name="요청자", value=f"{ctx.author.mention} (`{ctx.author}`)", inline=False)
            return await msg.edit(content="", embed=embed)
        voice.play(discord.FFmpegPCMAudio(tgt_url, before_options=get_youtube.before_args))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = default_vol
        embed.add_field(name="재생 시작", value=f"업로더: [`{vid_author}`]({vid_channel_url})\n제목: [`{vid_title}`]({vid_url})",
                        inline=False)
        embed.add_field(name="요청자", value=f"{ctx.author.mention} (`{ctx.author}`)", inline=False)
        await msg.edit(content="", embed=embed)
        queue["playing"] = {}
        queue["playing"]["vid_url"] = vid_url
        queue["playing"]["vid_title"] = vid_title
        queue["playing"]["vid_author"] = vid_author
        queue["playing"]["vid_channel_url"] = vid_channel_url
        queue["playing"]["thumb"] = thumb
        queue["playing"]["tgt_url"] = tgt_url
        queue["playing"]["vol"] = default_vol
        queue["playing"]["req_by"] = ctx.author.id
        queue["playing"]["loop"] = False
        queue["playing"]["random"] = False
        await update_queue(ctx.guild.id, queue)
        await asyncio.create_task(queue_task(self.bot, ctx, voice))

    @commands.command(name='루프', description="재생중인 음악을 무한 반복하거나 무한 반복을 해제합니다.", aliases=["무한반복", "loop", "repeat"])
    async def music_loop(self, ctx):
        voice_ok = await check_voice(ctx)
        if not voice_ok:
            return
        queue = await get_queue(ctx.guild.id)
        if queue["playing"]["loop"] is not True:
            msg = await ctx.send(f"{ctx.author.mention} 정말로 이 음악을 무한반복할까요?")
            res = await confirm.confirm(self.bot, ctx, msg)
            if res is not True:
                return await msg.edit(content=f"{ctx.author.mention} 무한반복이 취소되었습니다.")
            queue["playing"]["loop"] = True
            await update_queue(ctx.guild.id, queue)
            return await msg.edit(content=f"{ctx.author.mention} 이 음악을 무한반복할께요!")
        elif queue["playing"]["loop"] is True:
            msg = await ctx.send(f"{ctx.author.mention} 정말로 무한반복을 해제할까요?")
            res = await confirm.confirm(self.bot, ctx, msg)
            if res is not True:
                return await msg.edit(content=f"{ctx.author.mention} 무한반복 해제가 취소되었습니다.")
            queue["playing"]["loop"] = False
            await update_queue(ctx.guild.id, queue)
            return await msg.edit(content=f"{ctx.author.mention} 무한반복이 해제되었습니다.")

    @commands.command(name="셔플", description="대기 리스트에서 음악을 무작위로 재생합니다.", aliases=["랜덤", "random", "shuffle", "sf", "ㄶ", "ㄴㅎ"])
    async def shuffle(self, ctx):
        voice_ok = await check_voice(ctx)
        if not voice_ok:
            return
        queue = await get_queue(ctx.guild.id)
        if queue["playing"]["random"] is not True:
            msg = await ctx.send(f"{ctx.author.mention} 정말로 랜덤 재생 기능을 켤까요?")
            res = await confirm.confirm(self.bot, ctx, msg)
            if res is not True:
                return await msg.edit(content=f"{ctx.author.mention} 랜덤 재생이 취소되었습니다.")
            queue["playing"]["random"] = True
            await update_queue(ctx.guild.id, queue)
            return await msg.edit(content=f"{ctx.author.mention} 랜덤 재생이 켜졌어요!")
        elif queue["playing"]["random"] is True:
            msg = await ctx.send(f"{ctx.author.mention} 정말로 랜덤 재생을 해제할까요?")
            res = await confirm.confirm(self.bot, ctx, msg)
            if res is not True:
                return await msg.edit(content=f"{ctx.author.mention} 랜덤 재생 해제가 취소되었습니다.")
            queue["playing"]["random"] = False
            await update_queue(ctx.guild.id, queue)
            return await msg.edit(content=f"{ctx.author.mention} 랜덤 재생이 해제되었습니다.")

    @commands.command(name="스킵", description="재생중인 음악을 스킵합니다.", aliases=["s", "skip", "ㄴ"])
    async def skip(self, ctx):
        voice = ctx.voice_client
        voice_ok = await check_voice(ctx)
        if not voice_ok:
            return
        voice.stop()

    @commands.command(name="정지", description="음악 재생을 멈춥니다.", aliases=["stop", "ㄴ새ㅔ"])
    async def stop(self, ctx):
        voice = ctx.voice_client
        voice_ok = await check_voice(ctx)
        if not voice_ok:
            return
        os.remove(f"music/{ctx.guild.id}.json")
        voice.stop()

    @commands.command(name="일시정지", description="음악을 일시정지합니다.", aliases=["pause", "ps", "ㅔㄴ"])
    async def pause(self, ctx):
        voice = ctx.voice_client
        voice_ok = await check_voice(ctx)
        if not voice_ok:
            return
        voice.pause()
        await ctx.send(f"{ctx.author.mention} 플레이어를 일시정지했습니다.")

    @commands.command(name="계속재생", description="음악 일시정지를 해제합니다.", aliases=["resume", "r", "ㄱ"])
    async def resume(self, ctx):
        voice = ctx.voice_client
        voice_ok = await check_voice(ctx, resume=True)
        if voice_ok is None:
            pass
        elif not voice_ok:
            return
        voice.resume()
        await ctx.send(f"{ctx.author.mention} 음악을 계속 재생합니다.")

    @commands.command(name="강제연결해제", description="봇 오류로 음악 재생에 문제가 발생했을 때 강제로 접속을 해제합니다.", aliases=["나가", "제발나가", "quit", 'leave', 'l', "ㅣ"])
    async def force_quit(self, ctx):
        voice = ctx.voice_client
        await voice.disconnect(force=True)
        await ctx.send("강제 연결 해제가 완료되었습니다.")

    @commands.command(name="볼륨", description="음악의 볼륨을 조절합니다.", aliases=["volume", "vol", "v", "패ㅣㅕㅡㄷ", "ㅍ"])
    async def volume(self, ctx, vol: int = None):
        if vol > 100:
            return await ctx.send("숫자가 너무 큽니다.")
        if vol <= 0:
            return await ctx.send("숫자가 너무 작습니다.")
        queue = await get_queue(ctx.guild.id)
        voice_ok = await check_voice(ctx)
        if not voice_ok:
            return
        current_vol = float(queue["playing"]["vol"])
        if vol is None:
            return await ctx.send(f"{ctx.author.mention} 현재 볼륨은 `{current_vol * 100}%` 입니다.")
        queue["playing"]["vol"] = vol / 100
        ctx.voice_client.source.volume = vol / 100
        await ctx.send(f"{ctx.author.mention} 볼륨이 `{vol}%`로 변경되었습니다.")
        await update_queue(ctx.guild.id, queue)

    @commands.command(name="대기리스트", description="현재 대기 리스트를 보여줍니다.", aliases=["대기열", "재생리스트", "pl", "ql", "queuelist", "playlist", "비", "ㅔㅣ"])
    async def queue_list(self, ctx):
        queue_list = await get_queue(ctx.guild.id)
        if bool(queue_list) is False:
            return await ctx.send("현재 재생중이 아닙니다.")
        temp_ql_embed = discord.Embed(title="뮤직 대기 리스트", color=discord.Colour.from_rgb(225, 225, 225))
        temp_ql_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        playing_vid_url = queue_list["playing"]["vid_url"]
        playing_vid_title = queue_list["playing"]["vid_title"]
        playing_vid_author = queue_list["playing"]["vid_author"]
        playing_vid_channel_url = queue_list["playing"]["vid_channel_url"]
        playing_thumb = queue_list["playing"]["thumb"]
        vol = queue_list["playing"]["vol"]
        one_embed = discord.Embed(title="현재 재생중", colour=discord.Color.green())
        one_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        one_embed.set_image(url=playing_thumb)
        req_by = self.bot.get_user(int(queue_list["playing"]["req_by"]))
        one_embed.add_field(name="정보",
                            value=f"업로더: [`{playing_vid_author}`]({playing_vid_channel_url})\n제목: [`{playing_vid_title}`]({playing_vid_url})",
                            inline=False)
        one_embed.add_field(name="요청자", value=f"{req_by.mention} (`{req_by}`)", inline=False)
        one_embed.add_field(name="현재 볼륨", value=f"{float(vol) * 100}%", inline=False)
        one_embed.add_field(name="대기중인 음악 개수", value=f"{len([x for x in queue_list.keys() if not x == 'playing'])}개")
        if ctx.voice_client.is_paused():
            one_embed.add_field(name="플레이어 상태", value="현재 일시정지 상태입니다.", inline=False)
        elif queue_list["playing"]["random"]:
            one_embed.add_field(name="플레이어 상태", value="랜덤 재생 기능이 켜져있습니다.", inline=False)
        if len(queue_list.keys()) == 1:
            return await ctx.send(embed=one_embed)
        ql_num = 1
        embed_list = [one_embed]
        ql_embed = None
        for x in queue_list.keys():
            if x == "playing":
                ql_embed = temp_ql_embed.copy()
                continue
            if ql_num != 1 and (ql_num - 1) % 5 == 0:
                embed_list.append(ql_embed)
                ql_embed = temp_ql_embed.copy()
            queue_vid_url = queue_list[x]["vid_url"]
            queue_vid_title = queue_list[x]["vid_title"]
            queue_vid_author = queue_list[x]["vid_author"]
            queue_thumb = queue_list[x]["thumb"]
            queue_req_by = self.bot.get_user(int(queue_list[x]["req_by"]))
            ql_embed.add_field(name="대기리스트" + str(ql_num),
                               value=f"제목: [`{queue_vid_title}`]({queue_vid_url})\n요청자: {queue_req_by.mention} (`{queue_req_by}`)",
                               inline=False)
            ql_num += 1
        next_song = queue_list[list(queue_list.keys())[1]]
        next_embed = discord.Embed(title="다음곡", color=discord.Colour.red())
        next_vid_url = next_song["vid_url"]
        next_vid_title = next_song["vid_title"]
        next_vid_author = next_song["vid_author"]
        next_vid_channel_url = next_song["vid_channel_url"]
        next_thumb = next_song["thumb"]
        next_req_by = self.bot.get_user(int(next_song["req_by"]))
        next_embed.add_field(name="정보",
                             value=f"업로더: [`{next_vid_author}`]({next_vid_channel_url})\n제목: [`{next_vid_title}`]({next_vid_url})",
                             inline=False)
        next_embed.add_field(name="요청자", value=f"{next_req_by.mention} (`{next_req_by}`)", inline=False)
        next_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        next_embed.set_image(url=next_thumb)
        embed_list.append(ql_embed)
        embed_list.append(next_embed)
        await page.start_page(self.bot, ctx, embed_list, embed=True)


def setup(bot):
    bot.add_cog(Music(bot))
