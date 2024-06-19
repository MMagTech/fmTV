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

- `LASTFM_USERNAME`: Your Last.fm username to fetch recent tracks.
- `LASTFM_API_KEY`: Your Last.fm API key for accessing Last.fm services.
- `POLLING_INTERVAL`: Interval (in seconds) between Last.fm API polls (`300` seconds by default).
- `DOWNLOAD_PATH`: Directory where downloaded videos will be saved (`/downloads` by default).
- `APP_DATA_PATH`: Directory for storing application data and logs (`/appdata` by default).



### Obtain an API key from Last.fm

This script assumes you already have a Last.fm account and are scrobbling succesfully

**Log In:**
Log in to your Last.fm account.

**Go to the API Page:**
Navigate to the Last.fm API page by going to https://www.last.fm/api.

**Create an API Account:**
On the API page, you’ll see an option to create an API account. Click on "Create API account."

**Fill Out the Application Form:**
You will be asked to fill out a form with details about your application. Provide the following information:

Application Name: A name for your application
Application Description: A brief description of what your application does.
Application Website: Not Applicable
Application Redirect URI: Not Applicable
Agreement to Terms: Check the box to agree to the API Terms of Use.

**Submit the Form:**
After filling out the form, submit it. Last.fm will process your request, and once approved, you will receive an API key.

**Access Your API Key:**
After approval, you can access your API key from the API page under your account.
