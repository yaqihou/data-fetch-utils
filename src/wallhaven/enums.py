
from enum import Enum

class MaskEnum(Enum):

    def __add__(self, other):

        if isinstance(other, self.__class__):
            return self.__class__(self.value | other.value)
        else:
            raise ValueError(f'Cannot add {type(self)} and {type(other)}')

    def __radd__(self, left):
        return self.__add__(left)

    def __str__(self):
        # Use 8 to ensure always have 3 digits
        return bin(8 | self.value)[3:]

class StrEnum(Enum):

    def __str__(self):
        return self.value


class Purity(MaskEnum):

    SFW = 4 # 100
    SKETCHY = 2  # 010
    NSFW = 1  # 001

    SFW_SKETCHY = 6
    SFW_NSFW = 5
    SKETCHY_NSFW = 3

    ALL = 7


class Category(MaskEnum):

    GENERAL = 4  # 100
    ANIME = 2  # 010
    PEOPLE = 1  # 001

    GENERAL_ANIME = 6
    GENERAL_PEOPLE = 5
    ANIME_PEOPLE = 3

    ALL = 7


class Sorting(StrEnum):

    DATE_ADDED = 'date_added'
    RELEVANCE = 'relevance'
    RANDOM = 'random'
    VIEWS = 'views'
    FAVORITES = 'favorites'
    TOPLIST = 'toplist'
        

class SortingOrder(StrEnum):

    DESC = 'desc'
    ASC = 'asc'


class TopRange(StrEnum):

    D1 = '1d'
    D3 = '3d'
    W1 = '1w'
    M1 = '1M'
    M3 = '3M'
    M6 = '6M'
    Y1 = '1Y'


class Color(StrEnum):
    m_660000 = "660000"
    m_990000 = "990000"
    m_cc0000 = "cc0000"
    m_cc3333 = "cc3333"
    m_ea4c88 = "ea4c88"
    m_993399 = "993399"
    m_663399 = "663399"
    m_333399 = "333399"
    m_0066cc = "0066cc"
    m_0099cc = "0099cc"
    m_66cccc = "66cccc"
    m_77cc33 = "77cc33"
    m_669900 = "669900"
    m_336600 = "336600"
    m_666600 = "666600"
    m_999900 = "999900"
    m_cccc33 = "cccc33"
    m_ffff00 = "ffff00"
    m_ffcc33 = "ffcc33"
    m_ff9900 = "ff9900"
    m_ff6600 = "ff6600"
    m_cc6633 = "cc6633"
    m_996633 = "996633"
    m_663300 = "663300"
    m_000000 = "000000"
    m_999999 = "999999"
    m_cccccc = "cccccc"
    m_ffffff = "ffffff"
    m_424153 = "424153"


class DownloadStatus(Enum):

    SUCCEED = 0
    EXISTED = 1
    FAILED = 2
