import logging

from draft_util import BasketballDb, BasketballCrawler

if __name__ == "__main__":
	update_drafts = False

	logging.basicConfig()
	logger = logging.getLogger('draft_selection_crawler')
	logger.setLevel(logging.DEBUG)
	logger.info("Checking database...")
	
	db = DraftDb()
	selections = db.get_selections()

	if not selections.keys():
		logger.info("No selections were found in the database")
		update_drafts = True

	crawler = DraftSelectionsCrawler()
	if update_players:
		logger.info("Getting the players list from the web...")
		selections = crawler.get_selections()
		db.add_selections(selections)

	selection_count = 0
	for s in selections:
		logger.info(str(player_count) + "/" + str(len(players)) + " done...")
		player_count += 1
		crawler.save_player(p, players[p], db)