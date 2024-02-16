# pylint: disable=protected-access
import os
from datetime import datetime, timedelta
from time import sleep
from unittest import TestCase

from freezegun import freeze_time
from testfixtures import compare
from trello import TrelloClient

from src.trello_manager import TrelloManager, TrelloExecption, ShoppingTask, ReplayDateTask, ScheduledTodos

TEST_BOARD = "UNITTEST"
TEST_KEY = "TRELLO_API_KEY_TEST"
TEST_SECRET = "TRELLO_API_SECRET_TEST"


class TrelloTest(TestCase):
    def first_weekday_of_the_year(self, day) -> str:
        d = datetime(datetime.now().year, 1, 7)
        offset = -d.weekday() + day  # weekday == 0 means Monday
        return (d + timedelta(offset)).strftime("%Y-%m-%d")

    @classmethod
    def setUpClass(cls):
        cls.client = TrelloClient(
            api_key=os.environ["TRELLO_API_KEY_TEST"],
            api_secret=os.environ["TRELLO_API_SECRET_TEST"]
        )

    def setUp(self):
        # this is necessary, because the calls to the api of trello are limited to
        # 100calls/10seconds.
        if "CIRCLECI" in os.environ:
            sleep(4)
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
            self.client.fetch_json(f"boards/{board_hit.id}", http_method="DELETE")


class TestTrelloManager(TrelloTest):
    TrelloManager._board_name = TEST_BOARD
    TrelloManager._key = TEST_KEY
    TrelloManager._secret = TEST_SECRET

    def setUp(self):
        super().setUp()
        self.manager = TrelloManager()

    def test_no_board(self):
        TrelloManager._board_name = "Tada"
        with self.assertRaises(TrelloExecption):
            TrelloManager()

        TrelloManager._board_name = None
        with self.assertRaises(TrelloExecption):
            TrelloManager()

    def test_get_list_by_name(self):
        self.board.add_list("neue_liste")
        list_id = self.board.get_lists(None)[0].id
        fetched_list = self.manager.get_list_by_name("neue_liste")
        compare(list_id, fetched_list.id)
        compare(None, self.manager.get_list_by_name("bla"))


class TestShoppingTask(TrelloTest):
    ShoppingTask._board_name = TEST_BOARD
    ShoppingTask._key = TEST_KEY
    ShoppingTask._secret = TEST_SECRET

    def setUp(self):
        super().setUp()
        self.buy_list = self.board.add_list("Wichtiges Einkaufen")
        self.list_lebensmittel = self.board.add_list("Gerade nicht kaufen (Lebensmittel)")
        self.label_lebensmittel = self.board.add_label("Lebensmittel", "orange")
        self.label_getraenke = self.board.add_label("Getränke", "yellow")
        self.list_drogerie = self.board.add_list("Gerade nicht kaufen (Drogerie)")
        self.label_drogerie = self.board.add_label("Drogerie", "red")
        self.task = ShoppingTask()

    def test_integration(self):
        self.buy_list.add_card("Test_Item_1", labels=[self.label_lebensmittel])
        self.buy_list.add_card("Test_Item_2", labels=[self.label_drogerie])
        self.buy_list.add_card("Test_Item_3", labels=[self.label_getraenke])
        self.buy_list.add_card("Don't show")
        self.buy_list.archive_all_cards()
        self.buy_list.add_card("Show")

        self.task.run()

        drogerie_cards = self.list_drogerie.list_cards()
        compare(1, len(drogerie_cards))
        compare("Test_Item_2", drogerie_cards[0].name)
        lebensmittel_cards = self.list_lebensmittel.list_cards()
        compare(2, len(lebensmittel_cards))
        compare("Test_Item_1", lebensmittel_cards[0].name)
        compare("Test_Item_3", lebensmittel_cards[1].name)
        buy_cards = self.buy_list.list_cards()
        compare(1, len(buy_cards))
        compare("Show", buy_cards[0].name)
        closed_cards = self.board.closed_cards()
        compare(1, len(closed_cards))
        compare("Don't show", closed_cards[0].name)

    def test_sorting(self):
        for category in ((self.list_lebensmittel, self.label_lebensmittel),
                         (self.list_drogerie, self.label_drogerie)):
            self.buy_list.add_card("Test_Item_2", labels=[category[1]])
            self.buy_list.add_card("Test_Item_0", labels=[category[1]])
            self.buy_list.archive_all_cards()

            self.task.run()

            cards = category[0].list_cards()
            compare(2, len(cards))
            compare("Test_Item_0", cards[0].name)
            compare("Test_Item_2", cards[1].name)


