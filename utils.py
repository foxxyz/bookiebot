from errbot.utils import get_sender_username as err_get_sender_username

from api import HipchatAPI


def get_sender_username(msg):
	"""
	Method override to grab real user names via Hipchat's API

	Needed because in private chats, err will get the JID (I.E. 12345_334837),
	but in rooms it will receive the proper username (I.E. Joe Smith). So we
	need to account for both.
	"""
	username = err_get_sender_username(msg)
	if '_' in username:
		try:
			username = HipchatAPI().get_username(username.split('_')[1])
		except KeyError:
			pass
	return username.split(' ')[0]

def string_join_and(items):
	items = list(items)
	if len(items) > 1:
		string = ", ".join(items[:-1])
		return '{} and {}'.format(string, items[-1])
	return items[0]
