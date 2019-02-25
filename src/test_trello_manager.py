import os
from unittest import TestCase

from testfixtures import compare
from trello import TrelloClient

from src.trello_manager import TrelloManager, TrelloExecption, ShoppingTask


TEST_BOARD = "UNITTEST"


class TrelloTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TrelloClient(
            api_key=os.environ["TRELLO_API_KEY"],
            api_secret=os.environ["TRELLO_API_SECRET"]
        )
        cls.board = cls._refresh_test_board(cls.client)

    @classmethod
    def _refresh_test_board(cls, client):
        cls._remove_test_board(client)
        return client.add_board(TEST_BOARD)

    @staticmethod
    def _remove_test_board(client):
        board = None
        for board in client.list_boards():
            if TEST_BOARD == board.name:
                break
        if board:
            client.fetch_json('boards/{}'.format(board.id), http_method='DELETE')


class TestTrelloManager(TrelloTest):
    def setUp(self):
        self.manager = TrelloManager(TEST_BOARD)

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
    
    
ShoppingTask._board = TEST_BOARD
    
class TestShoppingTask(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = TrelloManager(TEST_BOARD)
        cls.client = cls.manager.client
        cls.board = cls.manager.board
        cls.task = ShoppingTask()

    def setUp(self):
        self.board.add_list("Wichtiges Einkaufen")
        self.buy_list = self.manager.get_list_by_name("Wichtiges Einkaufen")
        self.label_lebensmittel = self.board.add_label("Lebensmittel", "orange")

    def tearDown(self):
        for trello_list in self.board.get_lists(None):
            trello_list.close()
        
    def testFetchFromArchive(self):
        self.buy_list.add_card("Test_Item", labels=[self.label_lebensmittel])
        self.buy_list.add_card("Don't show")
        self.buy_list.archive_all_cards()

        compare(1, len(self.task._get_archived_cards()))



