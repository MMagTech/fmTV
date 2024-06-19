import os
import time
import requests
import subprocess
import logging
import numpy as np
import ffmpeg

from logging.handlers import TimedRotatingFileHandler
from yt_dlp import YoutubeDL

# Environment variables
USERNAME = os.getenv('LASTFM_USERNAME', 'your_lastfm_username')
API_KEY = os.getenv('LASTFM_API_KEY', 'your_lastfm_api_key')
POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', '300'))  # Default to 300 seconds (5 minutes)
DOWNLOAD_PATH = '/downloads'  # Hardcoded path
APP_DATA_PATH = '/appdata'  # Hardcoded path

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
            genre = track_info['toptags']['tag'][0]['name'] if track_info['toptags']['tag'] else ''
            return genre
    logger.error(f'Failed to fetch track info for {artist} - {track}: {response.status_code}')
    return ''

def search_video(song_title, artist):
    search_query = f'{artist} {song_title}'
    ydl_opts = {
        'format': 'best',
        'noplaylist': True,
        'quiet': True
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f'ytsearch:{search_query}', download=False)['entries']
            
            official_videos = [
                entry for entry in result 
                if 'official' in entry['title'].lower()
            ]
            
            remaster_videos = []
            if not official_videos:
                remaster_videos = [
                    entry for entry in result 
                    if 'remaster' in entry['title'].lower() or 'remaster' in entry.get('description', '').lower()
                ]

            if official_videos:
                logging.info(f'Found official video: {official_videos[0]["title"]}')
                return official_videos[0]['webpage_url']
            elif remaster_videos:
                logging.info(f'Found remastered video: {remaster_videos[0]["title"]}')
                return remaster_videos[0]['webpage_url']
            elif result:
                logging.info(f'Found other video: {result[0]["title"]}')
                return result[0]['webpage_url']
            else:
                logging.info('No videos found')
                return None
    except Exception as e:
        logging.error(f'Error occurred: {e}')
        return None

def download_song(video_url, song_title, artist, album, genre):
    file_name = f'{artist} - {song_title}.mp4'
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, file_name),
        'merge_output_format': 'mp4'
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    downloaded_file = os.path.join(DOWNLOAD_PATH, file_name)

    # Check if the downloaded file is a static image
    if is_static_image_for_5_seconds_ffmpeg(downloaded_file):
        os.remove(downloaded_file)
        logger.info(f'Deleted static image file: {downloaded_file}')
        return

    # Add metadata
    tagged_file_name = f'{artist} - {song_title}_tagged.mp4'
    ffmpeg_command = [
        'ffmpeg',
        '-i', downloaded_file,
        '-metadata', f'title={song_title}',
        '-metadata', f'artist={artist}',
        '-metadata', f'album={album}',
        '-metadata', f'genre={genre}',
        '-codec', 'copy',
        os.path.join(DOWNLOAD_PATH, tagged_file_name)
    ]
    logger.info(f'Adding metadata for {song_title} by {artist}')
    subprocess.run(ffmpeg_command, check=True)

    # Replace the original file with the tagged file
    os.rename(os.path.join(DOWNLOAD_PATH, tagged_file_name), downloaded_file)
    logger.info(f'Successfully processed {song_title} by {artist}')
    
def extract_frame(video_path, time):
    cmd = [
        'ffmpeg',
        '-ss', str(time),
        '-i', video_path,
        '-frames:v', '1',
        '-f', 'image2pipe',
        '-pix_fmt', 'rgb24',
        '-vcodec', 'rawvideo',
        '-'
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(f"Error extracting frame at {time} seconds: {result.stderr.decode()}")
    return np.frombuffer(result.stdout, np.uint8)

def is_static_image_for_5_seconds_ffmpeg(video_path):
    try:
        # Extract frames from the first 5 seconds
        duration = 5  # seconds
        frames = []
        for t in range(0, duration):
            frame = extract_frame(video_path, t)
            frames.append(frame)

        # Compare each frame with the first frame
        first_frame = frames[0]
        for frame in frames[1:]:
            if not np.array_equal(first_frame, frame):
                return False
        return True
    except Exception as e:
        logger.error(f"Error checking if video is static image: {e}")
        return False

def delete_if_static(video_path):
    if is_static_image_for_5_seconds_ffmpeg(video_path):
        try:
            os.remove(video_path)
            logger.info(f"Deleted static image: {video_path}")
        except OSError as e:
            logger.error(f"Error deleting file: {e}")
    else:
        logger.info(f"File is not a static image: {video_path}")

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
                        video_url = search_video(song_title, artist)
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
