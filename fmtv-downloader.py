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
FINAL_OUTPUT_PATH = os.getenv('FINAL_OUTPUT_PATH', '/final_output')
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
        'force_overwrites': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(query, download=False)
        if 'entries' in results:
            return results['entries'][0]['url']
    return None

def download_song(video_url, song_title, artist, album, genre):
    video_file_name = f'{artist} - {song_title}.mp4'
    audio_file_name = f'{artist} - {song_title}.m4a'
    downloaded_video = os.path.join(DOWNLOAD_PATH, video_file_name)
    downloaded_audio = os.path.join(DOWNLOAD_PATH, audio_file_name)
    final_file = os.path.join(FINAL_OUTPUT_PATH, video_file_name)

    ydl_opts_video = {
        'format': 'bestvideo',
        'outtmpl': downloaded_video,
        'force_overwrites': True,
    }
    ydl_opts_audio = {
        'format': 'bestaudio',
        'outtmpl': downloaded_audio,
        'force_overwrites': True,
    }

    with YoutubeDL(ydl_opts_video) as ydl:
        ydl.download([video_url])

    with YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([video_url])

    # Ensure both files exist before merging
    if not os.path.exists(downloaded_video) or not os.path.exists(downloaded_audio):
        logger.error(f"Video or audio file missing for {song_title} by {artist}")
        return

    # Merge video and audio with color space handling
    merge_command = [
        'ffmpeg', '-i', downloaded_video, '-i', downloaded_audio,
        '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental',
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
        final_file
    ]
    merge_result = subprocess.run(merge_command, capture_output=True, text=True)

    if merge_result.returncode != 0:
        logger.error(f"ffmpeg merge failed: {merge_result.stderr}")
        return

    logger.info(f'Successfully processed {song_title} by {artist}')

    # Cleanup temporary files
    if os.path.exists(downloaded_video):
        os.remove(downloaded_video)
    if os.path.exists(downloaded_audio):
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
                song_title = most_recent_track['name']
                artist = most_recent_track['artist']['#text']
                album = most_recent_track.get('album', {}).get('#text', '')

                # Check if the most recent track is different from the last downloaded track
                if most_recent_track != last_downloaded_track:
                    last_downloaded_track = most_recent_track

                    # Check if the video file already exists in the final output folder
                    file_name = f'{artist} - {song_title}.mp4'
                    final_file = os.path.join(FINAL_OUTPUT_PATH, file_name)
                    if not os.path.exists(final_file):
                        # Search and download the official video
                        video_url = search_official_video(song_title, artist)
                        if video_url:
                            logger.info(f'Found official video: {video_url}')
                            genre = get_track_info(artist, song_title)
                            download_song(video_url, song_title, artist, album, genre)
                        else:
                            logger.info('No official video found')
                    else:
                        logger.info(f'Video already downloaded: {final_file}')
            else:
                logger.info('No recent tracks found')

            time.sleep(POLLING_INTERVAL)
        except Exception as e:
            logger.error(f'An error occurred: {e}')
            time.sleep(POLLING_INTERVAL)
