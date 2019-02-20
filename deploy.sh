#!/usr/bin/env bash

LAMBDA_NAME=trello_manager
SCRIPT_DIR="$(cd "$(dirname "$0")" ; pwd -P)"

pushd "terraform" > /dev/null
VERSION=$(cat zip/version.txt)

rm -rf .terraform
terraform init
terraform apply -var "lambda_version=${VERSION}" \
                -var "trello_key=${TRELLO_API_KEY}" \
                -var "trello_secret=${TRELLO_API_SECRET}"

popd > /dev/null
