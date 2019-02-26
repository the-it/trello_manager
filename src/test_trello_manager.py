import os
from unittest import TestCase

from testfixtures import compare
from trello import TrelloClient

from src.trello_manager import TrelloManager, TrelloExecption, ShoppingTask


TEST_BOARD = "UNITTEST"
TEST_KEY = "TRELLO_API_KEY_TEST"
TEST_SECRET = "TRELLO_API_SECRET_TEST"


class TrelloTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TrelloClient(
            api_key=os.environ["TRELLO_API_KEY_TEST"],
            api_secret=os.environ["TRELLO_API_SECRET_TEST"]
        )

    def setUp(self):
        self.board = self._refresh_test_board()

    def tearDown(self):
        self._remove_test_board()

    def _refresh_test_board(self):
        self._remove_test_board()
        return self.client.add_board(TEST_BOARD)

    def _remove_test_board(self):
        board_hit = None
        for board in self.client.list_boards():
            if TEST_BOARD == board.name:
                board_hit = board
                break
        if board_hit and board_hit.name == TEST_BOARD:
            self.client.fetch_json('boards/{}'.format(board_hit.id), http_method='DELETE')


class TestTrelloManager(TrelloTest):
    TrelloManager._board = TEST_BOARD
    TrelloManager._key = TEST_KEY
    TrelloManager._secret = TEST_SECRET

    def setUp(self):
        super().setUp()
        self.manager = TrelloManager()

    def test_no_board(self):
        TrelloManager._board = "Tada"
        with self.assertRaises(TrelloExecption):
            TrelloManager()

        TrelloManager._board = None
        with self.assertRaises(TrelloExecption):
            TrelloManager()

    def test_get_list_by_name(self):
        self.board.add_list("neue_liste")
        list_id = self.board.get_lists(None)[0].id
        fetched_list = self.manager.get_list_by_name("neue_liste")
        compare(list_id, fetched_list.id)
        compare(None, self.manager.get_list_by_name("bla"))


class TestShoppingTask(TrelloTest):
    ShoppingTask._board = TEST_BOARD
    ShoppingTask._key = TEST_KEY
    ShoppingTask._secret = TEST_SECRET

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.buy_list = self.board.add_list("Wichtiges Einkaufen")
        self.list_lebensmittel = self.board.add_list("Gerade nicht kaufen (Lebensmittel)")
        self.label_lebensmittel = self.board.add_label("Lebensmittel", "orange")
        self.label_getraenke = self.board.add_label("Getränke", "yellow")
        self.list_drogerie = self.board.add_list("Gerade nicht kaufen (Drogerie)")
        self.label_drogerie = self.board.add_label("Drogerie", "red")
        self.list_sonstiges = self.board.add_list("Gerade nicht kaufen (Sonstiges)")
        self.label_sonstiges = self.board.add_label("Sonstiges", "green")
        self.task = ShoppingTask()
        
    def test_integration(self):
        self.buy_list.add_card("Test_Item_1", labels=[self.label_lebensmittel])
        self.buy_list.add_card("Test_Item_2", labels=[self.label_drogerie])
        self.buy_list.add_card("Test_Item_3", labels=[self.label_getraenke])
        self.buy_list.add_card("Test_Item_4", labels=[self.label_sonstiges])
        self.buy_list.add_card("Don't show")
        self.buy_list.archive_all_cards()
        self.buy_list.add_card("Show")

        self.task.run()

        compare(1, len(self.list_drogerie.list_cards()))
        compare("Test_Item_2", self.list_drogerie.list_cards()[0].name)
        compare(1, len(self.list_sonstiges.list_cards()))
        compare("Test_Item_4", self.list_sonstiges.list_cards()[0].name)
        compare(2, len(self.list_lebensmittel.list_cards()))
        compare("Test_Item_1", self.list_lebensmittel.list_cards()[0].name)
        compare("Test_Item_3", self.list_lebensmittel.list_cards()[1].name)
        compare(1, len(self.buy_list.list_cards()))
        compare("Show", self.buy_list.list_cards()[0].name)
        compare(1, len(self.board.closed_cards()))
        compare("Don't show", self.board.closed_cards()[0].name)

    def test_sorting(self):
        for category in {(self.list_lebensmittel, self.label_lebensmittel),
                         (self.list_drogerie, self.label_drogerie),
                         (self.list_sonstiges, self.label_sonstiges)}:
            self.buy_list.add_card("Test_Item_4", labels=[category[1]])
            self.buy_list.add_card("Test_Item_2", labels=[category[1]])
            self.buy_list.add_card("Test_Item_0", labels=[category[1]])
            self.buy_list.archive_all_cards()

            self.task.run()

            cards = category[0].list_cards()
            compare(3, len(cards))
            compare("Test_Item_0", cards[0].name)
            compare("Test_Item_2", cards[1].name)
            compare("Test_Item_4", cards[2].name)
