import yt_dlp
link = "https://www.youtube.com/watch?v=V9G-teNRTGQ"
with yt_dlp.YoutubeDL() as ydl:
    info_dict = ydl.extract_info(link, download=False)
    formats = info_dict['formats']
    info = []
    for i in range(len(formats)):
        if formats[i]['ext'] == 'webm' or formats[i]['ext'] == '3gp':
            continue
        else:
            if formats[i]['format'].split('- ')[1] == formats[i-1]['format'].split('- ')[1]:
                print(formats[i]['format'])
                continue
            else:
                info.append({
                    "format_id": formats[i]["format_id"],
                    "ext": formats[i]["ext"],
                    "quality": formats[i]["format"].split('- ')[1],
                    "acodec": formats[i]["acodec"],
                    "fps": formats[i]["fps"],
                })
    best_video = info[-1]
    print(best_video)
    best_quality = best_video['quality']
    best_ext = best_video['ext']
    best_fps = best_video['fps']
    best_format_id = best_video['format_id']
print(info)
