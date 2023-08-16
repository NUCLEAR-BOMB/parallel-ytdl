import subprocess
import threading
import queue
import sys
import argparse
import shutil
import os
import multiprocessing

def invoke_single_downloader(args, download_queue, lock, name_formatter, done_cache):
    while True:
        if done_cache is not None:
            url, cache = download_queue.get()
        else:
            url = download_queue.get()
        full_command = args + [*(name_formatter.extra if name_formatter else ()), url]
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        std_output, std_error = process.communicate()
        encoding = sys.getdefaultencoding()
        if name_formatter is not None:
            name_formatter(std_output.decode(encoding).rstrip())

        if len(std_error) != 0:
            with lock:
                sys.stderr.write(
                    "Failed with: " + " ".join(full_command) + '\n' +
                    std_error.decode('ascii').rstrip('\n')
                )
        download_queue.task_done()
        if done_cache is not None: done_cache.append(cache)

def invoke_downloaders(args, download_list, name_formatter, done_cache):
    max_downloaders = min(len(download_list), multiprocessing.cpu_count())

    download_queue = queue.Queue(max_downloaders)
    lock = threading.Lock()

    for _ in range(max_downloaders):
        threading.Thread(target=invoke_single_downloader, args=(
            args, download_queue, lock, name_formatter, done_cache
        ), daemon=True).start()
    
    for url_and_cache in download_list:
        download_queue.put(url_and_cache)

    download_queue.join()

def apply_download_preset(name):
    if name == 'audio': 
        return ['--format', 'ba', '--audio-format', 'mp3', '-x']
    return []
    
def find_download_executable(arg):
    if arg is None:
        ytdlp_path = shutil.which('yt-dlp')
        if ytdlp_path is not None: return ytdlp_path
        sys.exit("error: cannot find 'yt-dlp' binary. Please consider downloading it from 'https://github.com/yt-dlp/yt-dlp'")
    else:
        custom_exec_path = shutil.which(arg)
        if custom_exec_path is not None: return custom_exec_path
        sys.exit("error: downloader '{}' was not found or is not executable".format(arg))

def extract_download_list(filename):
    if not os.path.isfile(filename):
        sys.exit('error: {} is not exists'.format(filename))

    with open(filename, 'r') as cache:
        download_list = cache.read().splitlines()

    if len(download_list) == 0:
        print('warning: {} is empty'.format(filename))
    return download_list

def file_path(string):
    if os.path.isfile(string):
        return string
    raise argparse.ArgumentTypeError("file '{}' not found".format(string))

def remove_postfix(text, prefix):
    if text.endswith(prefix):
        return text[:-len(prefix)]
    return text

class AuthorTitleFormatter:
    def __init__(self):
        self._delim = '&#&#&' 
        self.extra = ('-o', '%(channel)s{0}%(title)s'.format(self._delim), 
                      '--print', 'after_move:filepath')

    def _format(self, author, title):
        author = remove_postfix(author, ' - Topic')
        if title.endswith(author):
            title = title[:-len(author)].rstrip(' -')
        elif title.startswith(author):
            title = title[len(author):].lstrip(' -')
        
        return '{0} - {1}'.format(author, title)

    def __call__(self, path):
        filename, fileext = os.path.splitext(os.path.basename(path))
        name = self._format(*filename.split(self._delim))
        
        try:
            os.rename(path, name + fileext)
        except FileExistsError as err:
            sys.stderr.write("'{}' file exists'\n".format(err.filename2))
            os.remove(path)

def select_name_formatter(preset):
    if preset is None: return None

    if preset == 'author-title': return AuthorTitleFormatter()

URL_HASH_LEN = 11
def hash_url(url):
    return url[-11:].encode()

CACHE_TRUNCATE = False
def cache_diff(urls, path):
    old_cache = set()
    if os.path.isfile(path):
        with open(path, 'rb') as cache:
            while True:
                tmp = cache.read(URL_HASH_LEN)
                if len(tmp) < URL_HASH_LEN: break
                old_cache.add(tmp)
    url_and_hash, done_cache = [], []
    for url in urls:
        url_hash = hash_url(url)
        if url_hash in old_cache:
            if CACHE_TRUNCATE: done_cache.append(url_hash)
        else:
            url_and_hash.append((url, url_hash))
    return url_and_hash, done_cache

def cache_update(urls_cache, path):
    with open(path, 'wb+' if CACHE_TRUNCATE else 'ab') as cache:
        cache.write(b''.join(urls_cache))

def str_to_bool(string):
    if string in ['', 'yes' 'true', '1']: return True
    elif string in ['false', 'no', '0']: return False
    raise argparse.ArgumentTypeError("'{}' cannot be converted to boolean".format(string))

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--download-preset', choices=('audio',))
    parser.add_argument('--exec', metavar='PATH')
    parser.add_argument('--list', type=file_path, metavar='PATH', default='list.txt')
    parser.add_argument('--output-preset', choices=('author-title',))
    parser.add_argument('--cache', metavar='PATH', default='download.cache')
    parser.add_argument('--use-cache', type=str_to_bool, nargs='?', const=True, default=True)

    args, rest = parser.parse_known_args()

    urls = rest[:rest.index('--')] if '--' in rest else rest
    dl_extra_args = rest[rest.index('--') + 1:] if '--' in rest else []

    dl_preset_args = apply_download_preset(args.download_preset)

    dl_exec = find_download_executable(args.exec)

    dl_list = extract_download_list(args.list) if len(urls) == 0 else urls
    done_cache = None
    if args.use_cache:
        dl_list, done_cache = cache_diff(dl_list, path=args.cache)

    name_formatter = select_name_formatter(args.output_preset)
    invoke_downloaders([dl_exec] + dl_preset_args + dl_extra_args, dl_list, name_formatter, done_cache)
    if args.use_cache:
        cache_update(done_cache, path=args.cache)

if __name__ == '__main__':
    main()
