# fmTV Downloader

![fmTV Downloader](assets/icon.png)

## Overview

The `fmTV Downloader` is a Python-based application designed to fetch and download music videos based on data from Last.fm. It uses the Last.fm API to retrieve recently played tracks and searches YouTube for official music videos matching those tracks. The downloaded videos are tagged with metadata and stored in a specified directory.

## Features

- **Track Retrieval:** Polls Last.fm for recent tracks on a set interval.
- **Video Search and Download:** Searches YouTube for hihest quality video and audio for a music video and downloads and merges them to .mp4
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

