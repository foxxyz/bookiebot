import os
import unittest

from errbot.backends.test import FullStackTest, pushMessage, popMessage

from objects import Game, GameError, Match, Round, Score


class BookieBotTests(FullStackTest):
    def setUp(self):
        me = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
        # Adding /la/bla to path is needed because of the path mangling
        # FullStackTest does on extra_test_file.
        plugin_dir = os.path.join(me, 'la', 'bla')
        super(BookieBotTests, self).setUp(extra_test_file=plugin_dir)

    def test_scoreboard_empty(self):
        pushMessage('!scoreboard')
        self.assertIn('Scoreboard is empty', popMessage())


class TestGame(unittest.TestCase):
	"Tests for game outcomes"

	def setUp(self):
		self.game = Game()

	def test_correct_scoring(self):
		self.assertEqual(self.game.scores, [])
		self.game.new_round(Match(['Honduras', 'Poland']))
		self.game.add('1-1', 'Pete')
		self.game.add('2-1 Poland', 'Joe')
		self.game.close_round('2-1 Poland')
		self.assertEqual(self.game.scores, [('Joe', 2), ('Pete', 0)])

	def test_previous_scores(self):
		self.game = Game({'Marcy': 6, 'Joe': 1, 'Pete': 3})
		self.game.new_round(Match(['Honduras', 'Poland']))
		self.game.add('1-1', 'Pete')
		self.game.add('2-1 Poland', 'Joe')
		self.game.close_round('1-1')
		self.assertEqual(self.game.scores, [('Marcy', 6), ('Pete', 5), ('Joe', 1)])

	def test_no_active_rounds(self):
		self.assertRaises(GameError, self.game.add, '1-1', 'Joe')

	def test_multiple_active_rounds(self):
		self.game.new_round(Match(['Honduras', 'Poland']))
		self.game.add('1-1', 'Pete')
		self.game.new_round(Match(['Argentina', 'Peru']))
		self.game.add('3-3 Poland', 'Joe')
		self.game.add('3-1 Argentina', 'Joe')
		self.game.add('1-0 Peru', 'Pete')
		self.game.add('0-0 Poland', 'Marcy')
		self.game.close_round('2-2 Peru')
		self.assertEqual(self.game.score_dict, {'Joe': 1, 'Marcy': 0, 'Pete': 0})
		self.game.close_round('2-2 Poland')		
		self.assertEqual(self.game.scores, [('Joe', 2), ('Pete', 1), ('Marcy', 0)])

	def test_multiple_active_rounds_ambiguous_score(self):
		self.game.new_round(Match(['Honduras', 'Poland']))
		self.game.new_round(Match(['Argentina', 'Peru']))
		self.assertRaises(GameError, self.game.add, '1-1', 'Pete')
	
	def test_multiple_active_rounds_unspecified_result(self):
		self.game.new_round(Match(['Honduras', 'Poland']))
		self.game.new_round(Match(['Argentina', 'Peru']))
		self.assertRaises(GameError, self.game.close_round, '1-1')	

class TestRound(unittest.TestCase):
	"Tests for round outcomes"

	def setUp(self):
		match = Match(['Nigeria', 'Russia'])
		self.round = Round(match)
		self.round.add('2-0 Russia', 'Pete')
		self.round.add('0-0', 'Joe')
		self.round.add('2-2', 'Amanda')
		self.round.add('2-2', 'Marcy')
		self.round.add('4-1 Nigeria', 'Anthony')

	def test_round_winner_exact(self):
		self.round.close('0-2 Nigeria')
		self.assertEqual(len(self.round.winners), 1)
		self.assertEqual(self.round.winners, {'Pete': 2})

	def test_round_winner_exact_multiple(self):
		self.round.close('2-2')
		self.assertEqual(len(self.round.winners), 2)
		self.assertEqual(self.round.winners, {'Amanda': 2, 'Marcy': 2})

	def test_round_winner_closest(self):
		self.round.close('7-1 Nigeria')
		self.assertEqual(len(self.round.winners), 1)
		self.assertEqual(self.round.winners, {'Anthony': 1})

	def test_round_winner_closest_multiple(self):
		self.round.close('0-1 Nigeria')
		self.assertEqual(len(self.round.winners), 2)
		self.assertEqual(self.round.winners, {'Pete': 1, 'Joe': 1})

	def test_round_winner_closest_triple(self):
		self.round.close('2-1 Russia')
		self.assertEqual(len(self.round.winners), 3)
		self.assertEqual(self.round.winners, {'Pete': 1, 'Amanda': 1, 'Marcy': 1})

class TestScore(unittest.TestCase):
	"Tests for score creation and subtraction"

	def setUp(self):
		self.match = Match(['Nigeria', 'Russia'])
		self.other_match = Match(['Honduras', 'Poland'])

	def test_parsing_normal(self):
		score = Score(self.match, '2-0 Russia')
		self.assertEqual(score['Russia'], 2)
		self.assertEqual(score['Nigeria'], 0)
		self.assertEqual(score.winner, 'Russia')

	def test_parsing_opposite(self):
		score = Score(self.match, '4-5 Nigeria')
		self.assertEqual(score['Russia'], 5)
		self.assertEqual(score['Nigeria'], 4)
		self.assertEqual(score.winner, 'Russia')

	def test_parsing_inexact(self):
		score = Score(self.match, '4-5   nig')
		self.assertEqual(score['Russia'], 5)
		self.assertEqual(score['Nigeria'], 4)
		self.assertEqual(score.winner, 'Russia')

	def test_parsing_tie(self):
		score = Score(self.match, '0-0')
		self.assertEqual(score['Russia'], 0)
		self.assertEqual(score['Nigeria'], 0)
		self.assertEqual(score.winner, None)

	def test_parsing_no_order_given(self):
		self.assertRaises(ValueError, Score, self.match, '4-5')

	def test_parsing_invalid_team(self):
		self.assertRaises(ValueError, Score, self.match, '3-0 Paraguay')

	def test_difference(self):
		score_a = Score(self.match, '4-2 Nigeria')
		score_b = Score(self.match, '2-1 Russia')
		self.assertEqual(score_a - score_b, 3)

	def test_difference_complex(self):
		score_a = Score(self.match, '4-2 Russia')
		score_b = Score(self.match, '6-2 Nigeria')
		self.assertEqual(score_a - score_b, 6)			

	def test_difference_same_scores(self):
		score_a = Score(self.match, '1-1')
		score_b = Score(self.match, '1-1')
		self.assertEqual(score_a - score_b, 0)

	def test_difference_negative_offset(self):
		score_a = Score(self.match, '0-0')
		score_b = Score(self.match, '2-1 Russia')
		self.assertEqual(score_a - score_b, 3)

	def test_difference_fail(self):
		score_a = Score(self.match, '0-0')
		score_b = Score(self.other_match, '0-0')
		self.assertRaises(TypeError, score_a.__sub__, score_b)

if __name__ == '__main__':
	unittest.main()
