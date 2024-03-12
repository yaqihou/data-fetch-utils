
import argparse
import logging

from src.wallhaven.enums import Purity, Category
from src.wallhaven.fetcher import DailyFetcher

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--download-files', action='store_true')
parser.add_argument('-f', '--fetch-details', action='store_true')
parser.add_argument('-D', '--dir', nargs='?', type=str, default=None)
parser.add_argument('-p', '--page', nargs='?', type=str, default='1-50',
                    help="Range of page to dwonload, use dash (-) for range, comma for separation")
parser.add_argument('-i', '--interval', nargs='?', type=int, default=2)
parser.add_argument('-C', '--categories', nargs='?', type=str, default='111',
                    help='Flag for categories (General/Anime/People) in form of 101 (Default 111)'
                    )
parser.add_argument('-P', '--purities', nargs='?', type=str, default='110',
                    help='Flag for categories (SFW/Sketchy/NSFW) in form of 110 (Default 110)')
parser.add_argument('-l', '--log-file', nargs='?', type=str, default=None)
parser.add_argument('-o', '--keep-output', action='store_true',
                    help='Leave output when set log-file')

args = parser.parse_args()

logger = logging.getLogger('data-fetch-utils.wallhaven.fetcher')
logger.handlers.clear()

formatter = logging.Formatter(
    fmt='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel('logging.DEBUG')

if args.log_file is not None:
    file_handler = logging.FileHandler(args.log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel('logging.INFO')

    logger.addHandler(file_handler)

if args.log_file is None or args.keep_output:
    logger.addHandler(stream_handler)

# TODO - add sanity check
purities = Purity(int(args.purities, base=2))
categories = Category(int(args.categories, base=2))
page_range = []
for rng in args.page.split(','):
    rng = rng.strip()
    if '-' in rng:
        s, e = rng.split('-')
        page_range.extend(range(int(s), int(e)))
    else:
        page_range.append(int(rng))


daily_fetcher = DailyFetcher(
    fetch_wallpaper_details=args.fetch_details,
    download_file=args.download_files,
    base_dir=args.dir,
    page_range=page_range,
    purities=purities,
    categories=categories,
    interval=args.interval
)
daily_fetcher.run()
