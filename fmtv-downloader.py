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
            genre = track_info['toptags']['tag'][0]['name'] if 'toptags' in track_info and 'tag' in track_info['toptags'] else 'Unknown'
            return genre
        else:
            return 'Unknown'
    else:
        logger.error(f'Failed to fetch track info: {response.status_code}')
        return 'Unknown'

def search_official_video(song_title, artist):
    query = f'{artist} {song_title} official music video'
    search_url = f'https://www.youtube.com/results?search_query={query.replace(" ", "+")}'
    logger.info(f'Searching for video: {search_url}')
    response = requests.get(search_url)
    if response.status_code == 200:
        html = response.text
        video_id = html.split('href="/watch?v=')[1].split('"')[0]
        return f'https://www.youtube.com/watch?v={video_id}'
    else:
        logger.error(f'Failed to search for video: {response.status_code}')
        return None

def download_song(video_url, song_title, artist, album, genre):
    logger.info(f'Downloading {song_title} by {artist}')
    download_options = {
        'format': 'bestvideo[height<=1080]+bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, f'{artist} - {song_title}.%(ext)s'),
        'verbose': True,  # Enable verbose logging
        'logger': logger,  # Use the same logger for yt-dlp
        'merge_output_format': 'mp4',  # Ensure the final output is in mp4 format
        'progress_hooks': [my_hook],  # Optional: add a progress hook
    }
    try:
        with YoutubeDL(download_options) as ydl:
            ydl.download([video_url])
        logger.info(f'Successfully downloaded {song_title} by {artist}')
    except Exception as e:
        logger.error(f'Failed to download {song_title} by {artist}: {e}')

def my_hook(d):
    if d['status'] == 'finished':
        logger.info('Done downloading, now converting...')

if __name__ == "__main__":
    last_downloaded_track = None

    while True:
        try:
            logger.info('Polling Last.fm for recent tracks')
            recent_tracks = get_recent_tracks()

            # Get the most recent track
            if recent_tracks:
                most_recent_track = recent_tracks[0]
                song_title = most_recent_track['name']
                artist = most_recent_track['artist']['#text']
                album = most_recent_track.get('album', {}).get('#text', '')

                # Check if the most recent track is different from the last downloaded track
                if most_recent_track != last_downloaded_track:
                    last_downloaded_track = most_recent_track

                    # Check if the video file already exists
                    file_name = f'{artist} - {song_title}.mp4'
                    downloaded_file = os.path.join(DOWNLOAD_PATH, file_name)
                    if not os.path.exists(downloaded_file):
                        # Search and download the official video
                        video_url = search_official_video(song_title, artist)
                        if video_url:
                            logger.info(f'Found official video: {video_url}')
                            genre = get_track_info(artist, song_title)
                            download_song(video_url, song_title, artist, album, genre)
                        else:
                            logger.info('No official video found')
                    else:
                        logger.info(f'Video already downloaded: {downloaded_file}')
            else:
                logger.info('No recent tracks found')

            time.sleep(POLLING_INTERVAL)
        except Exception as e:
            logger.error(f'An error occurred: {e}')
            time.sleep(POLLING_INTERVAL)
