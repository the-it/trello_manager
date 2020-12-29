#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

BASENAME=$(basename "$0")
CANONICAL_SCRIPT=$(readlink -e "$0")
SCRIPT_DIR=$(dirname "${CANONICAL_SCRIPT}")

# build stuff
LAMBDA_NAME=trello_manager
WORK_DIR="${SCRIPT_DIR}/build"
ZIP_FOLDER="${WORK_DIR}/zip"
VENV_FOLDER="${WORK_DIR}/venv"
TARGET_TMP="${WORK_DIR}/target"

error_exit() {
    echo "ERROR: $1" >&2
    exit 4
}

exit_with_usage() {
    cat <<EOF
    ${BASENAME} <command>

available commands:
terraform <tst/prd>
build
EOF
    exit 1
}

function get_version() {
    if [[ $(git diff --stat) != '' ]]; then
        echo "dev-$(date '+%Y%m%d_%H%M%S')"
    else
        echo `git rev-parse HEAD`
    fi
}

function build() {
    VERSION=`get_version`

    # Cleanup temp folders
    rm -rf ${WORK_DIR}
    mkdir -p ${ZIP_FOLDER}
    mkdir -p ${TARGET_TMP}

    # Install proper dependencies
    python3 -m venv ${VENV_FOLDER}
    source ${VENV_FOLDER}/bin/activate
    pip install -r requirements.txt
    deactivate

    # copy all relevant files to the temporary target folder
    cp -r ${VENV_FOLDER}/lib/python3.*/site-packages/* ${TARGET_TMP}
    cp -r src/* ${TARGET_TMP}
    echo "${VERSION}" > ${TARGET_TMP}/version.txt

    # zip to nice little package
    pushd ${TARGET_TMP}
    zip -r ${LAMBDA_NAME}.zip .
    mv ${LAMBDA_NAME}.zip "${ZIP_FOLDER}"
    echo "Created ${LAMBDA_NAME}.zip for ${LAMBDA_NAME} with version ${VERSION}"
    popd
}

pushd "${SCRIPT_DIR}" > /dev/null
OPERATION=${1:-}

case ${OPERATION} in
terraform)
    ENV=${2:-}
    pushd "terraform/${ENV}" > /dev/null
    terraform init
    terraform apply -var "trello_key=${TRELLO_API_KEY}"   -var "trello_secret=${TRELLO_API_SECRET}"

    popd > /dev/null
    ;;
build)
    build
    ;;
push)
    ENV=${2:-}
    if [ -z "${CIRCLECI+xxx}" ]; then
        echo " LOCAL PUSH"
        export AWS_PROFILE="ersotech_aws_${ENV}_1"
    fi

    aws s3 cp ${ZIP_FOLDER}/${LAMBDA_NAME}.zip s3://trello-manager-code-${ENV}-1/${LAMBDA_NAME}.zip
    aws lambda update-function-code \
        --function-name trello-manager \
        --s3-bucket trello-manager-code-${ENV}-1 \
        --s3-key trello_manager.zip \
        --region eu-central-1
    ;;
*)
    exit_with_usage
    ;;
esac

popd > /dev/null
