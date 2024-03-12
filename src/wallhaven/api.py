
import re
import os
import time
import requests
import logging
from typing import Optional
from functools import wraps

from .enums import Category, Purity, SortingOrder, TopRange, Sorting, Color
from ..exceptions import TooManyRequestsError, UnauthorizedError, UnknownResponseError, MaxRetryReachedError

logger = logging.getLogger('data-fetch-util.wallhaven.api')

class API:

    # NSFW wallpapers are blocked to guests.
    # Users can access them by providing their API key:
    # https://wallhaven.cc/api/v1/w/<ID>?apikey=<API KEY>
    WALLPAPER_INFO_URL = 'https://wallhaven.cc/api/v1/w/'

    # With no additional parameters the search will display the latest SFW
    # wallpapers. See the parameter list above to access other listings
    # (random/toplist/etc.).
    # 
    # Listings are limited to 24 results per page. Meta information is
    # available with each response for pagination.
    #
    # When searching for an exact tag (id:##), providing the tag exists, the
    # resolved tag name will be provided in the meta data.
    # 
    # Sorting by 'random' will produce a seed that can be passed between pages
    # to ensure there are no repeats when getting a new page.
    SEARCH_API_URL = 'https://wallhaven.cc/api/v1/search'

    # API calls are currently limited to 45 per minute. If you do hit this
    # limit, you will receive a 429 - Too many requests error.
    # 
    # Attempting to access a NSFW wallpaper without an API Key or with an
    # invalid one will result in a 401 - Unauthorized error.
    #
    # Any other attempts to use an invalid API key will result in a 401 -
    # Unauthorized error.
    last_request_time = time.time()


    def __init__(self,
                 apikey: Optional[str] = None,
                 max_retries: int = 5,
                 request_interval: int = 2):

        self.apikey = os.getenv('WALLHAVEN_API_KEY') if apikey is None else apikey
        self.max_retries = max_retries
        self.request_interval = request_interval

    def _request(self, url, method='get', params=dict()) -> requests.Response:

        if self.apikey is not None and 'apikey' not in params:
            params['apikey'] = self.apikey

        while time.time() - self.last_request_time <= self.request_interval:
            time.sleep(.5)
        
        logger.debug(f'Requesting URL: {url}')
        logger.debug(f'Request method: {method}')
        logger.debug(f'Request params: {params}')

        r = requests.request(method, url, params=params)
        self.last_request_time = time.time()

        if r.status_code == 200:
            return r
        elif r.status_code == 429:
            raise TooManyRequestsError
        elif r.status_code == 401:
            raise UnauthorizedError
        else:
            raise UnknownResponseError(r)

    def request(self, url, method='get', params=dict()) -> requests.Response:

        retry = 0
        while retry < self.max_retries:
            try:
                ret = self._request(url, method=method, params=params)
            except TooManyRequestsError as e:
                logger.info("Request returned with code 429, waiting to retry")
                retry += 1
                time.sleep(5)
            else:
                return ret

        raise MaxRetryReachedError

    def get_wallpaper_info(self, wid) -> requests.Response:
        return self.request(self.WALLPAPER_INFO_URL + str(wid))

    def _parse(self, res_json):
        ret = {}
        for data in res_json['data']:
            ret[data['id']] = {k: v for k, v in data.items() if k != 'id'}

    @staticmethod
    def _verify_dimension_format(dim_str):
        if re.match(r'^[0-9]+x[0-9]+$', dim_str) is None:
            raise ValueError(f'Given input {dim_str} is not valid')

    def search(self,
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
               page: Optional[int] = None,
               seed: Optional[str] = None) -> requests.Response:

        if top_range is not None:
            if sorting is None or sorting != Sorting.TOPLIST:
                raise ValueError(f'Argument top_range must be used with sorting = toplist')

        params = {}
        
        # param from Enum
        for name, var in [
                ('q', q),
                ('page', page),
                ('seed', seed),
                ('sorting', sorting),
                ('order', order),
                ('topRange', top_range),
                ('colors', colors),
                ('categories', categories),
                ('purity', purity),
        ]:
            if var is not None:
                params[name] = str(var)

        # param requiring special treatment
        for name, var in [
                ('atleast', atleast),
                ('resolutions', resolutions),
                ('ratios', ratios)]:

            if var is not None:

                if name == 'atleast':
                    self._verify_dimension_format(var)
                    params[name] = var
                else:
                    map(self._verify_dimension_format, var)            
                    params[name] = ','.join(var)

        return self.request(self.SEARCH_API_URL, params=params)

