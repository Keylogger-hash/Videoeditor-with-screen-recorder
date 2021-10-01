import youtube_dl

dls_opt = {}


def download(link: str):
    with youtube_dl.YoutubeDL(dls_opt) as ydl:
        ydl.download([link])
    return True