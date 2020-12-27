locals {
  project_postfix = "tst-1"
}

provider "aws" {
  region = "eu-central-1"
  shared_credentials_file = "~/.aws/creds"
  profile = "ersotech_aws_tst_1"
}

terraform {
  backend "s3" {
    bucket = "terraform-shared-state-ersotech-aws-tst-1"
    key = "terraform/trello_manager_state"
    region = "eu-central-1"
    shared_credentials_file = "~/.aws/creds"
    profile = "ersotech_aws_tst_1"
  }
}

module "trello_manager" {
    source = "../modules/trello_manager"
    environment = local.project_postfix
    trello_key = var.trello_key
    trello_secret = var.trello_secret
}

output "code_uploader_bucket_name" {
    value = module.trello_manager.code_uploader_bucket_name
}

output "code_uploader_id" {
    value = module.trello_manager.code_uploader_id
}

output "code_uploader_secret" {
    value = module.trello_manager.code_uploader_secret
}
