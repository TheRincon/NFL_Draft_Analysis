import sqlite3
import logging
from urllib2 import urlopen

from re import findall

class DraftDb:
	def __init__(self):
		self.conn = sqlite3.connect('draft.db')
		self.c = self.conn.cursor()

	def get_selections(self):
		self.c.execute('''SELECT * FROM draft''')
		selections = {}
		for r in self.c.fetchall():
			selections[r[0]] = (r[1], r[3])

		return selections

	def add_selection(self, players):
		for p in players.keys():
			self.c.execute('INSERT OR IGNORE INTO player (name, link, updated) VALUES (?, ?, ?)'
				, (p, players[p][0], 0))
		self.conn.commit()

	def add_page(self, player_name, page):
		##TODO Decide whit to do with encoding
		self.c.execute('INSERT OR REPLACE INTO player_page (name, page) VALUES (?, ?)',
		 (player_name, page))
		self.c.execute("UPDATE player SET updated = 1 WHERE name = ?", (player_name,))
		self.conn.commit()


class DraftCrawler:
	def __init__(self):
		self.players = {}
		self.logger = logging.getLogger('draft_selection_crawler')

	def get_selections(self):
		page_link = "https://www.pro-football-reference.com/teams/"

		for i in range(26):
			letter = chr(97 + i)
			self.logger.debug("Getting the letter " + letter)

			response = urlopen(page_link + letter)
			if response.code == 200:
				links = findall(r"""<strong><a href="([^"]+)">([^<]+)</a></strong>""",
				 response.read())
				for p in links:
					self.players[p[1]] = (p[0], 0)
			else:
				self.logger.warning("Problem downloading page: " + page_link + letter + 
					" " + response.code)

		return self.selections

	def save_player(self, player_name, player_info, db):
		##TODO Decide whit to do with encoding
		main_link = "http://www.basketball-reference.com/"
		if player_info[1] == 1:
			self.logger.debug("This player is already done: " + player_name)
		else:

			self.logger.debug("Getting player: " + player_name)
			response = urlopen(main_link + player_info[0])
			if response.code == 200:
				db.add_page(player_name, response.read().decode("utf-8"))

			else:
				self.logger.warning("Problem downloading page: " + page_link + player_info[0] 
					+ " " + response.code)




