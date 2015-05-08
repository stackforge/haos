#!/bin/bash

TOP_DIR=$(cd $(dirname "$0") && pwd)

SCENARIO=$1

if [ ! -z ${SCENARIO} ]; then
    rally --verbose --plugin-path ${TOP_DIR}/../haos/rally/context,${TOP_DIR}/../haos/rally/plugin task start ${SCENARIO}
fi
