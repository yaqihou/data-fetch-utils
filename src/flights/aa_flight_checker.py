#!/usr/bin/env python3

import os
import time
import pickle
import datetime as dt
from typing import Optional
from tabulate import SEPARATING_LINE, tabulate

from tqdm import tqdm

from selenium.webdriver.chrome.webdriver import WebDriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


from ..utils import convert_text_to_img, send_pushover_notification
from ..driver import MyDriver
from ..logger import MyLogger
from .defs import Flight, Flights, UNKNOWN_CABIN

logger = MyLogger('data-fetch-utils.flights')
# NOTE - there are hidden accessible class having more details textual information

class AAFlightChecker:

    start_page = 'https://www.aa.com/booking/find-flights'
    MAX_RETRIES = 3
    tmp_image_path = '/tmp/my-aa-checker-tmp.jpg'

    def __init__(self,
                 from_airport, dest_airport, depart_date, return_date,
                 driver: Optional[WebDriver] = None
                 ):

        # TODO - check the format of depart_date & return date

        self.depart_date = (depart_date.strftime('%m/%d/%y')
                            if isinstance(depart_date, dt.date)
                            else depart_date)
        self.return_date = (return_date.strftime('%m/%d/%y')
                            if isinstance(return_date, dt.date)
                            else return_date)

        self.from_airport = from_airport
        self.dest_airport = dest_airport

        logger.info("Checking for the following flight:")
        logger.info(f"    - {self.from_airport} -> {self.dest_airport}")
        logger.info(f"    - {self.depart_date} -> {self.return_date}")

        self.success = False
        if not driver:
            driver = MyDriver().driver
        self.driver = driver

        self.reset()

    def reset(self):
        self.running_time = dt.datetime.now()
        self.flights: Flights = Flights([])

    def click_and_enter(self, *args, text=""):
        assert isinstance(text, str), f"Given input text {text} ({type(text)}) is not str"
        ele = self.driver.find_element(*args)

        # self.driver.execute_script(
        #     "arguments[0].value = arguments[1]",
        #     ele, text)

        ele.click()
        time.sleep(0.1)

        ele.send_keys(Keys.CONTROL + "a")
        time.sleep(0.1)

        ele.send_keys(text)
        time.sleep(0.1)

    def click_and_cancel(self, *args):
        ele = self.driver.find_element(*args)
        ele.click()
        time.sleep(0.1)

        for button in self.driver.find_element(By.CSS_SELECTOR, 'div#ui-datepicker-div')\
                                    .find_elements(By.TAG_NAME, 'button'):
            if button.text.upper() == "CLOSE":
                button.click()
                time.sleep(0.1)
                break

    def clean_cookie_banner(self):
        try:
            banner = self.driver.find_element(By.TAG_NAME, 'adc-cookie-banner')
            shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', banner)
            # NOTE - invalid argument exception if using By.ID / TAG_NAME within shadow root
            button = shadow_root.find_element(By.CSS_SELECTOR, '#toast-dismiss-button')
            button.click()
        except NoSuchElementException:
            logger.debug('No cookie banner detected.')
        else:
            time.sleep(0.5)

    def fill_search_info(self):

        for args, text in [
                ((By.ID, 'segments0.origin'),      self.from_airport),
                ((By.ID, 'segments0.destination'), self.dest_airport),
                ((By.ID, 'segments0.travelDate'),  self.depart_date),
                ((By.ID, 'segments1.travelDate'), self.return_date),
        ]:
            self.click_and_enter(*args, text=text)
            time.sleep(0.5)
            
        self.clean_cookie_banner()

        # For datapicker, we need extra steps to apply the value of field
        # A better way is to find the target field and send the vlaue to it directly via js
        for args in [(By.CSS_SELECTOR, 'div#departDateSection button'),
                    (By.CSS_SELECTOR, 'div#returnDateSection button')]:
            self.click_and_cancel(*args)

    def submit(self):

        search_button = self.driver.find_element(By.ID, 'flightSearchSubmitBtn')
        search_button.click()

        # The maximum waiting time for the results request is 30 sec, with 5 extra loading time
        try:
            WebDriverWait(self.driver, 40).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.results-matrix'))
            )
        except TimeoutException as e:
            # Usually a refresh will work
            logger.debug('Encounter error when submitting, try to refresh')
            self.driver.refresh()

            WebDriverWait(self.driver, 40).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.results-matrix'))
            )
            
    # -----------------------------------------

    def parse_flights(self):
        self.driver.implicitly_wait(0)

        results_matrix = self.driver.find_element(By.CSS_SELECTOR, 'div.results-matrix')

        # Get cabin type
        header = results_matrix.find_element(By.ID, 'header')
        cabin_group = header.find_element(By.CSS_SELECTOR, 'div.groups')

        self.cabins = []
        for cabin in cabin_group.find_elements(By.TAG_NAME, 'button'):
            self.cabins.append(cabin.get_attribute('id').lower().removeprefix('sort-by-'))
        self.flights.update_cabins(self.cabins)

        logger.info('Found the folloing cabins: %s', ' / '.join(self.cabins))

        # Get flight details
        results = results_matrix.find_element(By.CSS_SELECTOR, 'div.results-grid-container')

        appslices = results.find_elements(By.TAG_NAME, 'app-slice-details')
        for appslice in tqdm(appslices, desc='Parsing flight'):
            self.flights.add_flight(self._parse_flight_details(appslice))

    def _parse_flight_details(self, appslice) -> Flight:

        # Parse flight information
        flight_card = appslice.find_element(By.TAG_NAME, 'app-matrix-flight-card')

        depart_time = flight_card.find_element(By.CSS_SELECTOR, 'div.origin > div.time').text.strip()
        arrive_time = flight_card.find_element(By.CSS_SELECTOR, 'div.destination > div.time').text.strip()

        duration = flight_card.find_element(By.CSS_SELECTOR, 'div.duration').text.strip()

        stop_tooltip = flight_card.find_element(By.CSS_SELECTOR, 'div.stops > app-stops-tooltip')
        # There will be a button to show details unless for non-stop flight
        stop = ''
        try:
            _stop_btn = stop_tooltip.find_element(By.TAG_NAME, 'button')
        except NoSuchElementException:
            stop = 'NON-STOP'
        else:
            # TODO - may fail if there are more than 1 stop
            stop = _stop_btn.text.strip()

        # NOTE - there could be multiple number / aircraft
        details = flight_card.find_elements(By.CSS_SELECTOR, 'div.flight-details')
        flight_details = []
        for detail in details:
            flight_number = detail.find_element(By.CSS_SELECTOR, 'span.flight-number').text.strip()
            aircraft = detail.find_element(By.CSS_SELECTOR, 'span.aircraft').text.strip()
            flight_details.append((flight_number, aircraft))

        # Parse price
        products = appslice.find_elements(By.CSS_SELECTOR, 'app-product-groups > div.product-groups > div')

        prices = dict()
        prices_unknown_cabin = []
        for product in products:

            cabin = UNKNOWN_CABIN
            try:
                price = product.find_element(By.CSS_SELECTOR, 'div.price').text.strip()
                price = price.replace(r"$", "").replace(",", "")
                _details = product.find_element(By.CSS_SELECTOR, 'span.hidden-accessible').text.strip()

                # Make sure the price is aligned with the cabin type
                for _cabin in self.cabins:
                    if _cabin in _details.lower():
                        cabin = _cabin
                        break
            except NoSuchElementException:
                price = "N/A"

            if cabin == UNKNOWN_CABIN and price != 'N/A':
                prices_unknown_cabin.append(price)
            else:
                prices[cabin] = price

        return Flight(
            depart_time=depart_time,
            arrive_time=arrive_time,
            duration=duration,
            stop=stop,
            flight_details=flight_details,
            prices=prices,
            prices_cabin_unk=prices_unknown_cabin
        )

    # -----------------------------------------
    def _get_file_basename(self):
        return "-".join([
            self.from_airport,
            self.dest_airport,
            self.depart_date.replace('/', '_'),
            self.return_date.replace('/', '_'),
        ]) + "@" + self.running_time.strftime('%Y%m%d-%H:%M:%S')

    def _get_folder(self, save_folder):
        folder = os.path.join(
            save_folder,
            f'{self.from_airport}-{self.dest_airport}',
            f"{self.depart_date.replace('/', '_')}-{self.return_date.replace('/', '_')}"
        )
        
        os.makedirs(folder, exist_ok=True)
        return folder
    
    def dump_pkl(self, filename=None, save_folder="."):
        folder = self._get_folder(save_folder)
        filename = filename if filename else self._get_file_basename() + '.pkl'

        path = os.path.join(folder, filename)
        with open(path, 'wb') as f:
            pickle.dump(self.flights, f)
            logger.info(f"PKL file saved to %s", path)

    def dump_txt(self, filename=None, save_folder="."):
        folder = self._get_folder(save_folder)
        filename = filename if filename else self._get_file_basename() + '.txt'

        path = os.path.join(folder, filename)
        with open(path, 'w') as f:
            f.write(self.tabulate_flights())
            logger.info(f"TXT file saved to %s", path)

    def dump_tsv(self, filename=None, save_folder="." ):
        folder = self._get_folder(save_folder)
        filename = filename if filename else self._get_file_basename() + '.tsv'

        path = os.path.join(folder, filename)
        with open(path, 'w') as f:
            f.write(self.tabulate_flights(fmt='tsv'))
            logger.info(f"TSV file saved to %s", path)

    def _get_meta_data(self):
        ret = [["From:", self.from_airport, "To:", self.dest_airport,
                 "Depart:", self.depart_date, "Return:", self.return_date],
                ["Collect Time:", self.running_time.strftime('%Y/%m/%d %H:%M:%S')]]
        ret += self.flights.export_stat()
        return ret
        
    def tabulate_flights(self, fmt='simple') -> str:
        metadata = self._get_meta_data() + [SEPARATING_LINE]
        
        data = [
            Flight.header(),
            [""] * (len(Flight.header()) - 1) + self.cabins,
            SEPARATING_LINE
        ]
        for line in self.flights.export_details():
            data.append(line)
            data.append(SEPARATING_LINE)
        data.pop()  # Remove the last separating line
        logger.debug(f'Tabulated entries num: {len(self.flights)}')
        
        return tabulate(metadata + data, tablefmt=fmt)

    def send_notification(self):

        title = "AA Flight Detail Report"
        message = (
            "\n".join([f"Report Time: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "",])
            + "\n".join(" ".join(map(str, line)) for line in self._get_meta_data())
            )
        
        convert_text_to_img(self.tabulate_flights().splitlines(), self.tmp_image_path)
        files = {
            "attachment": (self.tmp_image_path, open(self.tmp_image_path, "rb"), "image/jpeg")
        }       
        send_pushover_notification(message, title=title, files=files)
        
    # -----------------------------------------
    def _run(self):
        self.reset()
        self.driver.get(self.start_page)

        self.fill_search_info()
        time.sleep(1)

        # The date field is input using js, but I haven't found the real value field.
        # Refresh here to make it retrive the information from cookies
        # self.driver.refresh()
        # wait = WebDriverWait(self.driver, 60)
        # wait.until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, 'div.results-matrix'))
        # )
        self.submit()

        self.parse_flights()

    def run(self):

        retries = 0
        while not self.success and retries < self.MAX_RETRIES:
            try:
                self._run()
            except Exception as e:
                logger.debug('Encountered the above exception, retrying', exc_info=e)
                retries += 1
            else:
                self.success = True

# driver = MyDriver().driver
# checker = AAChecker(from_airport, dest_airport, depart_date, return_date, driver=driver)
# driver = checker.driver
# self = checker
# self.driver.get(self.start_page)
    # checker.fill_search_info()

# checker.submit()
