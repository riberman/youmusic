from __future__ import unicode_literals
import youtube_dl


ydl_opts = {
    'outtmpl': 'downloaded_music/%(title)s-%(id)s.%(ext)s',
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}
print("Insert URL from YouTube video to download")
url = input()

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
