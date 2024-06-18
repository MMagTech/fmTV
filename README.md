# fmTV

fmTV is a tool for automatically downloading music videos from YouTube based on your LastFM scrobbles.

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Using Docker](#using-docker)
  - [Manual Setup](#manual-setup)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Description

fmTV is a Python application that interfaces with LastFM to track music you listen to and automatically downloads corresponding music videos from YouTube using `yt-dlp`. This README provides instructions for setting up and running fmTV using Docker or manually.

## Features

- Automatically downloads music videos from YouTube based on LastFM scrobbles.
- Uses `yt-dlp` for flexible downloading options.
- Configurable via environment variables.

## Installation

### Prerequisites

Before installing fmTV, ensure you have the following installed:

- Docker (if using Docker installation)
- Python 3.9 or higher (if using manual setup)

### Using Docker

1. **Clone the repository:**

   ```bash
   git clone https://github.com/MMagTech/fmTV.git
   cd fmTV
