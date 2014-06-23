import operator
import re

EXACT_GUESS_POINTS = 2
CLOSEST_GUESS_POINTS = 1

class GameError(Exception):
	pass

class Game:
	"""
	A game consists of a number of rounds,
	and a global scoreboard.
	"""

	def __init__(self, scores=None):
		self.score_dict = scores if scores else {}
		self.active_rounds = set()

	def add(self, score, author):
		"Add a bet to this game"

		# Only add a bet if there are active rounds
		if not self.active_rounds:
			raise GameError('No active rounds to add a bet to!')

		self.attempt('add', score, author)

		# Add any new players to the scoreboard
		if author not in self.score_dict:
			self.score_dict[author] = 0

		return score

	def attempt(self, action, *args):
		"Attempt an action on all currently active rounds"

		# Make sure tie scores are specified when there are multiple rounds
		if len(self.active_rounds) > 1 and re.match(r'^\s*\d\s*-\s*\d\s*$', args[0]):
			raise GameError('There are multiple active rounds - please specify a team with your score.')

		for rnd in self.active_rounds:
			try:
				getattr(rnd, action)(*args)
			except ValueError:
				pass
			else:
				return rnd
		raise ValueError("Your score is not valid for any of the active rounds.")

	def close_round(self, final_score):
		"Close round with a final score"

		# Only close round if there are active rounds
		if not self.active_rounds:
			raise GameError('No active rounds to close!')

		rnd = self.attempt('close', final_score)
		self.active_rounds.remove(rnd)

		# Add points to scoreboard
		for winner, points in rnd.winners.items():
			self.score_dict[winner] = self.score_dict.get(winner, 0) + points

		return rnd.match, final_score, rnd.winners

	def new_round(self, match):
		"Start a new round in this game"
		rnd = Round(match)
		if rnd in self.active_rounds:
			raise GameError('Match is already active!')
		self.active_rounds.add(Round(match))

	@property
	def scores(self):
		return sorted(self.score_dict.items(), key=operator.itemgetter(1), reverse=True)

class Round:
	"""
	A round consists of a match being bet on
	and several scores entered by betters.
	"""

	def __init__(self, match):
		self.open = True
		self.match = match
		self.scores = {}
		self.winners = None

	def __hash__(self):
		return hash(tuple(set(self.match.teams)))

	def __eq__(self, other):
		"Equality test"
		return set(self.match.teams) == set(other.match.teams)

	def add(self, score, author):
		"Add a bet to this round"
		if not self.open:
			raise GameError("This round is closed!")
		self.scores[author] = Score(self.match, score, author)

	def close(self, final_score):
		"Close round and determine winner"
		self.match.score = final_score = Score(self.match, final_score)
		# Determine differences between bets and final score
		deltas = sorted([(score.author, final_score - score) for score in self.scores.values()], key=operator.itemgetter(1))
		# Calculate scores -- 2 if exact, otherwise 1 for being closest
		self.winners = {d[0]: EXACT_GUESS_POINTS if d[1] == 0 else CLOSEST_GUESS_POINTS for d in deltas if d[1] == deltas[0][1]}
		self.open = False

class Match:
	"""
	A match is a sports game between two teams.
	"""

	def __init__(self, teams, uuid=None):
		if len(teams) != 2:
			raise Exception("A match must have two teams!")
		self.teams = teams
		self.score = None
		self.uuid = uuid

	def __str__(self):
		return ' vs. '.join(self.teams)

	def get_team(self, name):
		"Loose match string to teams"
		for team in self.teams:
			if name.lower() in team.lower():
				return team

class Score:
	"""
	Outcome of a match.
	"""
	regex = re.compile(r'\s*(\d)\s*-\s*(\d)\s*(?!:for)?\s*(.+)?')

	def __init__(self, match, score, author=None):
		self.match = match
		self.author = author

		# Parse score string
		score_elements = self.regex.match(score)
		if not score_elements:
			raise ValueError("That doesn't seem to be a valid score!")
		score_a, score_b, team_a = score_elements.groups()
		scores = [int(score_a), int(score_b)]

		# Check team name, if given
		if team_a and not match.get_team(team_a):
			raise ValueError("{} is not playing in this match!".format(team_a))

		if score_a != score_b:
			# Require team name if score is not a tie
			if not team_a:
				raise ValueError("If score is not a tie, specify a team for ordering!")
			# Reverse scores depending on the order of the teams in the match
			if match.teams[0] != match.get_team(team_a):
				scores.reverse()

		# Save score as a dict and cache predicted winning team
		self.score = dict(zip(match.teams, scores))
		self.winner = None if score_a == score_b else sorted(self.score.items(), key=operator.itemgetter(1))[1][0]

	def __getitem__(self, key):
		return self.score[key]

	def __repr__(self):
		return '<Score {}>'.format(str(self))

	def __str__(self):
		score = '{}-{}'.format(*sorted(self.score.values(), reverse=True))
		if self.winner:
			score += ' ' + self.winner
		if self.author:
			score += ' by {}'.format(self.author)
		return score

	def __sub__(self, other):
		"Subtract scores"
		if other.match != self.match:
			raise TypeError("Can't subtract scores from different matches!")
		return sum([abs(other[team] - self[team]) for team in self.match.teams])

