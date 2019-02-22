import os
import typing

from trello import TrelloClient, Board, List, Card


class TrelloExecption(Exception):
    pass


class TrelloManager:
    def __init__(self, board: str):
        self.client = TrelloClient(
            api_key=os.environ["TRELLO_API_KEY"],
            api_secret=os.environ["TRELLO_API_SECRET"]
        )
        self.board = self._init_board(board)
        if not self.board:
            raise TrelloExecption("Board {} doesn't exists.".format(board))

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

class ShoppingTask:
    _board = "Einkaufen"

    label = {"Drogerie": "Drogerie",
             "Lebensmittel": "Lebensmittel",
             "Getränke": "Lebensmittel",
             "Sonstiges": "Sonstiges"}

    def __init__(self):
        self.manager = TrelloManager(self._board)
        self.lists = self._get_lists()

    def _get_archived_cards(self):
        cards = {}
        for key in self.label.values():
            cards[key] = []
        for card in self.manager.board.get_cards(filters={"filter": "closed"}):
            if card.labels:
                for label in card.labels:
                    if label.name in self.label.keys():
                        cards[self.label[label.name]].append(card)
                        break
        return cards

    def _get_lists(self):
        lists = {}
        for list_name in self.label.values():
            lists[list_name] = self.manager.get_list_by_name(f"Gerade nicht kaufen ({list_name})")
        return lists

    def _move_to_category(self, card_dict: typing.Dict[str, typing.List[Card]]):
        for key in card_dict:
            for card in card_dict[key]:
                #card.change_list(self.lists[key].id)
                pass





if __name__ == "__main__":
    task = ShoppingTask()
    cards = task._get_archived_cards()
    task._move_to_category(cards)

