from trello_manager import ShoppingTask


def lambda_handler(event, _):
    """
    handler for the lambda framework in the AWS. The event is not picked up because lambda is cron triggered.
    """
    print("Get the Shopping Cards from the archive and sort them")
    ShoppingTask().run()
