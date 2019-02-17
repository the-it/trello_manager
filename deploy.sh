#!/usr/bin/env bash

LAMBDA_NAME=trello_manager
SCRIPT_DIR="$(cd "$(dirname "$0")" ; pwd -P)"

pushd "terraform" > /dev/null
VERSION=$(cat zip/version.txt)
rm -rf .terraform
terraform init
terraform apply -var "lambda_version=${VERSION}"

popd > /dev/null
