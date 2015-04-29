#!/bin/bash

echo "Verifying your env (have you tuned etc/openrc already?)"

if [ -z ${SHAKER_SERVER_ENDPOINT} ]; then
    echo "Specify value for SHAKER_SERVER_ENDPOINT env var"
    exit 1
fi

if [ -z ${FUEL_HOST} ]; then
    echo "Specify value for FUEL_HOST env var"
    exit 1
fi

if [ -z ${OS_AUTH_URL} ]; then
    echo "Specify value for OS_AUTH_URL env var"
    exit 1
fi
