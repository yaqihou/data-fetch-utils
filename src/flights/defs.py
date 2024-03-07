
import re
from dataclasses import dataclass, field

from typing import Optional

UNKNOWN_CABIN = "UNK_CABIN"

@dataclass
class Flight:

    depart_time: str
    arrive_time: str

    duration: str
    stop: str
    flight_details: list[tuple[str, str]]

    prices: dict[str, str]
    prices_cabin_unk: list[str]

    stop_num: int = -1


    # TODO - add post parsing for stop_int
    def __post_init__(self):
        if self.stop == 'NON-STOP':
            self.stop_num = 0
        else:
            m = re.search(r"([0-9]+) ?stop", self.stop)
            if m:
                try:
                    self.stop_num = int(m.group(1))
                except:
                    print(f'Failed to parsing {self.stop} to integer')

            self.stop = "\n".join(line.strip(',') for line in self.stop.splitlines())

    @classmethod
    def header(cls) -> list[str]:
        # return [f.name for f in dataclasses.fields(self)]
        return ['Depart', "Arrive", "Duration", "Stop", "Stop Details", "Flight#", "Aircraft", "Price"]

    def export(self, cabins: Optional[list[str]] = None):
        if cabins:
            prices = [self.prices.get(cabin, 'N/A') for cabin in cabins]
        else:
            prices = list(self.prices.values())
        
        return [self.depart_time,
                self.arrive_time,
                self.duration,
                self.stop_num,
                self.stop,
                # The tuple is (flight number, aircraft)
                '\n'.join(x[0] for x in self.flight_details),
                '\n'.join(x[1] for x in self.flight_details),
                *prices,
                *self.prices_cabin_unk
                ]

class Flights:

    def __init__(self, flight_lst: list[Flight] = []):
        self.flights = flight_lst[:]
        self.cabins = []

    def __len__(self):
        return len(self.flights)
    
    def update_cabins(self, cabins):
        self.cabins = cabins[:]

    @property
    def exist_unk_cabin(self):
        return any(len(flight.prices_cabin_unk) > 0 for flight in self.flights)

    def add_flight(self, flight: Flight):
        self.flights.append(flight)

    def get_min_price(self, stop: Optional[int] = None):
        ret = {cabin: 1e9 for cabin in self.cabins}
        if self.exist_unk_cabin:
            ret[UNKNOWN_CABIN] = 1e9

        for flight in self.flights:
            if stop is not None and flight.stop_num != stop:
                continue
            
            for cabin, price in flight.prices.items():
                try:
                    p = int(price)
                    ret[cabin] = min(ret[cabin], p)
                except:
                    # print("Could not convert price into int, skip")
                    pass

            for prices in flight.prices_cabin_unk:
                for price in prices:
                    try:
                        p = int(price)
                        ret[UNKNOWN_CABIN] = min(ret[UNKNOWN_CABIN], p)
                    except:
                        pass

        for k, v in ret.items():
            if v == 1e9:  ret[k] = 'N/A'

        return ret

    def export_stat(self):
        min_prices_nonstop = self.get_min_price(stop=0)
        min_prices_all = self.get_min_price()

        ret = [["Num of Flights:", len(self)]]
        # TODO - add more based on depart / arrive time

        for _type, data in [
                ("Nonstop", min_prices_nonstop),
                ("All", min_prices_all)]:
            tmp = []
            for cabin, min_price in data.items():
                tmp.append(f"Min Price ({_type}, {cabin})")
                tmp.append(min_price)
            ret.append(tmp)
        return ret

    def export_details(self):
        ret = []
        
        ret.append(self.flights[0].export(cabins=self.cabins))
        for flight in self.flights[1:]:
            ret.append(flight.export(cabins=self.cabins))

        return ret

