Rule34 Downloader

The primary purpose of this tool is to facilitate the systematic archiving and
preservation of digital media for local storage.

Releases

A standalone Windows executable is available in the Releases section. Download
the .zip file, extract it, and run the .exe to use the application without
installing Python.

Features

  - Tag Filtering: Supports standard searches and exclusion tags (e.g.,
    sakura_haruno -video).
  - Persistent State: Saves current page, download path, tags, and history of
    downloaded IDs to config_state.json.
  - Duplicate Prevention: Checks both the local history file and the physical
    disk before downloading.
  - Adjustable Delay: User-controlled slider for request delays (2s to 60s) to
    avoid rate-limiting.
  - Resumable: Can resume from a specific page number and migrates data from
    legacy download_state.json files.

Prerequisites (for Source Code)

  - Python 3.10 or higher.
  - Required libraries:
    pip install customtkinter requests beautifulsoup4

Usage

1.  Run the application via python rule34_downloader.py or the provided .exe.
2.  Select a download directory using the Browse Folder button.
3.  Enter desired tags in the Search Tags field.
4.  Press Start / Resume to begin.

Configuration

The application generates a config_state.json file to store your last used
directory, last processed page, and a list of all successfully downloaded post
IDs.

Building from Source

To compile into a standalone executable:

1.  Install PyInstaller:
    pip install pyinstaller
2.  Run the build command:
    python -m PyInstaller --noconsole --onefile --icon=icon.ico --collect-all customtkinter --add-data "icon.ico;." rule34_downloader.py

Disclaimer

This tool is for personal use only. Users are responsible for complying with the
target website's terms of service and local copyright laws.
