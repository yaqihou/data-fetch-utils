
import os
import abc
import time
import pickle
from typing import Iterable, Optional
import requests
import logging
from tqdm import tqdm

from .defs import Wallpaper 
from .enums import Purity, Category, Sorting, SortingOrder, TopRange, Color
from .api import API
from ..exceptions import TooManyRequestsError, UnknownResponseError

logger = logging.getLogger('data-fetch-utils.wallhaven.fetcher')

class Fetcher(abc.ABC):

    cache_file = os.path.join(os.getenv('HOME') or '.',
                              '.cache',
                              'data-fetch-utils',
                              'wallhaven_downloaded.pkl')

    last_download_time: float = time.time() 

    if os.path.isfile(cache_file):
        with open(cache_file, 'rb') as f:
            cache = pickle.load(f)
        logger.debug(f'Loaded {len(cache)} entries from cache file {cache_file}')
    else:
        logger.debug(f'Cache file {cache_file} does not exist, create an empty one')
        cache = {}

    def __init__(self,
                 fetch_wallpaper_details: bool = True,
                 download_file: bool = True,
                 base_dir: Optional[str] = None,
                 max_retries: int = 5,
                 interval: int = 2
                 ):

        self.need_fetch_wallpaper_details = fetch_wallpaper_details
        self.need_download_file = download_file
        self.base_dir = base_dir if base_dir is not None else (os.getenv('WALLHAVEN_DIR') or '.')
        self.max_retries: int = max_retries
        self.interval = interval

        self.api = API(max_retries=max_retries, request_interval=interval)

        logger.info("Fetcher initialize setup")
        logger.info(f'Need to fetch wallpaper details: {self.need_fetch_wallpaper_details}')
        logger.info(f'Need to download wallpaper file: {self.need_download_file}')
        logger.info(f'Base dir to save wallpaper: {self.base_dir}')
        logger.info(f'Max retries: {self.max_retries}')
        logger.info(f'Request interval {self.interval}')

    def add_to_cache(self, wallpaper: Wallpaper):
        self.cache[wallpaper.id] = wallpaper.json

    def save_cache(self):
        dirname = os.path.dirname(self.cache_file)
        if not os.path.isdir(dirname):
            logger.debug(f'Cache folder {dirname} does not exist, create one')
            os.makedirs(dirname)

        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)
            logging.debug(f'Saved {len(self.cache)} cached entries to {self.cache_file}')

    def download(self, wallpaper: Wallpaper, **kwargs):

        save_path = self._get_save_path(wallpaper)
        success = False
        if os.path.isfile(save_path):
            logger.info(f"Wallpaper {wallpaper.id} has existing file {save_path}")
        else:
            retry = 0
            while retry < self.max_retries:
                try:
                    self._download(wallpaper.path, save_path, **kwargs)
                except TooManyRequestsError as e:
                    logger.debug("Encountered 429 error when downloading")
                    time.sleep(5)
                except Exception as e:
                    logger.error(f"Encounter error when downloading {wallpaper.id} from {wallpaper.path}",
                                exc_info=e)
                    break
                else:
                    success = True
                    break

        return success

    def _download(self, url, save_path, no_progress: bool = True, total_size=None) -> bool:

        while time.time() - self.last_download_time < self.interval:
            time.sleep(1)
        
        r = requests.get(url, stream=True)
        
        if r.status_code == 429:
            raise TooManyRequestsError
        elif r.status_code != 200:
            raise UnknownResponseError(r)
        
        total_size = int(r.headers.get('content-length', 0))
        chunk_size = 32 * 1024

        dirname = os.path.dirname(save_path)
        if not os.path.isdir(dirname):
            logger.debug(f'Making directory {dirname}')
            os.makedirs(dirname)

        wrote = 0
        with tqdm(total=total_size, unit='B', unit_scale=True, miniters=1, disable=no_progress) as bar:
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size):

                    bar.update(len(chunk))
                    wrote += int(len(chunk))
                    f.write(chunk)
        r.close()

        return wrote == total_size

    @abc.abstractmethod
    def get_wallpapers(self) -> list[Wallpaper]:
        """Return a list of wallpaper instance to be downloaded"""

    def fetch_wallpaper_details(self, wallpapers):
        
        for wall in tqdm(wallpapers, desc="Updating wallpaper details"):

            if wall.id in self.cache:
                logger.info(f'Wallpaper details for {wall.id} existed in cache')
                wall.update(self.cache[wall.id])
            else:
                logger.info(f'Fetching details for {wall.id}')
                r = self.api.get_wallpaper_info(wid=wall.id)
                json = r.json()
                if "error" in json:
                    logger.warning(f"Encountered error when fetching details for wallpaper {wall.id}")
                else:
                    wall.update(json['data'])
                    self.add_to_cache(wall)

        self.save_cache()

    def _get_save_path(self, wallpaper: Wallpaper) -> str:
        
        basename = wallpaper.path.split('/')[-1]
        subfolder = basename[:2]
        save_path = os.path.join(self.base_dir, subfolder, basename)

        return save_path

    def run(self):

        wallpapers = self.get_wallpapers()

        if self.need_fetch_wallpaper_details:
            self.fetch_wallpaper_details(wallpapers)

        if self.need_download_file:
            download_status = {}
            for wallpaper in tqdm(wallpapers, desc='Downloading wallpapers'):
                download_status[wallpaper] = self.download(wallpaper)

            num_success = sum(download_status.values())

            logger.info(f"Download finished: succeeded {num_success} / failed {len(wallpapers) - num_success}")
            if num_success != len(wallpapers):
                for wall, status in download_status.items():
                    if not status:
                        logger.info(f"Failed to download for wallpaper {wall.id} @ {wall.path}")


class DailyFetcher(Fetcher):
    """Fetch from the latest list"""

    def __init__(self,
                 fetch_wallpaper_details: bool = True,
                 download_file: bool = True,
                 base_dir: Optional[str] = None,
                 max_retries: int = 5,
                 interval: int = 2,
                 page_range: Iterable[int] = range(1, 50+1),
                 purities: Purity = Purity.SFW + Purity.SKETCHY,
                 categories: Category = Category.ALL):

        super().__init__(
            fetch_wallpaper_details=fetch_wallpaper_details,
            download_file=download_file,
            base_dir=base_dir,
            max_retries=max_retries,
            interval=interval)

        self.page_range: Iterable[int] = page_range
        self.purities: Purity = purities
        self.categories: Category = categories

    def get_wallpapers(self) -> list[Wallpaper]:
        ret = []
        for page in self.page_range:
            logger.info(f"Searching wallpapers on page {page}")
            r = self.api.search(
                purity=self.purities,
                categories=self.categories,
                sorting=Sorting.DATE_ADDED,
                page=page
            )

            json_data = r.json()['data']

            logger.info(f"Found {len(json_data)} wallpapers on page {page}")
            for json in json_data:
                ret.append(Wallpaper(json))
        
        logger.info(f"Found {len(ret)} wallpapers in total.")

        return ret


class QueryFetcher(Fetcher):

    def query(
            self,
            q: Optional[str] = None,
            categories: Optional[Category] = None,
            purity: Optional[Purity] = None,
            sorting: Optional[Sorting] = None,
            order: Optional[SortingOrder] = None,
            top_range: Optional[TopRange] = None,
            atleast: Optional[str] = None,
            resolutions: Optional[list[str]] = None,
            ratios: Optional[list[str]] = None,
            colors: Optional[Color] = None,
            page: Optional[str] = None,
            seed: Optional[str] = None):
        pass

    # def _get_wallpapers(self)


