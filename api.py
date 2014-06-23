import operator
import requests
from time import time

NEW_MATCH_TIME_OFFSET = 1800 # 30 Minutes
HIPCHAT_AUTH_TOKEN = "0BRCJWCy5aLy0Avshzqo3GMCgEHVtAHR8VV9GDo9"

class FIFAAPI:
	URL = 'http://live.mobileapp.fifa.com/api/wc/matches'
	CACHE_TIME = 300 # 5 Minutes
	_data = None
	_data_time = None

	@property
	def data(self):
		"Facade to cache API data"
		if not self._data or time() - self._data_time > self.CACHE_TIME:
			self._data = requests.get(self.URL).json()['data']
			self._data_time = time()
		return self._data

	def get_match(self, uuid):
		"Get specific match information"
		all_matches = self.data['group'] + self.data['second']
		for match in all_matches:
			if match['n_MatchID'] == uuid:
				return match

	def get_upcoming_matches(self):
		"Get upcoming matches"
		all_matches = self.data['group'] + self.data['second']
		# Include matches that have started less than 30 min ago
		upcoming = [match for match in all_matches if match['d_Date'] > ((time() - NEW_MATCH_TIME_OFFSET) * 1000)]
		return sorted(upcoming, key=operator.itemgetter('c_Date'))


class HipchatAPI:
	ANNOUNCE_URL = "https://api.hipchat.com/v2/room/{name}/notification"
	USER_URL = 'https://api.hipchat.com/v2/user'
	CACHE_TIME = 3600 * 24 # 1 day
	_data = None
	_data_time = None

	def get_username(self, user_id):
		for user in self.get_users():
			if user['id'] == int(user_id):
				return user['mention_name']

	def get_users(self):
		"Get all users in group"
		if not self._data or time() - self._data_time > self.CACHE_TIME:
			self._data = requests.get(self.USER_URL, params={'auth_token': HIPCHAT_AUTH_TOKEN})
			self._data_time = time()
		return self._data.json()['items']

