
# parallel-ytdl

Utility for parallel video/audio download

## Options

- `--list PATH` (default: `list.txt`) Download videos from the list. One URL per line
- `--exec PATH` (default: `yt-dlp` or `youtube-dl`) Downloader executable path
- `--download-preset {audio}` Preset for downloading videos
	- `audio` Downloads the best audio quality and converts the file to `mp3` format
- `--output-preset {author-title}` Output filename formatter
	- `author-title` Tries to rename the file to the `"author - title.ext"` format
- `-- ... ` Additional parameters for each downloader being launched
