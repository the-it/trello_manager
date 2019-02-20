import os

from trello import TrelloClient

def lambda_handler(event, _):
    """
    handler for the lambda framework in the AWS. The event is not picked up because packy is cron triggered.
    """
    print("Hello Trello World")
    client = TrelloClient(
        api_key=os.environ["TRELLO_API_KEY"],
        api_secret=os.environ["TRELLO_API_SECRET"]
    )
    all_boards = client.list_boards()
    print(all_boards[-1])
    cards = all_boards[-1].get_cards(filters={"filter":"closed"})
    print(cards[-1])
