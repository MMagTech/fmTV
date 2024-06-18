# Use a base image with Python
FROM python:3.9-slim

# Set environment variables
ENV LASTFM_API_KEY=your_lastfm_api_key
ENV LASTFM_USERNAME=your_lastfm_username
ENV DOWNLOAD_PATH=/downloads
ENV APP_DATA_PATH=/appdata
ENV POLLING_INTERVAL=300

# Install yt-dlp and ffmpeg
RUN apt-get update && apt-get install -y ffmpeg \
    && pip install --no-cache-dir yt-dlp

# Create directories for downloads and app data
RUN mkdir -p $DOWNLOAD_PATH $APP_DATA_PATH

# Copy your application code into the container
COPY . /app

# Set the working directory
WORKDIR /app

# Default command to run your application
CMD ["python", "fmtv-downloader.py"]
