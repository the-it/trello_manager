def lambda_handler(event, _):
    """
    handler for the lambda framework in the AWS. The event is not picked up because packy is cron triggered.
    """
    print("Hello Trello World")
