import operator
import requests
from time import time
from datetime import datetime

from lib.settings import API_KEY, NEW_MATCH_TIME_OFFSET


class FootballDataAPI:
    """
    Quick and dirty implementation of the FIFA data stream
    """
    URL = 'https://api.football-data.org/v4/competitions/WC/matches'
    CACHE_TIME = 300  # 5 Minutes
    _data = None
    _data_time = None

    @property
    def data(self):
        "Facade to cache API data"
        if not self._data or time() - self._data_time > self.CACHE_TIME:
            headers = {'X-Auth-Token': API_KEY}
            self._data = requests.get(self.URL, headers=headers).json()
            self._data_time = time()
        return self._data

    def get_match(self, id):
        "Get specific match information"
        all_matches = self.data['matches']
        for match in all_matches:
            if match['id'] == id:
                return match

    def get_upcoming_matches(self):
        "Get upcoming matches"
        all_matches = self.data['matches']
        # Include matches that have started less than 30 min ago
        upcoming = [match for match in all_matches if datetime.fromisoformat(match['utcDate']).timestamp() > (time() - NEW_MATCH_TIME_OFFSET)]
        return sorted(upcoming, key=operator.itemgetter('utcDate'))
