from trello_manager import ReplayDateTask, ShoppingTask


def lambda_handler(event, _):  # pylint: disable=unused-argument
    """
    handler for the lambda framework in the AWS.
    The event is not picked up because lambda is cron triggered.
    """
    try:
        with open("version.txt") as version_file:
            print(f"Current running version is: {version_file.read()}")
    except FileNotFoundError:
        print("Local Development Mode")
    print("Move the todo cards on the board")
    ReplayDateTask().run()
    print("Get the Shopping Cards from the archive and sort them")
    ShoppingTask().run()
