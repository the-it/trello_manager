#!/usr/bin/env bash

LAMBDA_NAME=trello_manager
ROOT_DIR="$(cd "$(dirname "$0")" ; pwd -P)"
WORK_DIR="${ROOT_DIR}/build"
VERSION=`date '+%Y%m%d_%H%M%S'`
ZIP_FOLDER="${ROOT_DIR}/terraform/zip"
VENV_FOLDER="${WORK_DIR}/venv"
TARGET_TMP="${WORK_DIR}/target"

# Cleanup temp folders
rm -rf ${WORK_DIR}
rm -rf ${ZIP_FOLDER}
mkdir -p ${ZIP_FOLDER}
mkdir -p ${TARGET_TMP}

pushd ${WORK_DIR}

python3 -m venv ${VENV_FOLDER}
source ${WORK_DIR}/venv/bin/activate

pushd ${ROOT_DIR}

pip install -r requirements.txt

#venv/bin/nosetests


cp -r ${WORK_DIR}/venv/lib/python3.*/site-packages/* ${TARGET_TMP}
deactivate

cp -r src/* ${TARGET_TMP}

pushd ${TARGET_TMP}
zip -r lambda-${VERSION}.zip .
mv lambda-${VERSION}.zip "${ZIP_FOLDER}"
echo "Created lambda-${VERSION}.zip for ${LAMBDA_NAME}"

pushd ${ZIP_FOLDER}
echo "${VERSION}" > version.txt

popd