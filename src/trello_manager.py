import os
import re
from typing import Optional, Union
from datetime import datetime, timedelta

from pytz import UTC
from trello import Board, List, Card, Label
import trello


class TrelloExecption(Exception):
    pass


class TrelloManager:  # pylint: disable=too-few-public-methods
    _board_name = None  # type: str
    _key = "TRELLO_API_KEY"
    _secret = "TRELLO_API_SECRET"

    def __init__(self):
        self.client: trello.TrelloClient = trello.TrelloClient(
            api_key=os.environ[self._key],
            api_secret=os.environ[self._secret]
        )
        self.board: Board = self._init_board(self._board_name)
        if not self.board:
            raise TrelloExecption(f"Board {self._board_name} doesn't exists.")
        self.labels: list[Label] = self.board.get_labels()

    def _init_board(self, board_name: str) -> Union[Board, None]:
        for board in self.client.list_boards():
            if board_name == board.name:
                return board
        return None

    def get_list_by_name(self, name: str) -> Union[List, None]:
        for trello_list in self.board.get_lists(None):
            if name == trello_list.name:
                return trello_list
        return None


class ShoppingTask(TrelloManager):
    _board_name: str = "Einkaufen"

    label: dict[str, str] = {"Drogerie": "Drogerie",
                             "Lebensmittel": "Lebensmittel",
                             "Getränke": "Lebensmittel"}

    def __init__(self):
        super().__init__()
        self.lists: dict[str, List] = self._get_lists()

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

    def _get_archived_cards(self) -> dict[str, list[Card]]:
        label_keys = self.label.keys()
        cards: dict[str, list[Card]] = {}
        for key in self.label.values():
            cards[key] = []
        for card in self.board.closed_cards():
            if card.labels:
                for label in card.labels:
                    if label.name in label_keys:
                        cards[self.label[label.name]].append(card)
                        break
        return cards

    def _get_lists(self) -> dict[str, List]:
        lists = {}
        for list_name in self.label.values():
            lists[list_name] = self.get_list_by_name(f"Gerade nicht kaufen ({list_name})")
        return lists

    def _move_to_category(self, card_dict: dict[str, list[Card]]):
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
        sorted_cards = sorted(cards_with_due, key=lambda list_card: list_card.due)  # type: ignore
        for position, card in enumerate(sorted_cards):
            card.set_pos(position)

    @staticmethod
    def get_cards_with_due(list_to_sort: List) -> list[Card]:
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


class ScheduledTodos(TrelloManager):
    def __init__(self):
        super().__init__()
        self.orga_label: Label = None
        for label in self.labels:
            if label.name == "Orga":
                self.orga_label = label
            if self.orga_label:
                break
        self.todo_list: List = self.get_list_by_name("ToDo")

    def create_scheduled_reminder(self, title: str,
                                  checklist: list[str],
                                  days_of_month: Optional[list[int]] = None,
                                  days_of_week: Optional[list[int]] = None,  # 0-6
                                  months_of_year: Optional[list[int]] = None) -> None:
        tomorrow: datetime = datetime.today() + timedelta(days=1)
        # check of weekly occurence
        if days_of_week:
            if tomorrow.weekday() in days_of_week:
                self.create_todo(title, checklist)
                return

        if days_of_month:
            if months_of_year:
                # check for yearly occurences
                if tomorrow.month in months_of_year:
                    if tomorrow.day in days_of_month:
                        self.create_todo(title, checklist)
                        return
            else:
                # check for monthly occurence
                if tomorrow.day in days_of_month:
                    self.create_todo(title, checklist)
                    return

    def create_todo(self, title: str, checklist: Optional[list[str]]) -> None:
        print(f"Creating {title} reminder")
        todo_card: Card = self.todo_list.add_card(title)
        todo_card.set_pos(0)
        if checklist:
            todo_card.add_checklist("Checklist", checklist)
        todo_card.add_label(self.orga_label)


class PrivateTodos(ScheduledTodos):
    _board_name = "Tasks"

    def run(self):
        clean_checklist = [
            "Bad basics",
            "saugen",
            "Bett saugen",
            "Sofa saugen",
            "Scheuerleisten",
            "Bett neu beziehen",
            "Dusche",
            "Wischen",
            "kleines Klo spülen",
            "Seifenschale putzen",
            "Spiegel",
            "Popo-Dusche",
            "Badewanne auswischen",
            "Staub wischen",
            "Abseite putzen",
            "Flaschen wegbringen",
            "Rasen mähen",
            "Müllbeutel wegbringen",
            "Lichtschalter + schmale Kanten",
            "Handtuchhalter entstauben",
            "Küche putzen",
            "Schrankflächen abwischen",
            "Herd",
            "Fliesenspiegel",
            "Wasserkocherecke",
            "um die Spüle",
            "kleine Küchenschränkchen",
            "um die Küchenlampen",
        ]
        self.create_scheduled_reminder(title="Putzen",
                                       checklist=clean_checklist,
                                       days_of_week=[1])
        maintenance_checklist = [
            "NAS",
            "DNS",
            "media",
            "versions infrastructure repo",
            "Handy Photos leeren",
            "Trello Manager",
            "WS Bot",
        ]
        self.create_scheduled_reminder(title="Maintenance",
                                       checklist=maintenance_checklist,
                                       days_of_month=[10])
        daily_checklist = [
            "0,5h Garten",
            "Saft machen, Orangen holen",
            "0.5h priv Tech/WS",
            "Französisch lernen",
        ]
        tomorrow: datetime = datetime.today() + timedelta(days=1)
        self.create_scheduled_reminder(title=f"DAILYS {tomorrow.strftime('%a')}",
                                       checklist=daily_checklist,
                                       days_of_week=[0, 1, 2, 3, 4, 5, 6])
        monthly_checklist = [
            "Waschmaschine putzen",
            "Spúlmaschine putzen",
            "Dunstabzugshaube",
            "Mülleimer",
            "Fensterschränkchen",
        ]
        self.create_scheduled_reminder(title="Putzen monatlich",
                                       checklist=monthly_checklist,
                                       days_of_month=[1])
        self.create_scheduled_reminder(title="Über Freibeträge Gedanken",
                                       checklist=["Depot", "DKB"],
                                       days_of_month=[1],
                                       months_of_year=[11])


class WorkTodos(ScheduledTodos):
    _board_name = "Work"

    def run(self):
        daily_checklist = [
            "calendar https://calendar.google.com/calendar/u/0/r",
            "Board https://github.com/orgs/grafana/projects/146",
            "plan day",
            "write down worktime",
            "Mails https://mail.google.com/mail/u/0/#inbox",
            "read PR's https://github.com/pulls/review-requested",
            "Safed Slack Items",
        ]
        tomorrow: datetime = datetime.today() + timedelta(days=1)
        self.create_scheduled_reminder(title=f"DAILYS {tomorrow.strftime('%a')}",
                                       checklist=daily_checklist,
                                       days_of_week=[0, 1, 2, 3, 4])
        self.create_scheduled_reminder(title="DO EXPENSE REPORT",
                                       checklist=["co-working space", "travel stuff", "other expenses"],
                                       days_of_month=[1])


if __name__ == "__main__":  # pragma: no cover
    WorkTodos().run()
