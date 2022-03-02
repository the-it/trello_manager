import os
import re
import typing
from datetime import datetime, timedelta

from pytz import UTC
from trello import TrelloClient, Board, List, Card, Label


class TrelloExecption(Exception):
    pass


class TrelloManager:  # pylint: disable=too-few-public-methods
    _board_name = None  # type: str
    _key = "TRELLO_API_KEY"
    _secret = "TRELLO_API_SECRET"

    def __init__(self):
        self.client: TrelloClient = TrelloClient(
            api_key=os.environ[self._key],
            api_secret=os.environ[self._secret]
        )
        self.board: Board = self._init_board(self._board_name)
        if not self.board:
            raise TrelloExecption(f"Board {self._board_name} doesn't exists.")
        self.labels: typing.List[Label] = self.board.get_labels()

    def _init_board(self, board_name: str) -> typing.Union[Board, None]:
        for board in self.client.list_boards():
            if board_name == board.name:
                return board
        return None

    def get_list_by_name(self, name: str) -> typing.Union[List, None]:
        for trello_list in self.board.get_lists(None):
            if name == trello_list.name:
                return trello_list
        return None


class ShoppingTask(TrelloManager):
    _board_name: str = "Einkaufen"

    label: typing.Dict[str, str] = {"Drogerie": "Drogerie",
                                    "Lebensmittel": "Lebensmittel",
                                    "Getränke": "Lebensmittel",
                                    "Sonstiges": "Sonstiges"}

    def __init__(self):
        super().__init__()
        self.lists: typing.Dict[str, List] = self._get_lists()

    def run(self):
        cards = self._get_archived_cards()
        self._move_to_category(cards)
        for list_str in self.lists:
            print(f"Sorting list {list_str}")
            card_list = self.get_list_by_name(f"Gerade nicht kaufen ({list_str})")
            self._sort_list(card_list)

    @staticmethod
    def _sort_list(card_list: List):
        cards = card_list.list_cards()
        cards = sorted(cards, key=lambda list_card: list_card.name.lower())  # type: ignore
        for idx, card in enumerate(cards):
            card.set_pos(idx + 1)

    def _get_archived_cards(self) -> typing.Dict[str, typing.List[Card]]:
        label_keys = self.label.keys()
        cards: typing.Dict[str, typing.List[Card]] = {}
        for key in self.label.values():
            cards[key] = []
        for card in self.board.closed_cards():
            if card.labels:
                for label in card.labels:
                    if label.name in label_keys:
                        cards[self.label[label.name]].append(card)
                        break
        return cards

    def _get_lists(self) -> typing.Dict[str, List]:
        lists = {}
        for list_name in self.label.values():
            lists[list_name] = self.get_list_by_name(f"Gerade nicht kaufen ({list_name})")
        return lists

    def _move_to_category(self, card_dict: typing.Dict[str, typing.List[Card]]):
        for key in card_dict:
            for card in card_dict[key]:
                card.change_list(self.lists[key].id)
                card.set_closed(False)


