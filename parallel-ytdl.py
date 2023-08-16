import subprocess
import threading
import queue
import sys
import argparse
import shutil
import os
import multiprocessing
from typing import Any

def as_tuple(x): return x if type(x) is tuple else (x,)

def invoke_single_downloader(args, download_queue, lock, name_formatter, done_cache):
    while not download_queue.empty():
        url, cache, *_ = *as_tuple(download_queue.get_nowait()), None
        full_command = args + [*name_formatter.extra, '--print', 'after_move:filepath', url]
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        std_output, std_error = process.communicate()
        encoding = sys.getdefaultencoding()
        if len(std_error) != 0 or process.returncode != 0:
            with lock:
                sys.stderr.write('Failed with: {}\n{}'.format(
                    ' '.join(full_command), std_error.decode(encoding).rstrip('\n')
                ))
        else:
            name_formatter(std_output[:std_output.index(b'\n')].decode(encoding))
            done_cache.append(cache)
        download_queue.task_done()

def invoke_downloaders(args, download_list, name_formatter, done_cache):
    max_downloaders = min(len(download_list), multiprocessing.cpu_count())
    print('info: starting {} downloaders...'.format(max_downloaders))

    download_queue = queue.Queue(max_downloaders)
    lock = threading.Lock()

    for url_and_cache in download_list:
        download_queue.put_nowait(url_and_cache)
    
    for _ in range(max_downloaders):
        threading.Thread(target=invoke_single_downloader, args=(
            args, download_queue, lock, name_formatter, done_cache
        ), daemon=True).start()

    download_queue.join()

def apply_download_preset(name):
    if name is None: return []
    return ['-f', 'ba', '-x', '--audio-format', name]
    
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

class DefaultFormatter:
    def __init__(self): self.extra = ()
    def __call__(self, path): ...

class AuthorTitleFormatter(DefaultFormatter):
    def __init__(self):
        self._delim = '&#&#&' 
        self.extra = ('-o', '%(channel)s{0}%(title)s'.format(self._delim))

    def _format(self, author, title):
        author = remove_postfix(author, ' - Topic')
        if title.endswith(author):
            title = title[:-len(author)].rstrip(' -')
        elif title.startswith(author):
            title = title[len(author):].lstrip(' -')
        
        return '{0} - {1}'.format(author, title)

    def __call__(self, path):
        assert len(path) != 0, 'result path is empty'
        filename, fileext = os.path.splitext(os.path.basename(path))
        name = self._format(*filename.split(self._delim))
        
        try:
            os.rename(path, name + fileext)
        except FileExistsError as err:
            sys.stderr.write("warning: '{}' file exists\n".format(err.filename2))
            os.remove(path)

def select_name_formatter(preset):
    if preset == 'default': return DefaultFormatter()
    if preset == 'author-title': return AuthorTitleFormatter()

URL_HASH_LEN = 11
def hash_url(url):
    return url[-11:].encode()

def cache_diff(urls, *, mode, path):
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
            if mode == 'rewrite': done_cache.append(url_hash)
        else:
            url_and_hash.append((url, url_hash))
    return url_and_hash, done_cache

def cache_update(urls_cache, *, mode, path):
    if mode == 'rewrite':
        with open(path, 'wb+') as cache:
            cache.write(b''.join(urls_cache))
    elif mode == 'append':
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT), 'rb+') as cache:
            cache.seek(-(os.path.getsize(cache.name) % URL_HASH_LEN), os.SEEK_END)
            cache.write(b''.join(urls_cache))

def str_to_bool(string):
    if string in ['yes', 'true', '1']: return True
    if string in ['false', 'no', '0']: return False
    raise argparse.ArgumentTypeError("'{}' cannot be converted to boolean".format(string))

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--download-preset', choices=('mp3', 'opus', 'm4p'))
    parser.add_argument('--exec', metavar='PATH')
    parser.add_argument('--list', type=file_path, metavar='PATH')
    parser.add_argument('--output-preset', choices=('default', 'author-title',), default='default')
    parser.add_argument('--cache', metavar='PATH', default='download.cache')
    parser.add_argument('--use-cache', type=str_to_bool, nargs='?', const=True, default=True)
    parser.add_argument('--cache-mode', choices=('append','rewrite'), default='append')

    args, rest = parser.parse_known_args()

    urls = rest[:rest.index('--')] if '--' in rest else rest
    dl_extra_args = rest[rest.index('--') + 1:] if '--' in rest else []

    dl_preset_args = apply_download_preset(args.download_preset)

    dl_exec = find_download_executable(args.exec)

    dl_list = extract_download_list(args.list) if len(urls) == 0 else urls
    if args.use_cache:
        dl_list, done_cache = cache_diff(dl_list, mode=args.cache_mode, path=args.cache)
    else:
        done_cache = []

    name_formatter = select_name_formatter(args.output_preset)
    if len(dl_list) > 0:
        invoke_downloaders([dl_exec] + dl_preset_args + dl_extra_args, dl_list, name_formatter, done_cache)
    else:
        print('info: everything up-to-date')
        
    if len(dl_list) > len(done_cache):
        print('warning: failed to download {} URLs'.format(len(dl_list) - len(done_cache)))
    else:
        print('info: download completed successfully')

    if args.use_cache:
        cache_update(done_cache, mode=args.cache_mode, path=args.cache)

if __name__ == '__main__':
    main()
