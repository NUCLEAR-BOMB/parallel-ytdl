import subprocess
import threading
import queue
import sys
import argparse
import shutil
import os
import multiprocessing

def invoke_single_downloader(args, download_queue, lock, name_formatter):
    while True:
        url = download_queue.get()
        full_command = args + [*(name_formatter.extra if name_formatter else ()), url]
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        std_output, std_error = process.communicate()
        encoding = sys.getdefaultencoding()
        if name_formatter != None:
            name_formatter(std_output.decode(encoding).rstrip())

        if len(std_error) != 0:
            with lock:
                sys.stderr.write(
                    "Failed with: " + " ".join(full_command) + '\n' +
                    std_error.decode('ascii').rstrip('\n')
                )
        download_queue.task_done()

def invoke_downloaders(args, download_list, name_formatter):
    max_downloaders = min(len(download_list), multiprocessing.cpu_count())

    download_queue = queue.Queue(max_downloaders)
    lock = threading.Lock()

    for _ in range(max_downloaders):
        threading.Thread(target=invoke_single_downloader, args=(
            args, download_queue, lock, name_formatter
        ), daemon=True).start()
    
    for url in download_list:
        download_queue.put(url)

    download_queue.join()

def apply_download_preset(name):
    if name == 'audio': 
        return ['--format', 'ba', '--audio-format', 'mp3', '-x']
    return []
    
def find_download_executable(arg):
    if arg == None:
        ytdlp_path = shutil.which('yt-dlp')
        if ytdlp_path != None: return ytdlp_path
        youtube_dl_path = shutil.which('youtube-dl')
        if youtube_dl_path != None: return youtube_dl_path
        sys.exit('error: cannot find downloader binary')
    else:
        custom_exec_path = shutil.which(arg)
        if custom_exec_path != None: return custom_exec_path
        sys.exit("error: downloader '{}' was not found or is not executable".format(arg))

def extract_download_list(filename):
    with open(filename) as file:
        download_list = file.readlines()
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
    def __init__(self) -> None:
        self._delim = '&#&#&' 
        self.extra = ('-o', '%(channel)s{0}%(title)s'.format(self._delim), 
                      '--print', 'after_move:filepath')

    def _format(self, author, title):
        author = remove_postfix(author, ' - Topic')
        if title.endswith(author):
            title = title[:-len(author)].rstrip(' -')
        elif title.startswith(author):
            title = title[len(author):].lstrip(' -')
        
        return author, title

    def __call__(self, path):
        filename, fileext = os.path.splitext(os.path.basename(path))
        author, title = self._format(*filename.split(self._delim))
        
        try:
            os.rename(path, '{0} - {1}{2}'.format(author, title, fileext))
        except FileExistsError as err:
            sys.stderr.write("'{}' file exists'\n".format(err.filename2))
            os.remove(path)

def select_name_formatter(preset):
    if preset == None: return None

    if preset == 'author-title': return AuthorTitleFormatter()

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--download-preset', choices=('audio',))
    parser.add_argument('--exec', metavar='PATH')
    parser.add_argument('--list', type=file_path, metavar='PATH', default='list.txt')
    parser.add_argument('--output-preset', choices=('author-title',))
    parser.add_argument('downloader_args', nargs='*')

    args = parser.parse_args()
    dl_args = args.downloader_args
    dl_args += apply_download_preset(args.download_preset)

    dl_exec = find_download_executable(args.exec)

    dl_list = extract_download_list(args.list)

    name_formatter = select_name_formatter(args.output_preset)
    invoke_downloaders([dl_exec] + dl_args, dl_list, name_formatter)

if __name__ == '__main__':
    main()
