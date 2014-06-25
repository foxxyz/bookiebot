import json
from time import time

from errbot import BotPlugin, botcmd

# Hack to ensure we can import local modules
from sys import path
from os.path import dirname, realpath
path.append(dirname(realpath(__file__)))

import settings
from api import FIFAAPI, HipchatAPI
from game import Game, GameError, Match, Score
from utils import get_sender_username, string_join_and


class BookieBot(BotPlugin):
	"""Football Betting Bot for Err"""
	min_err_version = '1.6.0'
	max_err_version = '2.0.0'
	match_source = FIFAAPI()

	def activate(self):
		"Start game polling on activation"
		super(BookieBot, self).activate()
		self.game = self['game'] if 'game' in self else Game()
		self.start_poller(60, self.start_matches)
		self.start_poller(61, self.end_matches)

	def deactivate(self):
		"Save game on deactivation"
		self['game'] = self.game
		super(BookieBot, self).deactivate()

	@botcmd(admin_only=True)
	def end_match(self, _, args):
		"""
		Close an ongoing match with a final score (Example: `!end match 2-1 England`)
		"""
		try:
			match, final_score, winners = self.game.close_round(args)
		except ValueError:
			return "That score doesn't work for any of the active rounds."
		self.announce("Final score: {}, {}".format(final_score, self.summarize(winners)))
		self.announce(self.scoreboard(None, None))
		return "Closed match {} with {}".format(match, final_score)

	@botcmd(admin_only=True)
	def init(self, msg, args):
		"Restart the entire game"
		self.game = Game()
		yield "Started game."
		yield self.scoreboard(msg, args)

	@botcmd
	def matches(self, _, dummy):
		"Show current matches"
		if not self.game.active_rounds:
			return "No currently active matches!"
		return "Current matches in progress are {}".format(', '.join([str(rnd) for rnd in self.game.active_rounds]))

	@botcmd(split_args_with=' vs. ', admin_only=True)
	def start_match(self, _, args, uuid=None):
		"""
		Start a new match and round (Example: `!start match Germany vs. England`)
		"""
		match = Match(args, uuid)
		self.game.new_round(match)
		self.announce("Now taking bets for {}...".format(match))
		return "Started match {}".format(match)

	@botcmd
	def scores(self, _, dummy):
		"Show currently placed scores for each match"
		for rnd in self.game.active_rounds:
			for score in rnd.scores.values():
				yield '{}: {}'.format(rnd, score)

	@botcmd
	def score(self, msg, args):
		"""
		Allow user to enter a score and play (Example: `!score 1-0 Germany`)

		Can be automatically without !score via callback_message
		"""
		try:
			score = self.game.add(args, get_sender_username(msg))
			return "Thanks {}! I've noted {} for you.".format(get_sender_username(msg), score)
		except GameError as error:
			return str(error)
		except ValueError: # Ignore malformed scores
			pass

	@botcmd
	def scoreboard(self, _, dummy):
		"Display scoreboard with points for each player"
		if not self.game.scores:
			return 'Scoreboard is empty!'
		else:
			return 'Scores: {}'.format(" / ".join(["{}:{}".format(*s) for s in self.game.scores]))

	@botcmd(admin_only=True)
	def scoreboard_set(self, _, args):
		"""
		Manually enter scoreboard data as a JSON object for a starting score list.
		"""
		self.game = Game(json.loads(args))
		return self.scoreboard(None, None)

	def callback_message(self, _, msg):
		"Listen to every message in a room"
		# Adam's easter egg
		if 'adam' in str(msg).lower():
			self.respond(msg, "hey buddy")
		# Bookie bot's "hello world"
		if 'bookiebot?' in str(msg).lower():
			self.respond(msg, "Affirmative, {}. I read you.".format(get_sender_username(msg)))
		# Automatically detect correctly formatted score messages
		if Score.regex.match(str(msg)):
			self.respond(msg, self.score(msg, str(msg)))

	def end_matches(self):
		"Look for matches that have ended and close them if necessary"
		for match in [self.match_source.get_match(rnd.match.uuid) for rnd in self.game.active_rounds if hasattr(rnd.match, 'uuid')]:
			if match['b_Finished']:
				self.end_match(None, '{}-{} {}'.format(match['n_HomeGoals'], match['n_AwayGoals'], match['c_HomeTeam_en']))

	def respond(self, msg, text):
		"Shortcut for send()"
		self.send(msg.getFrom(), text, message_type=msg.getType())

	def start_matches(self):
		"Look for upcoming matches on FIFA and start a new round if necessary"
		for match in self.match_source.get_upcoming_matches():
			# Only consider matches that are within PRE_MATCH_BETTING_TIME seconds of starting
			if (match['d_Date'] / 1000) - time() > settings.PRE_MATCH_BETTING_TIME:
				continue
			try:
				self.start_match(None, [match['c_HomeTeam_en'], match['c_AwayTeam_en']], match['n_MatchID'])
			except GameError:
				pass

	@staticmethod
	def announce(msg):
		"Send message to Hipchat room"
		HipchatAPI().send(msg)

	@staticmethod
	def summarize(winners):
		"Make pretty string summary of winners"
		if not winners:
			return "there are no winners!"
		points = list(winners.values())[0]
		if points == settings.EXACT_GUESS_POINTS:
			score_text = "for guessing the score correctly"
		else:
			score_text = "for being closest"
		return '{} get{} {} point{} {}'.format(string_join_and(winners.keys()), '' if len(winners) > 1 else 's', points, 's' if points > 1 else '', score_text)

