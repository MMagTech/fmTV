import os
import time
import requests
import subprocess
import logging
from logging.handlers import TimedRotatingFileHandler
from yt_dlp import YoutubeDL
from PIL import Image
from io import BytesIO
from googleapiclient.discovery import build

# Environment variables
API_KEY = os.getenv('LASTFM_API_KEY', 'your_lastfm_api_key')
USERNAME = os.getenv('LASTFM_USERNAME', 'your_lastfm_username')
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', '/downloads')
APP_DATA_PATH = os.getenv('APP_DATA_PATH', '/appdata')
POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', '300'))  # Default to 300 seconds (5 minutes)
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

if not YOUTUBE_API_KEY:
    raise ValueError("No YOUTUBE_API_KEY found in environment variables")

LASTFM_URL = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={USERNAME}&api_key={API_KEY}&format=json'
LASTFM_TRACK_INFO_URL = f'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={API_KEY}&format=json&artist={{artist}}&track={{track}}'

# Configure logging
log_file_path = os.path.join(APP_DATA_PATH, 'downloader.log')
handler = TimedRotatingFileHandler(log_file_path, when="D", interval=7, backupCount=4)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def get_recent_tracks():
    logger.info('Fetching recent tracks from Last.fm')
    response = requests.get(LASTFM_URL)
    if response.status_code == 200:
        data = response.json()
        recent_tracks = data['recenttracks']['track']
        logger.info(f'Fetched {len(recent_tracks)} tracks')
        return recent_tracks
    else:
        logger.error(f'Failed to fetch recent tracks: {response.status_code}')
        return []

def get_track_info(artist, track):
    url = LASTFM_TRACK_INFO_URL.format(artist=artist, track=track)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'track' in data:
            track_info = data['track']
            genre = track_info['toptags']['tag'][0]['name'] if track_info['toptags']['tag'] else 'Unknown'
            return genre
    return 'Unknown'

def search_official_video(song_title, artist):
    query = f'{artist} {song_title} official music video'
    ydl_opts = {
        'quiet': True,
        'default_search': 'ytsearch',
        'noplaylist': True,
        'format': 'bestvideo+bestaudio/best',
        'extract_flat': 'in_playlist',
    }
    with YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(query, download=False)
        if 'entries' in results:
            return results['entries'][0]['url']
    return None

def download_thumbnail(thumbnail_url, output_path):
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        thumbnail_path = os.path.join(output_path, 'thumbnail.jpg')
        image.save(thumbnail_path)
        return thumbnail_path
    return None

def set_video_thumbnail(video_path, thumbnail_path):
    temp_video_path = video_path.replace('.mp4', '_with_thumbnail.mp4')
    command = [
        'ffmpeg', '-i', video_path, '-i', thumbnail_path,
        '-map', '0', '-map', '1', '-c', 'copy',
        '-disposition:1', 'attached_pic', temp_video_path
    ]
    subprocess.run(command, check=True)
    os.replace(temp_video_path, video_path)

def get_youtube_metadata(video_id):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.videos().list(part='snippet', id=video_id)
    response = request.execute()
    if response['items']:
        video_info = response['items'][0]['snippet']
        title = video_info['title']
        description = video_info['description']
        tags = video_info.get('tags', [])
        thumbnail_url = video_info['thumbnails']['high']['url']
        return title, description, tags, thumbnail_url
    return None, None, None, None

def download_song(video_url, song_title, artist, album, genre):
    video_file_name = f'{artist} - {song_title}.mp4'
    audio_file_name = f'{artist} - {song_title}.m4a'
    downloaded_video = os.path.join(DOWNLOAD_PATH, video_file_name)
    downloaded_audio = os.path.join(DOWNLOAD_PATH, audio_file_name)
    final_file = os.path.join(DOWNLOAD_PATH, video_file_name)

    ydl_opts_video = {
        'format': 'bestvideo',
        'outtmpl': downloaded_video,
    }
    ydl_opts_audio = {
        'format': 'bestaudio',
        'outtmpl': downloaded_audio,
    }

    with YoutubeDL(ydl_opts_video) as ydl:
        ydl.download([video_url])

    with YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([video_url])

    # Merge video and audio
    command = [
        'ffmpeg', '-i', downloaded_video, '-i', downloaded_audio,
        '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental',
        final_file
    ]
    subprocess.run(command, check=True)

    # Extract video ID from the URL
    video_id = video_url.split('v=')[-1]
    title, description, tags, thumbnail_url = get_youtube_metadata(video_id)

    if thumbnail_url:
        thumbnail_path = download_thumbnail(thumbnail_url, DOWNLOAD_PATH)
        if thumbnail_path:
            set_video_thumbnail(final_file, thumbnail_path)

    logger.info(f'Successfully processed {song_title} by {artist}')

    # Cleanup temporary files
    os.remove(downloaded_video)
    os.remove(downloaded_audio)

if __name__ == "__main__":
    last_downloaded_track = None

    while True:
        try:
            logger.info('Polling Last.fm for recent tracks')
            recent_tracks = get_recent_tracks()

            # Get the most recent track
            if recent_tracks:
                most_recent_track = recent_tracks[0]
 
