import os
from typing import Union

from trello import TrelloClient, Board, List



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

if __name__ == "__main__":
    pass


