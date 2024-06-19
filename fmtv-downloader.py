import os
import time
import requests
import subprocess
import logging
from logging.handlers import TimedRotatingFileHandler
from yt_dlp import YoutubeDL

# Environment variables
API_KEY = os.getenv('LASTFM_API_KEY', 'your_lastfm_api_key')
USERNAME = os.getenv('LASTFM_USERNAME', 'your_lastfm_username')
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', '/downloads')
APP_DATA_PATH = os.getenv('APP_DATA_PATH', '/appdata')
POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', '300'))  # Default to 300 seconds (5 minutes)

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

def get_last_downloaded_timestamp():
    timestamp_file = os.path.join(APP_DATA_PATH, 'last_downloaded_timestamp.txt')
    if os.path.exists(timestamp_file):
        with open(timestamp_file, 'r') as file:
            return file.read().strip()
    return None

def save_last_downloaded_timestamp(timestamp):
    timestamp_file = os.path.join(APP_DATA_PATH, 'last_downloaded_timestamp.txt')
    with open(timestamp_file, 'w') as file:
        file.write(timestamp)

def get_recent_tracks(since=None):
    url = LASTFM_URL
    if since:
        url += f'&from={since}'
    response = requests.get(url)
    data = response.json()
    recent_tracks = data['recenttracks']['track']
    return recent_tracks

def get_track_info(artist, track):
    url = LASTFM_TRACK_INFO_URL.format(artist=artist, track=track)
    response = requests.get(url)
    data = response.json()
    if 'track' in data:
        track_info = data['track']
        genre = track_info['toptags']['tag'][0]['name'] if track_info['toptags']['tag'] else ''
        return genre
    return ''

def search_official_video(song_title, artist):
    search_query = f'{artist} {song_title} official video'
    search_url = f'https://www.youtube.com/results?search_query={search_query}'

    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'skip_download': True
    }

    with YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(search_url, download=False)
        if 'entries' in result:
            return f"https://www.youtube.com/watch?v={result['entries'][0]['id']}"
    return None

def download_song(video_url, song_title, artist, album, genre):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, f'{song_title}.mp4'),
        'postprocessors': [{
            'key': 'FFmpegMetadata',
            'add_metadata': True,
            'metadata_from_title': '%(artist)s - %(title)s'
        }],
        'postprocessor_args': [
            '-metadata', f'album={album}',
            '-metadata', f'genre={genre}'
        ]
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    logger.info(f'Successfully downloaded {song_title} by {artist}')

    # Add metadata to the downloaded file
    downloaded_file = os.path.join(DOWNLOAD_PATH, f'{song_title}.mp4')
    ffmpeg_command = [
        'ffmpeg', '-i', downloaded_file,
        '-metadata', f'album={album}',
        '-metadata', f'genre={genre}',
        '-codec', 'copy',
        os.path.join(DOWNLOAD_PATH, f'{song_title}_tagged.mp4')
    ]
    logger.info(f'Adding metadata for {song_title} by {artist}')
    subprocess.run(ffmpeg_command)

    # Replace the original file with the tagged file
    os.rename(os.path.join(DOWNLOAD_PATH, f'{song_title}_tagged.mp4'), downloaded_file)
    logger.info(f'Successfully processed {song_title} by {artist}')

if __name__ == "__main__":
    last_downloaded_timestamp = get_last_downloaded_timestamp()

    while True:
        try:
            logger.info('Polling Last.fm for recent tracks')
            recent_tracks = get_recent_tracks(last_downloaded_timestamp)

            if recent_tracks:
                for track in reversed(recent_tracks):
                    song_title = track['name']
                    artist = track['artist']['#text']
                    album = track.get('album', {}).get('#text', '')
                    timestamp = track['date']['uts']

                    downloaded_file = os.path.join(DOWNLOAD_PATH, f'{song_title}.mp4')
                    if not os.path.exists(downloaded_file):
                        video_url = search_official_video(song_title, artist)
                        if video_url:
                            logger.info(f'Found official video: {video_url}')
                            genre = get_track_info(artist, song_title)
                            download_song(video_url, song_title, artist, album, genre)
                        else:
                            logger.info('No official video found')

                    save_last_downloaded_timestamp(timestamp)

            time.sleep(POLLING_INTERVAL)
        except Exception as e:
            logger.error(f'An error occurred: {e}')
            time.sleep(POLLING_INTERVAL)