class ReplayDateTask(TrelloManager):
    _board_name = "Tasks"
    _DAYS_FOR_TODO = 2

    def __init__(self):
        super().__init__()
        self.todo_list: List = self.get_list_by_name("ToDo")
        self.replay_list: List = self.get_list_by_name("Replay")
        self.dailys_list: List = self.get_list_by_name("Dailys")
        self.backlog_list: List = self.get_list_by_name("Backlog")
        self.replay_label: Label = None
        for label in self.labels:
            if label.name == "replay":
                self.replay_label = label
                break
        self.today: datetime = datetime.now().replace(tzinfo=UTC)

    def run(self):
        self._extract_from_archive()
        self._put_to_todo(self.replay_list)
        self._put_to_todo(self.backlog_list)
        self._sort_replay(self.replay_list)
        # self._sort_replay(self.todo_list)
        self._sort_replay(self.backlog_list)

    def _extract_from_archive(self):
        print("Processing closed Cards")
        for card in self.todo_list.list_cards(card_filter="closed"):
            if card.labels:
                if self.replay_label in card.labels:
                    print(f"openning Card {card}")
                    card.change_list(self.replay_list.id)
                    card.set_closed(False)
                    replay_hit = re.search(r".*\((\d{1,3}) d\)", card.name)
                    try:
                        replay_time = int(replay_hit.group(1))
                    except AttributeError:
                        print("ERROR: No valid duration in card name")
                        continue
                    card.set_due(self.today + timedelta(days=replay_time))

    @staticmethod
    def _sort_replay(list_to_sort: List):
        print(f"Sorting Cards on board {list_to_sort}")
        cards_with_due = ReplayDateTask.get_cards_with_due(list_to_sort)
        sorted_cards = sorted(cards_with_due, key=lambda list_card: list_card.due, reverse=True)  # type: ignore
        for card in sorted_cards:
            card.set_pos(0)

    @staticmethod
    def get_cards_with_due(list_to_sort: List) -> typing.List[Card]:
        cards_with_due = []
        for card in list_to_sort.list_cards():
            if card.due_date:
                cards_with_due.append(card)
        return cards_with_due

    def _put_to_todo(self, list_to_move: List):
        print(f"Moving Cards on board {list_to_move} to todo list")
        cards_with_due = ReplayDateTask.get_cards_with_due(list_to_move)
        for card in cards_with_due:
            if card.due_date.replace(tzinfo=UTC) < \
                    self.today.replace(tzinfo=UTC) + timedelta(days=self._DAYS_FOR_TODO):
                card.change_list(self.todo_list.id)


class DailyWorkTodos(TrelloManager):
    _board_name = "Tasks"

    def __init__(self):
        super().__init__()
        self.orga_label: Label = None
        for label in self.labels:
            if label.name == "Orga":
                self.orga_label = label
            if self.orga_label:
                break
        self.work_list: List = self.get_list_by_name("ToDo")

    def run(self):
        self.create_daily_todo()
        self.create_monthly_expense_reminder()

    def create_monthly_expense_reminder(self) -> None:
        tomorrow: datetime = datetime.today() + timedelta(days=1)
        if tomorrow.day == 1:
            print("Creating expense reminder")
            expense_reminder: Card = self.work_list.add_card("DO EXPENSE REPORT")
            expense_reminder.set_pos(0)
            checklist = [
                "co-working space",
                "travel stuff",
                "other expenses"
            ]
            expense_reminder.add_checklist("TODO", checklist)
            expense_reminder.add_label(self.orga_label)

    def create_daily_todo(self) -> None:
        tomorrow: datetime = datetime.today() + timedelta(days=1)
        # skip the creation of this task on the weekends
        if tomorrow.weekday() in (5, 6):
            print("It's a weekend, no need for a todo card")
            return
        print(f"Creating todo card for: DAILYS {tomorrow.strftime('%a')}")
        new_todos: Card = self.work_list.add_card(f"DAILYS {tomorrow.strftime('%a')}")
        new_todos.set_pos(0)
        checklist = [
            "calendar https://calendar.google.com/calendar/u/0/r",
            "plan day",
            "2 h tech writing",
            "1 h tech training",
            "3 h programming",
            "1 h orga",
            "1.5-hour grafana reading",
            "15-five update https://grafana.15five.com/profile/highlights/",
            "Mails https://mail.google.com/mail/u/0/#inbox",
            "Slack https://raintank-corp.slack.com/",
            "Github board https://github.com/orgs/grafana/projects/15",
            "read PR's https://github.com/pulls/review-requested"
        ]
        new_todos.add_checklist("TODO", checklist)
        new_todos.add_label(self.orga_label)


if __name__ == "__main__":  # pragma: no cover
    DailyWorkTodos().run()
