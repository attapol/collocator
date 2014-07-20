import sys
import sqlite3
import re
from itertools import izip


class DBWriter(object):

	def __init__(self, db_file):
		self.cur = sqlite3.connect(db_file, cached_statements=100000)
		self.word_re = re.compile('[a-z]+')
		self.dependency_re = re.compile("[a-z']+/[a-zA-Z]+/[a-zA-Z]+/\d")
		self.running_index = self.cur.execute('SELECT count(WID) From Words').fetchone()[0]
		print 'Starting from %s' % self.running_index
		self.wid_cache = {}
		self.cache_limit = 6000000
		self.governor_count = [0] * self.cache_limit
		self.dependent_count = [0] * self.cache_limit
		self.pair_cache = []
		self.triplet_cache = []
	

	def lookup_make_id(self, word, pos, dep_type, governing=False, dependent=False):
		if (word,pos,dep_type) in self.wid_cache:
			return self.wid_cache[(word,pos,dep_type)]
		select_command = """
			SELECT WID 
			FROM Words 
			WHERE Word="%s" AND WPOS="%s" AND DepType="%s" """ % (word, pos, dep_type)
		result = self.cur.execute(select_command).fetchone()
		if result is None:
			self.running_index += 1
			insert_command = """
			INSERT INTO Words (WID, Word, WPOS, DepType)
			VALUES (%s, "%s", "%s", "%s") """ % (self.running_index, word, pos, dep_type)
			self.cur.execute(insert_command)
			self.wid_cache[(word,pos,dep_type)] = self.running_index
			return self.running_index
		else:
			self.wid_cache[(word,pos,dep_type)] = result[0]
			return result[0]

	def insert_pair(self, head_id, dep_id, count):
		sql_command = """
			INSERT INTO DependencyRelations (GovernorID, DependentID, Count)
			VALUES ("%s", "%s", "%s") """ % (head_id, dep_id, count)
		self.cur.execute(sql_command)

	def insert_triplet(self, head_id, intermediate_id, dep_id, count):
		sql_command = """
			INSERT INTO DependencyRelations (GovernorID, IntermediateID, DependentID, Count)
			VALUES ("%s", "%s", "%s", "%s") """ % (head_id, intermediate_id, dep_id, count)
		self.cur.execute(sql_command)

	def write_caches_to_db(self):
		sql_command = """
			INSERT INTO DependencyRelations (GovernorID, IntermediateID, DependentID, GovernorPosition, DependentPosition, Count)
			VALUES (?, ?, ?, ?, ?, ?) """
		self.cur.executemany(sql_command, self.triplet_cache)
		self.triplet_cache = []
		sql_command = """
			INSERT INTO DependencyRelations (GovernorID, DependentID, GovernorPosition, DependentPosition, Count)
			VALUES (?, ?, ?, ?, ?) """ % self.pair_cache
		self.cur.executemany(sql_command, self.pair_cache)
		self.pair_cache = []

	def write_counts(self):
		self.cur.executemany('UPDATE Words SET GovernorCount = ? WHERE WID = ?', \
				izip(self.governor_count[1:self.running_index+1], xrange(1,self.running_index+1)))
		self.cur.executemany('UPDATE Words SET DepCount = ? WHERE WID = ?', \
				izip(self.dependent_count[1:self.running_index+1], xrange(1,self.running_index+1)))
		self.cur.commit()

	def import_file(self, data_file):
		for line in open(data_file).readlines():
			word, dependency, count = line.strip().split('\t')
			count = int(count)
			try:
				if not self.word_re.match(word):
					continue
				dependency_tuples = dependency.split(' ')
				head_id, dep_id, intermediate_id = (-1, -1, -1)
				governor_position, dependent_position = (-1, -1)
				complete_dependency = True
				for i, d in enumerate(dependency_tuples):
					if not self.dependency_re.match(d):
						complete_dependency = False
						break
					word, pos, dep_type, head_pos = d.split('/')
					head_pos = int(head_pos)
					if head_pos == 0: # head_word
						governor_position = i
						head_id = self.lookup_make_id(word,pos,dep_type)
						self.governor_count[head_id] += count
					elif len(dependency_tuples) == 2 and head_pos != 0:
						dependent_position = i
						dep_id = self.lookup_make_id(word,pos,dep_type)
						self.dependent_count[dep_id] += count
					elif len(dependency_tuples) == 3 and head_pos != 0:
						if intermediate_id == -1:
							intermediate_id = self.lookup_make_id(word,pos,dep_type)
						elif dep_id == -1:
							dependent_position = i
							dep_id = self.lookup_make_id(word,pos,dep_type)
							self.dependent_count[dep_id] += count

				if complete_dependency:
					if len(dependency_tuples) == 2:
						self.pair_cache.append(
								(head_id,dep_id,governor_position,dependent_position,count))
					elif len(dependency_tuples) == 3:
						self.triplet_cache.append(
								(head_id,intermediate_id,dep_id,governor_position,dependent_position,count))
			except Exception as e:
				print (word, dependency, count)
		self.write_caches_to_db()
		if len(self.wid_cache) > self.cache_limit:
			self.wid_cache = {}
		self.cur.commit()
			
					
import cProfile
if __name__ == '__main__':
	db_file = sys.argv[1]
	writer = DBWriter(db_file)
	files = sys.argv[2:]
	for f in files:
		print f
		cProfile.run("writer.import_file(f)")
	cProfile.run("writer.write_counts()")
