resource "aws_s3_bucket_object" "code_package" {
    bucket = aws_s3_bucket.code_bucket.bucket
    key = "${local.module_name}.zip"
    source = "../../build/zip/${local.module_name}.zip"
}

resource "aws_iam_user" "iam_user" {
    name = "trello-manager-${var.environment}"
}

data "aws_iam_policy_document" "lambda_policy" {
    statement {
        sid = "AssumeLambda"
        effect = "Allow"
        actions = [
            "sts:AssumeRole"
        ]
        principals {
            type = "Service"
            identifiers = [
                "lambda.amazonaws.com"
            ]
        }
    }
}

data "aws_iam_policy_document" "allow_lambda_exec_document" {
    statement {
        sid = "TrelloManagerCreateLogs"
        effect = "Allow"
        actions = [
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:DescribeLogStreams"
        ]
        resources = [
            "*"]
    }
}

resource "aws_iam_role" "lambda_role" {
    name = "trello-manager-lambda-role"
    assume_role_policy = data.aws_iam_policy_document.lambda_policy.json
}

resource "aws_iam_role_policy" "lambda_exec" {
    name = "trello-manager-lambda-exec"
    policy = data.aws_iam_policy_document.allow_lambda_exec_document.json
    role = aws_iam_role.lambda_role.id
}

resource "aws_lambda_function" "lambda_function" {
    s3_bucket = aws_s3_bucket.code_bucket.bucket
    s3_key = "trello_manager.zip"
    description = "Moving some Tasks from A to B."
    function_name = "trello-manager"
    role = aws_iam_role.lambda_role.arn
    handler = "lambda_handler.lambda_handler"
    runtime = "python3.12"
    timeout = 240
    reserved_concurrent_executions = 1
    environment {
        variables = {
            TRELLO_API_KEY = var.trello_key,
            TRELLO_API_SECRET = var.trello_secret,
        }
    }
    depends_on = [
        aws_s3_bucket_object.code_package]
}

resource "aws_cloudwatch_event_rule" "scheduled_rule" {
    name = "trigger-trello-manager"
    schedule_expression = var.cron_schedule
    is_enabled = true
}

resource "aws_lambda_permission" "lambda_permission" {
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.lambda_function.function_name
    principal = "events.amazonaws.com"
    statement_id = "AllowExecutionForTrigger"
    source_arn = aws_cloudwatch_event_rule.scheduled_rule.arn
}

resource "aws_cloudwatch_event_target" "scheduled_rule_target" {
    arn = aws_lambda_function.lambda_function.arn
    rule = aws_cloudwatch_event_rule.scheduled_rule.name
}

resource "aws_cloudwatch_log_group" "log_group" {
    name = "/aws/lambda/${aws_lambda_function.lambda_function.function_name}"
    retention_in_days = 30
}

