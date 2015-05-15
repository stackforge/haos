#!/bin/bash

TOP_DIR=$(cd $(dirname "$0") && pwd)

RALLY_EXEC="$(which rally)"

if [ -z ${RALLY_EXEC} ]; then
    echo "Install and patch rally"

    TEMP_DIR="$(mktemp -d)"
    cd ${TEMP_DIR}
    git clone git://git.openstack.org/openstack/rally
    cd rally
    RALLY_VERSION="$(git describe --abbrev=0)"
    git checkout ${RALLY_VERSION}
    git apply ${TOP_DIR}/../patches/01-rally-plugin-dir.patch
    git apply ${TOP_DIR}/../patches/02-rally-no-postgresql.patch

    python setup.py install

    rally-manage db recreate
    rally deployment create --fromenv --name=haos
fi
