import os
import pprint
import typing

from trello import TrelloClient, Board, List, Card


class TrelloExecption(Exception):
    pass


class TrelloManager:
    _board = None # type: str
    _key = "TRELLO_API_KEY"
    _secret = "TRELLO_API_SECRET"

    def __init__(self):
        self.client = TrelloClient(
            api_key=os.environ[self._key],
            api_secret=os.environ[self._secret]
        )
        self.board = self._init_board(self._board)
        if not self.board:
            raise TrelloExecption("Board {} doesn't exists.".format(self._board))
        self.printer = pprint.PrettyPrinter(indent=2)

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
    _board = "Einkaufen"

    label = {"Drogerie": "Drogerie",
             "Lebensmittel": "Lebensmittel",
             "Getränke": "Lebensmittel",
             "Sonstiges": "Sonstiges"}

    def __init__(self):
        super().__init__()
        self.lists = self._get_lists()

    def run(self):
        cards = self._get_archived_cards()
        self.printer.pprint(cards)
        self._move_to_category(cards)
        for list_str in self.lists:
            print(f"Sorting list {list_str}")
            card_list = self.get_list_by_name(f"Gerade nicht kaufen ({list_str})")
            self._sort_list(card_list)

    def _sort_list(self, card_list: List):
        cards = card_list.list_cards()
        self.printer.pprint(cards)
        cards = sorted(cards, key=lambda list_card: list_card.name.lower())
        for idx, card in enumerate(cards):
            card.set_pos(idx + 1)

    def _get_archived_cards(self):
        cards = {}
        for key in self.label.values():
            cards[key] = []
        for card in self.board.closed_cards():
            if card.labels:
                for label in card.labels:
                    if label.name in self.label.keys():
                        cards[self.label[label.name]].append(card)
                        break
        return cards

    def _get_lists(self):
        lists = {}
        for list_name in self.label.values():
            lists[list_name] = self.get_list_by_name(f"Gerade nicht kaufen ({list_name})")
        return lists

    def _move_to_category(self, card_dict: typing.Dict[str, typing.List[Card]]):
        for key in card_dict:
            for card in card_dict[key]:
                card.change_list(self.lists[key].id)
                card.set_closed(False)
                pass


if __name__ == "__main__":  # pragma: no cover
    ShoppingTask().run()
