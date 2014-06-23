import json
from time import time

from errbot import BotPlugin, botcmd
from errbot.utils import get_sender_username as get_jabber_id

# Hack to ensure we can import local modules
from sys import path
from os.path import dirname, realpath
path.append(dirname(realpath(__file__)))

import settings
from api import FIFAAPI, HipchatAPI
from objects import Game, GameError, Match

def get_sender_username(msg):
	"Method override to grab real user names via Hipchat's API"
	jabber_id = get_jabber_id(msg)
	try:
		return HipchatAPI().get_user(jabber_id.split('_')[1])
	except KeyError:
		return jabber_id

def string_join_and(items):
	if len(items) > 1:
		string = ", ".join(items[:-1])
		return '{} and {}'.format(string, items[-1])
	return items[0]

class BookieBot(BotPlugin):
	"""Football Betting Bot for Err"""
	min_err_version = '1.6.0'
	max_err_version = '2.0.0'
	fifa = FIFAAPI()

	@staticmethod
	def summarize(winners):
		"String summary of winners"
		if winners.values()[0] == settings.EXACT_GUESS_POINTS:
			score_text = "for guessing the score correctly"
		else:
			score_text = "for being closest"
		return '{} get{} {}'.format(string_join_and(winners.keys()), 's' if len(winners) > 1 else '', score_text)

	def activate(self):
		"Start game polling on activation"
		super(BookieBot, self).activate()
		self.game = self['game'] if 'game' in self else Game()
		self.start_poller(60, self.start_matches)
		self.start_poller(301, self.end_matches)

	def announce(self, msg):
		"Send message to chat room"
		HipchatAPI().send(msg, settings.HIPCHAT_ROOM_NAME)
		
	def deactivate(self):
		"Save game on deactivation"
		self['game'] = self.game
		super(BookieBot, self).deactivate()

	@botcmd
	def end_match(self, _, args):
		match, final_score, winners = self.game.close_round(args)
		self.announce("Final score: {}, {}".format(final_score, self.summarize(winners)))
		self.announce(self.scoreboard(None, None))
		return "Closed match {} with {}".format(match, final_score)

	def end_matches(self):
		"Look for matches that have ended and close them if necessary"
		for match in [self.FIFA.get_match(rnd.match.uuid) for rnd in self.game.active_rounds if hasattr(rnd.match, 'uuid')]:
			print(match['n_HomeGoals'], match['n_AwayGoals'], match['b_Finished'])
			if match['b_Finished']:
				self.end_match(None, '{}-{} {}'.format(match['n_HomeGoals'], match['n_AwayGoals'], match['c_HomeTeam_en']))

	@botcmd
	def init(self, msg, args):
		"Restart the entire game"
		self.game = Game()
		yield "Started game."
		yield self.scoreboard(msg, args)

	@botcmd
	def matches(self, msg, args):
		"Show current matches"
		return ""

	@botcmd(split_args_with=' vs. ')
	def start_match(self, _, args, uuid=None):
		"Start a new match & round"
		match = Match(args, uuid)
		self.game.new_round(match)
		self.announce("Now taking bets for {}...".format(match))
		return "Started match {}".format(match)

	def start_matches(self):
		"Look for upcoming matches and start a new round if necessary"
		upcoming_matches = self.FIFA.get_upcoming_matches()
		if not upcoming_matches:
			return
		match = upcoming_matches[0]
		if (match['d_Date'] / 1000) - time() < settings.PRE_MATCH_BETTING_TIME:
			try:
				self.start_match(None, [match['c_HomeTeam_en'], match['c_AwayTeam_en']], match['n_MatchID'])
			except GameError:
				pass

	@botcmd
	def scores(self, msg, args):
		"Show currently placed scores"
		return ""

	@botcmd
	def score(self, msg, args):
		"Enter a score"
		try:
			score = self.game.add(args, get_sender_username(msg))
			return "Registered {}".format(score)
		except GameError as error:
			return str(error)

	@botcmd
	def scoreboard(self, _, args):
		if args:
			self.game = Game(json.loads(args))
			return self.scoreboard(None, None)
		elif not self.game.scores:
			return 'Scoreboard is empty!'
		else:
			return 'Scores: {}'.format(" / ".join(["{}:{}".format(*s) for s in self.game.scores]))

	def callback_message(self, conn, message):
		"Listen to every message in a room"
		pass
		# if Score.regex.match(str(message)):
		# 	return self.score(message, str(message))
