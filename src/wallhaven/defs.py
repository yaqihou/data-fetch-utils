
from typing import Optional

from .enums import Purity, Category

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

    def __init__(self, wallpaper_json):

        self.wallpaper_json: dict = {}
        self.tags = None

        self.update(wallpaper_json)

    def __str__(self):
        # TODO - polish this part later
        return str(self.wallpaper_json)

    def update(self, new_json):
        self.wallpaper_json.update(new_json)

        if 'tags' in self.wallpaper_json:
            self.tags = Tags(self.wallpaper_json['tags'])

    def _get_and_convert(self, attr, transform_func=lambda x: x):
        ret = self.wallpaper_json.get(attr)
        if ret is None:
            return ret
        else:
            return transform_func(ret)

    @property
    def id(self) -> str:
        return self.wallpaper_json['id']

    @property
    def url(self) -> Optional[str]:
        return self.wallpaper_json.get('url')

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
        return self.wallpaper_json.get('file_type')
        
    @property
    def source(self) -> Optional[str]:
        return self.wallpaper_json.get('source')
        
    @property
    def path(self) -> Optional[str]:
        return self.wallpaper_json.get('path')
        
    @property
    def purity(self) -> Optional[Purity]:
        return self._get_and_convert('purity', lambda x: Purity[x.upper()])

    @property
    def category(self) -> Optional[Category]:
        return self._get_and_convert('category', lambda x: Category[x.upper()])

    @property
    def filesize(self) -> Optional[int]:
        return self._get_and_convert('filesize', int)
