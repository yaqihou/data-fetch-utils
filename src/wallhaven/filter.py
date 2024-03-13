
from __future__ import annotations
import datetime as dt
from typing import Iterable, Iterator, Optional

from .defs import Wallpaper 
from .enums import By, Purity, Category
from .cacher import Cache

from ..utils import rectify_date
from ..logger import MyLogger

logger = MyLogger('data-fetch-utils.wallhaven.filter')

class Filter:
    """Apply filter by meta data using saved meta info"""

    def __init__(self, wallpapers: Optional[Iterable[Wallpaper | str] | Iterator[Wallpaper | str]] = None):
        """
        wallpapers: list of Wallpaper instances or wallpaper_id, if None, will use all entries from cache file
        """

        self.cache = Cache()

        if wallpapers is None:
            # Get all cached wallpaper ids
            wallpapers = list(self.cache)

        self._wallpapers: list[Wallpaper] = []
        for wall in wallpapers:
            if isinstance(wall, Wallpaper):
                self._wallpapers.append(wall)
            elif isinstance(wall, str):
                _wall = self.cache.fetch_wallpaper(wall)
                if _wall is None:
                    logger.debug(f'Wallpaper {wall} is not in the cache')
                    # TODO - add auto fetching through api
                else:
                    # TODO - wrap with try-except
                    self._wallpapers.append(_wall)
            else:
                logger.debug(f'Wallpaper {wall} is neither a str or Wallpaper instance')

        self._iter = iter(self._wallpapers)

    def __len__(self):
        return len(self._wallpapers)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iter)

    def __getitem__(self, index):
        return self._wallpapers[index]

    # TODO - add a caching mechanism for queried results
    def by(self, _by: By, *args, **kwargs) -> Filter:

        method_register = {
            By.RATIO: self._by_ratio,
            # By.FILE_SIZE: self._by_filesize,
            By.PURITY: self._by_purity,
            By.CATEGORY: self._by_category,
            # By.CREATED: self._by_created,
            By.CREATED_DATE: self._by_created_date,
        }

        return self.__class__(method_register[_by](*args, **kwargs))

    def _by_ratio(self, ratio_min: Optional[float] = None, ratio_max: Optional[float] = None):
        if ratio_min is None:
            ratio_min = 0.

        if ratio_max is None:
            ratio_max = float(1e9)
        
        if not isinstance(ratio_min, float):
            logger.error(f"Given ratio_min value {ratio_min} should be float")
        elif not isinstance(ratio_min, float):
            logger.error(f"Given ratio value {ratio_max} should be float")
        else:
            return filter(lambda x: ((x.ratio or -1) >= ratio_min and (x.ratio or -1) <= ratio_max),
                          self._wallpapers)

    def _by_purity(self, purity: Purity):
        return filter(lambda x: (x.purity or Purity.NONE) & purity, self._wallpapers)

    def _by_category(self, category: Category):
        return filter(lambda x: (x.category or Category.NONE) & category, self._wallpapers)

    def _by_created_date(self,
                         before: Optional[dt.date | str] = None,
                         after: Optional[dt.date | str] = None):

        if before is None:  before = dt.date(2099, 12, 31)
        if after is None:  after = dt.date(1900, 1, 1)
                
        before = rectify_date(before)
        after = rectify_date(after)

        return filter(
            lambda x:
            ((x.created_date or dt.date(1899, 12, 31)) >= after)
            and ((x.created_date or dt.date(1899, 12, 31)) <= before),
            self._wallpapers)
