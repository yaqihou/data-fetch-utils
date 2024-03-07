
import time
from tqdm import tqdm
import requests

from .api import API
from ..exceptions import TooManyRequestsError

class Fetcher:

    api = API()

    def download(self, url, savename, no_progress: bool = True, total_size=None) -> bool:
        
        r = requests.get(url, stream=True)
        total_size = int(r.headers.get('content-length', 0))
        chunk_size = 32 * 1024

        wrote = 0
        with tqdm(total=total_size, unit='B', unit_scale=True, miniters=1, disable=no_progress) as bar:

            with open(savename, 'wb') as f:
                for chunk in r.iter_content(chunk_size):

                    bar.update(len(chunk))
                    wrote += int(len(chunk))
                    f.write(chunk)

        r.close()

        return wrote == total_size

    def _get_wallpapers(self):
        pass

    def _get_savename(self):
        pass

    def run():

        try:
            self.download(url, savename)
        except TooManyRequestsError:
            time.sleep(45)


class DailyFetcher(Fetcher):
    """Fetch the latest """

    pass


class QueryFetcher(Fetcher):

    pass
