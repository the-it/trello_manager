from trello_manager import ReplayDateTask, ShoppingTask


def lambda_handler(event, _):  # pylint: disable=unused-argument
    """
    handler for the lambda framework in the AWS.
    The event is not picked up because lambda is cron triggered.
    """
    print("Move the todo cards on the board")
    ReplayDateTask().run()
    print("Get the Shopping Cards from the archive and sort them")
    ShoppingTask().run()