class TestReplayDateTask(TrelloTest):
    ReplayDateTask._board_name = TEST_BOARD
    ReplayDateTask._key = TEST_KEY
    ReplayDateTask._secret = TEST_SECRET

    _DATE_FORMAT = "%Y-%m-%d"

    def setUp(self):
        super().setUp()
        self.list_todo = self.board.add_list("ToDo")
        self.list_replay = self.board.add_list("Replay")
        self.list_backlog = self.board.add_list("Backlog")
        self.label_replay = self.board.add_label("replay", "red")
        self.task = ReplayDateTask()
        self.now = datetime.now()

    def test_fetch_replay_from_archive(self):
        self.list_todo.add_card("Test_Get_From_Archive_1 (20 d)", labels=[self.label_replay])
        self.list_todo.add_card("Test_Get_From_Archive_2 (10 d)", labels=[self.label_replay])
        self.list_todo.add_card("Test_Get_From_Archive_3 (wrong timedelta)",
                                labels=[self.label_replay],
                                due=self.now.strftime(self._DATE_FORMAT))
        self.list_todo.add_card("Test_Stay_In_Archive",
                                due=(self.now + timedelta(days=1)).strftime(self._DATE_FORMAT))
        self.list_todo.archive_all_cards()
        self.list_todo.add_card("Test_Stay_On_Board (20 d)", labels=[self.label_replay])

        self.task.run()

        todo_cards = self.list_todo.list_cards()
        compare(2, len(todo_cards))
        compare("Test_Stay_On_Board (20 d)", todo_cards[0].name)
        compare("Test_Get_From_Archive_3 (wrong timedelta)", todo_cards[1].name)
        compare(self.now.date(), todo_cards[1].due_date.date())

        replay_cards = self.list_replay.list_cards()
        compare(2, len(replay_cards))
        compare("Test_Get_From_Archive_2 (10 d)", replay_cards[0].name)
        compare((self.now + timedelta(days=10)).date(), replay_cards[0].due_date.date())
        compare("Test_Get_From_Archive_1 (20 d)", replay_cards[1].name)
        compare((self.now + timedelta(days=20)).date(), replay_cards[1].due_date.date())

        closed_cards = self.board.closed_cards()
        compare(1, len(closed_cards))
        compare("Test_Stay_In_Archive", closed_cards[0].name)

    def test_replay_and_backlog_to_todo(self):
        self.list_replay.add_card("Test_To_Todo_2 (20 d)",
                                  labels=[self.label_replay],
                                  due=self.now.strftime(self._DATE_FORMAT))
        self.list_replay.add_card("Test_To_Todo_1 (20 d)",
                                  labels=[self.label_replay],
                                  due=(self.now + timedelta(days=2)).strftime(self._DATE_FORMAT))
        self.list_replay.add_card("Test_Stay_Replay_1 (20 d)",
                                  labels=[self.label_replay],
                                  due=(self.now + timedelta(days=3)).strftime(self._DATE_FORMAT))
        self.list_backlog.add_card("Test_To_Todo_3",
                                   due=(self.now + timedelta(days=1)).strftime(self._DATE_FORMAT))
        self.list_backlog.add_card("Test_Stay_Backlog_1",
                                   due=(self.now + timedelta(days=10)).strftime(self._DATE_FORMAT))
        self.list_backlog.add_card("Test_Stay_Backlog_2",
                                   due=(self.now + timedelta(days=4)).strftime(self._DATE_FORMAT))
        self.list_todo.add_card("Just_a_card")

        self.task.run()

        replay_cards = self.list_replay.list_cards()
        compare(1, len(replay_cards))
        compare("Test_Stay_Replay_1 (20 d)", replay_cards[0].name)

        backlog_cards = self.list_backlog.list_cards()
        compare(2, len(backlog_cards))
        compare("Test_Stay_Backlog_2", backlog_cards[0].name)
        compare("Test_Stay_Backlog_1", backlog_cards[1].name)

        todo_cards = self.list_todo.list_cards()
        compare(4, len(todo_cards))
        compare("Test_To_Todo_2 (20 d)", todo_cards[0].name)
        compare("Test_To_Todo_3", todo_cards[1].name)
        compare("Just_a_card", todo_cards[2].name)
        compare("Test_To_Todo_1 (20 d)", todo_cards[3].name)


