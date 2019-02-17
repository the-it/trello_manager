terraform {
  backend "s3" {
    profile    = "default"
    bucket     = "ersotech-terraform-shared-state"
    key        = "trello-manager.tfstate"
    region     = "eu-central-1"
    encrypt    = "true"
  }
}

