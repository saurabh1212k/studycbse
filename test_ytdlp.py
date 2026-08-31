import yt_dlp
import requests

ydl_opts = {
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['en', 'hi'],
    'skip_download': True,
    'quiet': True,
}
url = "https://www.youtube.com/watch?v=PfomAFOur-g"
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)
    subs = info.get('requested_subtitles', {})
    
    if subs:
        sub_url = list(subs.values())[0]['url']
        r = requests.get(sub_url)
        print("Status code:", r.status_code)
        print("Text snippet:", r.text[:100])
