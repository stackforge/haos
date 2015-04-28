#!/bin/bash -xe

SERVER_ENDPOINT=$1

for i in `fuel nodes 2>/dev/null | grep ready | awk '{print $1}'`
do
    NODE_NAME="node-${i}"
    echo "Hacking ${NODE_NAME}"
    scp hack_openstack_node.sh ${NODE_NAME}:/root/
    ssh ${NODE_NAME} "/root/hack_openstack_node.sh ${SERVER_ENDPOINT} ${NODE_NAME}"
done
