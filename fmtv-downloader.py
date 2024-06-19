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

def get_recent_tracks(from_timestamp=None):
    url = LASTFM_URL
    if from_timestamp:
        url += f'&from={from_timestamp}'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        recent_tracks = data['recenttracks']['track']
        return recent_tracks
    except Exception as e:
        logger.error(f"Error fetching recent tracks: {e}")
        return []

def get_track_info(artist, track):
    try:
        url = LASTFM_TRACK_INFO_URL.format(artist=artist, track=track)
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'track' in data:
            track_info = data['track']
            tags = []
            if 'toptags' in track_info and 'tag' in track_info['toptags']:
                tags = [tag['name'] for tag in track_info['toptags']['tag']]
            return tags
        return []
    except Exception as e:
        logger.error(f"Error fetching track info for {artist} - {track}: {e}")
        return []

def search_official_video(song_title, artist):
    search_query = f'{artist} {song_title} official video'
    search_url = f'https://www.youtube.com/results?search_query={search_query}'

    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'force_generic_extractor': True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_url, download=False)
            if 'entries' in result:
                for entry in result['entries']:
                    title = entry.get('title', '').lower()
                    if 'official' in title and 'video' in title:
                        return entry['url']
    except Exception as e:
        logger.error(f"Error searching for official video: {e}")
    return None

def download_song(video_url, song_title, artist, album, tags):
    output_template = f'{DOWNLOAD_PATH}/%(title)s.%(ext)s'
    ytdlp_command = [
        'yt-dlp',
        '-f', 'bestvideo+bestaudio',
        '--merge-output-format', 'mp4',
        '--output', output_template,
        video_url
    ]
    logger.info(f'Downloading video for {song_title} by {artist}')
    subprocess.run(ytdlp_command)

    # Get the downloaded file name
    downloaded_file = os.path.join(DOWNLOAD_PATH, f'{song_title}.mp4')

    # Add metadata tags using ffmpeg
    ffmpeg_args = [
        'ffmpeg',
        '-i', downloaded_file,
        '-metadata', f'title={song_title}',
        '-metadata', f'artist={artist}',
        '-metadata', f'album={album}'
    ]
    
    # Add tags as metadata
    for tag in tags:
        ffmpeg_args.extend(['-metadata', f'tag={tag}'])

    ffmpeg_args.extend(['-codec', 'copy', os.path.join(DOWNLOAD_PATH, f'{song_title}_tagged.mp4')])
    logger.info(f'Adding metadata for {song_title} by {artist}')
    subprocess.run(ffmpeg_args)

    # Replace the original file with the tagged file
    os.rename(os.path.join(DOWNLOAD_PATH, f'{song_title}_tagged.mp4'), downloaded_file)
    logger.info(f'Successfully processed {song_title} by {artist}')

if __name__ == "__main__":
    last_downloaded_timestamp = None

    while True:
        logger.info('Polling Last.fm for recent tracks')
        
        # Fetch recent tracks since the last successful download
        recent_tracks = get_recent_tracks(from_timestamp=last_downloaded_timestamp)

        # Process each track
        if recent_tracks:
            for track in recent_tracks:
                timestamp = int(track['date']['uts'])
                if timestamp > last_downloaded_timestamp:
                    last_downloaded_timestamp = timestamp
                    
                    song_title = track['name']
                    artist = track['artist']['#text']
                    album = track.get('album', {}).get('#text', '')

                    # Check if the video file already exists
                    downloaded_file = os.path.join(DOWNLOAD_PATH, f'{song_title}.mp4')
                    if not os.path.exists(downloaded_file):
                        # Search and download the official video
                        video_url = search_official_video(song_title, artist)
                        if video_url:
                            logger.info(f'Found official video: {video_url}')
                            tags = get_track_info(artist, song_title)
                            download_song(video_url, song_title, artist, album, tags)
                        else:
                            logger.info('No official video found')
                    else:
                        logger.info(f'Video already downloaded: {downloaded_file}')

        time.sleep(POLLING_INTERVAL)
