
import os
import abc
import json
import time
from typing import Iterable, Optional
import requests
from tqdm import tqdm

from .defs import Wallpaper 
from .enums import Purity, Category, Sorting, SortingOrder, TopRange, Color, DownloadStatus
from .api import API
from .cacher import Cache

from ..exceptions import TooManyRequestsError, UnknownResponseError
from ..logger import MyLogger

logger = MyLogger('data-fetch-utils.wallhaven.fetcher')

class Fetcher(abc.ABC):

    last_download_time: float = time.time() 

    def __init__(self,
                 fetch_wallpaper_details: bool = True,
                 download_file: bool = True,
                 base_dir: Optional[str] = None,
                 max_retries: int = 5,
                 interval: int = 2):

        self.cache = Cache()

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

    def download(self, wallpaper: Wallpaper, **kwargs) -> DownloadStatus:

        save_path = self._get_save_path(wallpaper)
        status = DownloadStatus.FAILED
        if os.path.isfile(save_path):
            logger.info(f"Wallpaper {wallpaper.id} has existing file {save_path}")
            status = DownloadStatus.EXISTED
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
                    logger.info(f"Wallpaper {wallpaper.id} successfully downloaded to {save_path}")
                    status = DownloadStatus.SUCCEED
                    break

        return status

    def _download(self, url, save_path, no_progress: bool = True, total_size=None) -> bool:

        while time.time() - self.last_download_time < self.interval:
            time.sleep(.5)
        
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
        self.last_download_time = time.time()

        return wrote == total_size

    @abc.abstractmethod
    def get_wallpapers(self) -> list[Wallpaper]:
        """Return a list of wallpaper instance to be downloaded"""

    def fetch_wallpaper_details(self, wallpapers: list[Wallpaper]):
        
        save_cnt = 0
        for wall in tqdm(wallpapers, desc="Updating wallpaper details"):

            if wall.id in self.cache:
                logger.info(f'Wallpaper details for {wall.id} existed in cache')
                wall.update(self.cache[wall.id])
            else:
                try:
                    logger.info(f'Fetching details for {wall.id}')
                    r = self.api.get_wallpaper_info(wid=wall.id)
                except UnknownResponseError as e:
                    logger.warning("Encountered unknown response error when fetching details for wallpaper",
                                   exc_info=e)
                    wall.update({'path': 'ERROR'})
                else:
                    json = r.json()
                    if "error" in json:
                        logger.warning(f"Encountered error when fetching details for wallpaper {wall.id}")
                        wall.update({'path': 'ERROR'})
                    else:
                        wall.update(json['data'])

                self.cache.add(wall)

                save_cnt += 1
                if save_cnt == 200:
                    self.cache.save()
                    save_cnt = 0

        self.cache.save()

    def _get_save_path(self, wallpaper: Wallpaper) -> str:
        
        basename = wallpaper.path.split('/')[-1].removeprefix('wallhaven-')
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

            self._report_download_status(download_status)

    @staticmethod
    def _report_download_status(download_status: dict[Wallpaper, DownloadStatus]):
        num_success = sum(1 if v is DownloadStatus.SUCCEED else 0
                          for v in download_status.values())
        num_existed = sum(1 if v is DownloadStatus.EXISTED else 0
                          for v in download_status.values())
        num_failed = len(download_status) - num_existed - num_success

        logger.info(f"Download summary: {num_success} / {num_existed} / {num_failed}"
                    " (success / existed / failed)")
        if num_failed > 0:
            for wall, status in download_status.items():
                if status is DownloadStatus.FAILED:
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


class IDFetcher(Fetcher):
    """Fetch wall from given Ids"""

    def __init__(self,
                 wall_ids: list[str],
                 download_file: bool = True,
                 base_dir: Optional[str] = None,
                 max_retries: int = 5,
                 interval: int = 2):
        super().__init__(fetch_wallpaper_details=True,
                         download_file=download_file,
                         base_dir=base_dir,
                         max_retries=max_retries,
                         interval=interval)
        self.wall_ids = wall_ids
        logger.info(f'Loaded {len(wall_ids)} wallpaper ids')

    def _create_empty_wallpaper(self, wall_id):
        return Wallpaper({'id': wall_id})

    def get_wallpapers(self) -> list[Wallpaper]:
        return [self._create_empty_wallpaper(wall_id) for wall_id in self.wall_ids]


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

    # def _get_wallpape1rs(self)


