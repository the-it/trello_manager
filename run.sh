#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

BASENAME=$(basename "$0")
CANONICAL_SCRIPT=$(readlink -e "$0")
SCRIPT_DIR=$(dirname "${CANONICAL_SCRIPT}")

# build stuff
LAMBDA_NAME=trello_manager
WORK_DIR="${SCRIPT_DIR}/build"
VERSION=`date '+%Y%m%d_%H%M%S'`
ZIP_FOLDER="${SCRIPT_DIR}/terraform/zip"
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
terraform
    plan
    apply
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
    echo $VERSION
}

pushd "${SCRIPT_DIR}" > /dev/null
OPERATION=${1:-}

case ${OPERATION} in
terraform)
    COMMAND=${2:-}
    case ${COMMAND} in
	apply)
		echo "apply"
		;;
	plan)
		echo "plan"
		;;
	*)
		exit_with_usage
		;;
	esac
	;;
build)
	build
	;;
*)
	exit_with_usage
	;;
esac

popd > /dev/null
