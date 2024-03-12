
import json
import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver

from webdriver_manager.chrome import ChromeDriverManager
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import HardwareType, OperatingSystem

logger = logging.getLogger('data-fetch-utils.driver')

class MyDriver:

    def __init__(self,
                 random_ua: bool = False,
                 cookies_file: Optional[str] = None,
                 disable_extensions: bool = False,
                 load_extensions: list[str] = [],
                 no_sandbox: bool = True,
                 options: Optional[webdriver.ChromeOptions] = None,
                 ):

        if options is None:
            
            self.options = webdriver.ChromeOptions()

            if random_ua:
                ua = UserAgent(
                    operating_systems=[OperatingSystem.LINUX.value,
                                    OperatingSystem.WINDOWS.value,
                                    OperatingSystem.MACOS.value],
                    hardware_types=[HardwareType.COMPUTER.value]
                )
                self.options.add_argument(f'--user-agent={ua.get_random_user_agent()}')

            if load_extensions and disable_extensions:
                logger.warning('Both --disable-extensions and --load-extension are set,'
                               ' ignore --disable-extensions')
                disable_extensions = False
            
            if disable_extensions:
                self.options.add_argument("--disable-extensions")

            for ext_path in load_extensions:
                self.options.add_argument(f'--load-extension={ext_path}')

            if no_sandbox:
                self.options.add_argument("--no-sandbox")
            
        else:
            self.options = options
            
        self.service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        if cookies_file:
            with open(cookies_file, 'r', newline='') as f:
                cookies = json.load(f)
                for cookie in cookies:
                    if 'sameSite' in cookie and cookie['sameSite'] == 'unspecified':
                        cookie['sameSite'] = "None"
                    self.driver.add_cookie(cookie)

        self.driver.implicitly_wait(2)
    
    def __enter__(self) -> WebDriver:
        return self.driver

    def __exit__(self, type, value, traceback):
        self.on_exit()

    def on_exit(self):
        self.driver.quit()
