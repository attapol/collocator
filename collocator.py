import sqlite3
from operator import itemgetter

class Collocator(object):

	def __init__(self, db_file):
		self.cur = sqlite3.connect(db_file)
		self.cur.row_factory = sqlite3.Row

	def collocate(self, word):
		sql_command = """SELECT WPOS, SUM(DepCount)
			FROM Words Where Word = "%s" 
			GROUP BY WPOS ORDER BY SUM(DepCount) DESC """ % word
		results = self.cur.execute(sql_command).fetchall()
		pos = results[0]['WPOS']
		if pos[0] == 'V':
			self.collocate_verb(word)
		elif pos[0] == 'N':
			self.collocate_noun(word)
		elif pos == 'RB':
			self.collocate_adverb(word)
		elif pos == 'JJ':
			self.collocate_adj(word)

	def collocate_verb(self, word):
		print 'N + %s' % word
		self.collocate_dtype(word, "nsubj")

		print '%s + N' % word
		self.collocate_dtype(word, "dobj")

		print '%s + ADV' % word
		self.collocate_dtype(word, "advmod")

	def collocate_noun(self, word):
		print 'V + %s' % word
		self.collocate_head_dtype(word, "dobj")

		print '%s + V' % word
		self.collocate_head_dtype(word, "nsubj")

		print 'ADJ + %s' % word
		self.collocate_dtype(word, "amod")

	def collocate_adverb(self, word):
		print 'V + %s' % word
		self.collocate_head_dtype(word, "advmod")

		print 'ADJ + %s' % word
		self.collocate_head_pos(word, "JJ")
	
	def collocate_adj(self, word):
		print 'ADV + %s' % word
		self.collocate_pos(word, "RB")

		print '%s + N' % word
		self.collocate_pos(word, "NN")
			
	def collocate_pos(self, word, pos):
		word = word.lower()
		sql_command = """SELECT W2.Word, W2.WPOS, SUM(D.Count)
			FROM DependencyRelations as D, Words as W, Words as W2
			WHERE W.Word = "%s" AND W2.WPOS = "%s" AND 
			W.WID = D.GovernorID AND W2.WID = D.DependentID
			GROUP BY W2.Word, W2.WPOS
			ORDER BY SUM(D.Count) DESC""" % (word, pos)
		results = self.cur.execute(sql_command).fetchall()
		if len(results) == 0: return None
		print ', '.join([results[i][0] for i in range(min(40, len(results)))])

	def collocate_head_pos(self, word, pos):
		word = word.lower()
		sql_command = """SELECT W2.Word, W2.WPOS, SUM(D.Count)
			FROM DependencyRelations as D, Words as W, Words as W2
			WHERE W.Word = "%s" AND W2.WPOS = "%s" AND 
			W2.WID = D.GovernorID AND W.WID = D.DependentID
			GROUP BY W2.Word, W2.WPOS
			ORDER BY SUM(D.Count) DESC""" % (word, pos)
		results = self.cur.execute(sql_command).fetchall()
		if len(results) == 0: return None
		print ', '.join([results[i][0] for i in range(min(40, len(results)))])

	def collocate_dtype(self, word, dtype):
		word = word.lower()
		sql_command = """ SELECT W.Word AS Word, SUM(W.DepCount) AS DCount, T.Count
				FROM Words as W,
					(SELECT W2.Word AS Word, SUM(D.Count) AS Count
					FROM DependencyRelations as D, Words as W, Words as W2
					WHERE W.Word = "%s" AND W2.DepType = "%s" AND 
					W.WID = D.GovernorID AND W2.WID = D.DependentID 
					GROUP BY W2.Word
					ORDER BY SUM(D.Count) DESC) AS T
				WHERE W.Word = T.Word 
				GROUP BY W.Word
				ORDER BY T.Count DESC
				""" % (word, dtype)
		results = self.cur.execute(sql_command).fetchall()
		if len(results) == 0: return None
		#print 'Before scoring'
		print ', '.join([results[i]['Word'] for i in range(min(40, len(results)))]) + '\n'
		word_score_pairs = [(x['Word'], (x['Count'] + 0.0) / x['DCount'], x['Count'], x['DCount'] ) for x in results if x['DCount'] > 0]
		word_score_pairs = sorted(word_score_pairs, key=itemgetter(1), reverse=True)
		#print 'After scoring'
		#print ', '.join([str(word_score_pairs[i]) for i in range(min(40, len(word_score_pairs)))]) + '\n'


	def collocate_head_dtype(self, word, dtype):
		word = word.lower()
		sql_command = """SELECT W2.Word, SUM(D.Count)
			FROM DependencyRelations as D, Words as W, Words as W2
			WHERE W.Word = "%s" AND W.DepType = "%s" AND 
			W.WID = D.DependentID AND W2.WID = D.GovernorID
			GROUP BY W2.Word
			ORDER BY SUM(D.Count) DESC""" % (word, dtype)
		results = self.cur.execute(sql_command).fetchall()
		if len(results) == 0: return None
		print ', '.join([results[i][0] for i in range(min(40, len(results)))]) + '\n'

	def score(self, results):
		""" Score the results

		"""
		scores = []
		for i in range(min(10, len(results))):
			#import pdb; pdb.set_trace()
			sql_command = """SELECT sum(D.Count) 
				FROM DependencyRelations as D, Words as W
				WHERE D.DependentID = W.WID AND W.Word = "%s" """ % results[i]['WID']
			df = self.cur.execute(sql_command).fetchone()[0] + 0.0
			#scores.append((word,float(count / df)))
		scores = sorted(scores, key=itemgetter(1), reverse = True)
		return scores

	def compare_words(self, word1, word2):
		"""Compare and see how synonymous these two words are """
		pass

def demo():
	collocator = Collocator('dependency_db.db')
	print 'Adjectives that go with performance'
	collocator.collocate_pos("performance","JJ")

	print 'Adverbs that go with observe'
	collocator.collocate_pos("observe","RB")

	print 'Adverbs that go with improve'
	collocator.collocate_pos("improve","RB")

	print 'Nouns that go with criticize'
	collocator.collocate_pos("criticize","NN")

	print 'Direct objects of conduct'
	collocator.collocate_dtype("conduct","dobj")

	print 'Adverbs modifiers that go with little'
	collocator.collocate_dtype("little","advmod")

	print 'Adverbs modifiers that go with small'
	collocator.collocate_dtype("small","advmod")

	print 'Noun that governs sweet'
	collocator.collocate_head_dtype("sweet","amod")

	print 'Noun that governs substantial'
	collocator.collocate_head_dtype("substantial","amod")

	print 'Noun that governs substantial'
	collocator.collocate_head_dtype("opalescent","amod")
	collocator.collocate_head_dtype("opalescent","amod")

import sys
if __name__ == '__main__':
	#demo()
	collocator = Collocator('dependency_db.db')
	collocator.collocate_verb('conduct')
	collocator.collocate_noun('margin')
	while True:
		print 'Please enter a word or q to quit'
		word = sys.stdin.readline().strip()
		if word == 'q': 
			break
		collocator.collocate(word)
