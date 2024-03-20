
from typing import Optional

import logging

class MyLogger:

    _registers = {}

    def __init__(self, name: Optional[str] = None):
        self.name = name

        if name not in self._registers:
            self._registers[name] = logging.getLogger(name)

        self._logger = self._registers[name]

    @property
    def logger(self):
        return self._logger
    
    def info(self, *args, **kwargs):
        return self.logger.info(*args, **kwargs)

    def debug(self, *args, **kwargs):
        return self.logger.debug(*args, **kwargs)
        
    def warn(self, *args, **kwargs):
        return self.logger.warn(*args, **kwargs)
    
    def warning(self, *args, **kwargs):
        return self.logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        return self.logger.error(*args, **kwargs)

    # --------------------
    def addHandler(self, *args, **kwargs):
        return self.logger.addHandler(*args, **kwargs)

    @property
    def handlers(self):
        return self.logger.handlers

    # --------------------
    def setLevel(self, *args, **kwargs):
        return self.logger.setLevel(*args, **kwargs)
