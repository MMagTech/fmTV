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
- `YOUTUBE_API_KEY` = Google Developer APIU key for Youtube Data API v3

### Obtaining a Developer Key from Google Developer Console

Used for downloading metadata and setting thumbnail

**To obtain an API key from the Google Developer Console, follow these steps:**

Go to the Google Developer Console:


**Create a New Project:**

Click on the project drop-down menu at the top of the page.
Click on "New Project".
Enter a project name and click "Create".
**Enable YouTube Data API:**

With your new project selected, go to the left-hand menu and click on "Library".
In the search bar, type "YouTube Data API v3" and select it from the search results.
Click the "Enable" button.

**Create Credentials:**

Go to the left-hand menu and click on "Credentials".
Click on "Create Credentials" at the top of the page.
Select "API key".
A dialog will appear with your new API key. You can copy this key to use in your script.

**Restrict API Key (Optional but recommended):**

Click on the "Restrict key" button in the dialog where your API key is displayed.
Under "API restrictions", select "Restrict key" and choose "YouTube Data API v3".
Under "Application restrictions", you can specify the type of applications that can use this key (e.g., HTTP referrers, IP addresses, etc.).
Click "Save".
