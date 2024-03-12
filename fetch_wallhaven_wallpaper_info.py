
import os
import sys
import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument('wall_ids', nargs='+', type=str, default=[],
                    help='Waiting interval between two downloads or requests')
parser.add_argument('-d', '--download-files', action='store_true',
                    help="Whether to download image files (Default False)")
parser.add_argument('-D', '--dir', nargs='?', type=str, default=None,
                    help="Base directory to save wallpaper files, if not given, environment variable WALLHAVEN_DIR or current folder will be used")
parser.add_argument('-I', '--input', nargs='?', type=str, default="",
                    help='Input file containing one wallpaper id per line')
parser.add_argument('-i', '--interval', nargs='?', type=int, default=2,
                    help='Waiting interval between two downloads or requests')
parser.add_argument('-l', '--log-file', nargs='?', type=str, default=None,
                    help='Log file to store logging information')
parser.add_argument('-o', '--keep-output', action='store_true',
                    help='Leave output when set log-file')

args = parser.parse_args()

logger = logging.getLogger('data-fetch-utils.wallhaven')
logger.handlers.clear()

formatter = logging.Formatter(
    fmt='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p')

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)

if args.log_file is not None:
    file_handler = logging.FileHandler(args.log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)

if args.log_file is None or args.keep_output:
    logger.addHandler(stream_handler)

logger.setLevel(logging.DEBUG)

from src.wallhaven.fetcher import IDFetcher

wall_ids = args.wall_ids
if os.path.isfile(args.input):
    with open(args.input, 'r') as f:
        data = f.readlines()
    wall_ids += data

id_fetcher = IDFetcher(
    wall_ids = wall_ids,
    download_file=args.download_files,
    base_dir=args.dir,
    interval=args.interval
)
id_fetcher.run()
