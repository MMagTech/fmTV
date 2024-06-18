# fmTV Downloader

![bb2080eb-8cd2-4cbe-a253-30398bb5f2be-ezgif com-webp-to-jpg-converter-modified](https://github.com/MMagTech/fmTV/assets/64668236/5e0d6e00-78ec-4e86-a747-372bc53947d0)

## Overview

The `fmTV Downloader` is a Python-based application designed to fetch and download music videos based on data from Last.fm. It uses the Last.fm API to retrieve recently played tracks and searches YouTube for official music videos matching those tracks. The downloaded videos are tagged with metadata and stored in a specified directory.

## Features

- **Track Retrieval:** Polls Last.fm for recent tracks.
- **Video Search and Download:** Searches YouTube for official music videos and downloads them.
- **Metadata Tagging:** Tags downloaded videos with title, artist, album, and genre information.
- **Logging and Error Handling:** Maintains logs and handles errors gracefully.

## Setup and Installation

### Prerequisites

- Docker
- Docker Compose
- Last.fm Username
- Last.fm API Key



### Environment Variables

The application requires the following environment variables to be set:

- `LASTFM_API_KEY`: Your Last.fm API key for accessing Last.fm services.
- `LASTFM_USERNAME`: Your Last.fm username to fetch recent tracks.
- `DOWNLOAD_PATH`: Directory where downloaded videos will be saved (`/downloads` by default).
- `APP_DATA_PATH`: Directory for storing application data and logs (`/appdata` by default).
- `POLLING_INTERVAL`: Interval (in seconds) between Last.fm API polls (`300` seconds by default).
- START_TIMESTAMP=1624147200  # Example start timestamp (replace with your desired value in UNIX time Format)

### UNIX Time Format Website
https://www.unixtimestamp.com/
