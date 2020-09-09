import asyncio
import youtube_dl

ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True
}
before_args = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
loop = asyncio.get_event_loop()


async def get_youtube(url):
    return await loop.run_in_executor(None, _get_youtube, url)


def _get_youtube(url):
    need_entries = False
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.cache.remove()
        if not bool(url.startswith("https://") or url.startswith("http://") or url.startswith("youtu.be") or url.startswith("youtube.com")):
            need_entries = True
            url = "ytsearch1:" + url
        song = ydl.extract_info(url, download=False)
        if need_entries:
            song = song["entries"][0]
        return song


if __name__ == "__main__":
    res = loop.run_until_complete(get_youtube("teminite monster"))
    print(res)
    res = loop.run_until_complete(get_youtube("https://www.youtube.com/watch?v=1SAXBLZLYbA"))
    print(res)
