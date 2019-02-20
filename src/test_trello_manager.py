import os
from unittest import TestCase

from testfixtures import compare
from trello import TrelloClient

from src.trello_manager import TrelloManager, TrelloExecption


class TestTrelloManager(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TrelloClient(
            api_key=os.environ["TRELLO_API_KEY"],
            api_secret=os.environ["TRELLO_API_SECRET"]
        )
        cls.board = None
        for board in cls.client.list_boards():
            if "UNITTEST" == board.name:
                cls.board = board

    def setUp(self):
        self.manager = TrelloManager("UNITTEST")


    def tearDown(self):
        for trello_list in self.board.get_lists(None):
            trello_list.close()

    def test_no_board(self):
        with self.assertRaises(TrelloExecption):
            TrelloManager("TADA")

    def test_get_list_by_name(self):
        self.board.add_list("neue_liste")
        list_id = self.board.get_lists(None)[0].id
        fetched_list = self.manager.get_list_by_name("neue_liste")
        compare(list_id, fetched_list.id)
        compare(None, self.manager.get_list_by_name("bla"))