class TestDailyWorkTodos(TrelloTest):
    ScheduledTodos._board_name = TEST_BOARD
    ScheduledTodos._key = TEST_KEY
    ScheduledTodos._secret = TEST_SECRET

    def setUp(self):
        super().setUp()
        self.list_todo = self.board.add_list("ToDo")
        self.orga_label = self.board.add_label("Orga", "pink")
        self.task = ScheduledTodos()

    def test_create_daily_todos(self):
        # tomorrow is Saturday
        with freeze_time(self.first_weekday_of_the_year(4)):
            self.task.create_scheduled_reminder(title="Test",
                                                checklist=["1", "2"],
                                                days_of_week=[5])

            todo_cards = self.list_todo.list_cards()
            compare(1, len(todo_cards))
            compare("Test", todo_cards[0].name)
            compare(2, len(todo_cards[0].checklists[0].items))
            compare(self.orga_label, todo_cards[0].labels[0])

    def test_no_todos_on_the_weekend(self):
        # Sunday
        with freeze_time(self.first_weekday_of_the_year(6)):
            self.task.create_scheduled_reminder(title="Test",
                                                checklist=["1", "2"],
                                                days_of_week=[3])

        todo_cards = self.list_todo.list_cards()
        # only cards on friday
        compare(0, len(todo_cards))

    def test_monthly_reminder(self):
        # last_day of January
        with freeze_time(datetime(datetime.now().year, 1, 31).strftime("%Y-%m-%d")):
            self.task.create_scheduled_reminder(title="Test",
                                                checklist=["1", "2"],
                                                days_of_month=[1])
            todo_cards = self.list_todo.list_cards()
            compare(1, len(todo_cards))
            compare("Test", todo_cards[0].name)
            compare(2, len(todo_cards[0].checklists[0].items))
            compare(self.orga_label, todo_cards[0].labels[0])

    def test_yearly_reminder(self):
        with freeze_time(datetime(datetime.now().year, 1, 31).strftime("%Y-%m-%d")):
            self.task.create_scheduled_reminder(title="Test",
                                                checklist=["1", "2"],
                                                months_of_year=[2],
                                                days_of_month=[1])
            todo_cards = self.list_todo.list_cards()
            compare(1, len(todo_cards))
            compare("Test", todo_cards[0].name)
            compare(2, len(todo_cards[0].checklists[0].items))
            compare(self.orga_label, todo_cards[0].labels[0])

    def test_yearly_reminder_only_correct_month(self):
        with freeze_time(datetime(datetime.now().year, 1, 31).strftime("%Y-%m-%d")):
            self.task.create_scheduled_reminder(title="Test",
                                                checklist=["1", "2"],
                                                months_of_year=[3],
                                                days_of_month=[1])
            todo_cards = self.list_todo.list_cards()
            compare(0, len(todo_cards))

    def test_monthly_reminder_only_on_the_first_of_month(self):
        with freeze_time(datetime(datetime.now().year, 1, 3).strftime("%Y-%m-%d")):
            self.task.create_scheduled_reminder(title="Test",
                                                checklist=["1", "2"],
                                                days_of_month=[1])
            todo_cards = self.list_todo.list_cards()
            compare(0, len(todo_cards))

    def test_two_criteria(self):
        # tomorrow is Saturday
        with freeze_time(self.first_weekday_of_the_year(4)):
            self.task.create_scheduled_reminder(title="Test",
                                                checklist=["1", "2"],
                                                days_of_week=[5],
                                                days_of_month=[13])

            todo_cards = self.list_todo.list_cards()
            # if two days match only one card to create
            compare(1, len(todo_cards))
            compare(self.orga_label, todo_cards[0].labels[0])
