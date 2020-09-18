import asyncio
import youtube_dl

ytdl_opts = {
    'format': 'bestaudio/best',
    'quiet': True
}
before_args = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
loop = asyncio.get_event_loop()


class YTDLModel:
    def __init__(self, resp):
        self.resp = resp
        self.vid_url = resp["webpage_url"]
        self.vid_title = resp["title"]
        self.vid_author = resp["uploader"]
        self.vid_channel_url = resp["uploader_url"]
        self.tgt_url = resp["url"]
        self.thumb = resp["thumbnail"]

    def raw(self) -> dict:
        return self.resp

    def __str__(self) -> str:
        return str(self.resp)


async def get_youtube(url) -> YTDLModel:
    return await loop.run_in_executor(None, _get_youtube, url)


def _get_youtube(url) -> YTDLModel:
    need_entries = False
    with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
        ytdl.cache.remove()
        if not bool(url.startswith("https://") or url.startswith("http://") or url.startswith("youtu.be") or url.startswith("youtube.com")):
            need_entries = True
            url = "ytsearch1:" + url
        song = ytdl.extract_info(url, download=False)
        if need_entries:
            song = song["entries"][0]
        return YTDLModel(song)


if __name__ == "__main__":
    res = _get_youtube("teminite monster")
    print(res)
    res = _get_youtube("https://www.youtube.com/watch?v=1SAXBLZLYbA")
    print(res)
