
# parallel-ytdl

Utility for parallel video/audio download. Allows to cache downloaded videos so that it is not downloaded several times

## Options

- `--list PATH` (**default**: `list.txt`) Download videos from the list. One URL per line
- `--exec PATH` (**default**: `yt-dlp` or `youtube-dl`) Downloader executable path
- `--download-preset {mp3,opus,m4p}` Preset for downloading videos
- `--output-preset {author-title}` Output filename formatter
	- `author-title` Tries to rename the file to the `"author - title.ext"` format
- `--cache PATH` (**default**: `download.cache`) The path to the file that stores the cache
- `--use-cache BOOL` (**default**: `true`) Use the cache to store downloaded videos
- `--cache-mode`
- `URL ...` List of download urls. The list file will not be used if there is at least one URL
- `-- EXTRA ... ` Additional parameters for each downloader being launched

## Examples

```bash
# Download URLs using the default configuration
$ python parallel-ytdl.py URLs...

# Download URLs from the file 'list.txt' and cache the downloaded
$ python parallel-ytdl.py

# Download URLs from the file 'list.txt' in 'mp3' format
$ python parallel-ytdl.py --download-preset=audio

# Download URLs from the file 'list.txt " in mp3 format and try to rename them in the format of the name 'author - title'
$ python parallel-ytdl.py --download-preset=audio --output-preset=author-title

# Download URLs from the file 'other_list.txt' and write their cache to 'my_downloads.cache'
$ python parallel-ytdl.py --list other_list.txt --cache my_downloads.cache

# Download URLs using the 'custom_ytdlp' program
$ python parallel-ytdl.py --exec custom_ytdlp URLs ...

# Download URLs and use a custom file name format
$ python parallel-ytdl.py -- -o "%(channel)s - %(title)s"
```
