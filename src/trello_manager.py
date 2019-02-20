import os

from trello import TrelloClient

class TrelloManager:
    def __init__(self, board: str):
        self.client = TrelloClient(
            api_key=os.environ["TRELLO_API_KEY"],
            api_secret=os.environ["TRELLO_API_SECRET"]
        )
        self.board = None

    def tada(self):
        pass

if __name__ == "__main__":
    pass


