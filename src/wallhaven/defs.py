
import logging
import datetime as dt
from typing import Optional

from .enums import Purity, Category

logger = logging.getLogger('data-fetch-utils.wallhaven')

class Tags:

    def __init__(self, tag_json_list):

        self.tags = {}
        for tag_json in tag_json_list:
            self.tags[tag_json['id']] = {k: v for k, v in tag_json.items() if k != 'id'}

    def __contains__(self, key: str | int):

        if isinstance(key, int) or key.isnumeric():  # search in id
            return int(key) in self.tags
        else:
            return any(key.upper() == tag['name'].upper() for tag in self.tags.values())

    def __str__(self):
        # TODO - polish this part later
        return str(self.tags)
        

class Wallpaper:

    def __init__(self, json):

        self.json: dict = {}
        self._tags = None

        self.update(json)

    def __str__(self):
        # TODO - polish this part later
        return str(self.json)

    def __hash__(self):
        return hash(self.id)

    def update(self, new_json: dict):
        self.json.update(new_json)

        if 'tags' in self.json:
            self._tags = Tags(self.json['tags'])

    def _get_and_convert(self, attr, transform_func=lambda x: x):
        ret = self.json.get(attr)
        if ret is None:
            return ret
        else:
            return transform_func(ret)

    @property
    def tags(self) -> Optional[Tags]:
        return self._tags

    @property
    def id(self) -> str:
        return self.json['id']

    @property
    def path(self) -> str:
        return self.json['path']

    @property
    def url(self) -> Optional[str]:
        return self.json.get('url')

    @property
    def resolution(self) -> Optional[tuple[int, int]]:
        return self._get_and_convert(
            'resolution',
            lambda x: tuple(map(int, x.slipt('x'))))

    @property
    def ratio(self) -> Optional[float]:
        return self._get_and_convert('ratio', float)

    @property
    def file_type(self) -> Optional[str]:
        return self.json.get('file_type')
        
    @property
    def file_size(self) -> Optional[int]:
        return self._get_and_convert('file_size', int)

    @property
    def source(self) -> Optional[str]:
        return self.json.get('source')
        
    @property
    def purity(self) -> Optional[Purity]:
        return self._get_and_convert('purity', lambda x: Purity[x.upper()])

    @property
    def category(self) -> Optional[Category]:
        return self._get_and_convert('category', lambda x: Category[x.upper()])

    @staticmethod
    def _parse_time(x):
        try:
            ret = dt.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
        except:
            logging.debug(f'Failed to parse created_at time string {x}')
            ret = None

        return ret
        
    @property
    def created(self) -> Optional[dt.datetime]:
        return self._get_and_convert('created_at', self._parse_time)

    @property
    def created_date(self) -> Optional[dt.date]:
        ret = self.created
        return ret if ret is None else ret.date()
        
