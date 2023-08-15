
# parallel-ytdl

Utility for parallel video/audio download. Allows to cache downloaded videos so that it is not downloaded several times

## Options

- `--list PATH` (**default**: `list.txt`) Download videos from the list. One URL per line
- `--exec PATH` (**default**: `yt-dlp` or `youtube-dl`) Downloader executable path
- `--download-preset {audio}` Preset for downloading videos
	- `audio` Downloads the best audio quality and converts the file to `mp3` format
- `--output-preset {author-title}` Output filename formatter
	- `author-title` Tries to rename the file to the `"author - title.ext"` format
- `--cache PATH` (**default**: `download.cache`) The path to the file that stores the cache
- `--use-cache BOOL` (**default**: `true`) Use the cache to store downloaded videos
- `URL ...` List of download urls. The list file will not be used if there is at least one URL
- `-- EXTRA ... ` Additional parameters for each downloader being launched
