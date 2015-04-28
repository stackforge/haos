#!/bin/bash -xe

TOP_DIR=$(cd $(dirname "$0") && pwd)
MARKER="${TOP_DIR}/../.installed"

if [ ! -f "${MARKER}" ]; then
    echo "Install Shaker agents onto OpenStack nodes"

    sshpass -p ${FUEL_PASSWORD} scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${TOP_DIR}/helpers/hack_fuel_master.sh ${FUEL_USERNAME}@${FUEL_HOST}:/root/
    sshpass -p ${FUEL_PASSWORD} scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${TOP_DIR}/helpers/hack_openstack_node.sh ${FUEL_USERNAME}@${FUEL_HOST}:/root/
    sshpass -p ${FUEL_PASSWORD} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${FUEL_USERNAME}@${FUEL_HOST} /root/hack_fuel_master.sh ${SHAKER_SERVER_ENDPOINT}

    touch ${MARKER}
fi