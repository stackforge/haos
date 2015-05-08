#!/bin/bash -xe

TOP_DIR=$(cd $(dirname "$0") && pwd)

NETWORK_NAME=${NETWORK_NAME:-net04}
HAOS_SERVER_ENDPOINT=${HAOS_SERVER_ENDPOINT}
IMAGE_NAME=${HAOS_IMAGE:-haos-image}
FLAVOR_NAME=${HAOS_FLAVOR:-haos-flavor}
CLOUD_IMAGE_NAME="haos-cloud-image"

CIRROS_IMAGE_URL="http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img"

error() {
    printf "\e[31mError: %s\e[0m\n" "${*}" >&2
    exit 1
}

message() {
    printf "\e[33m%s\e[0m\n" "${1}"
}

remote_shell() {
    host=$1
    key=$2
    command=$3
    ssh -i ${key} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 cirros@${host} "$command"
}

remote_cp() {
    host=$1
    key=$2
    src=$3
    dst=$4
    scp -i ${key} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 "$src" cirros@${host}:${dst}
}

build_image() {
    message "Installing Haos image, will take some time"

    if [ -z "$(glance image-show ${CLOUD_IMAGE_NAME})" ]; then
        message "Downloading Cirros image"
        glance image-create --name ${CLOUD_IMAGE_NAME} --disk-format qcow2 --container-format bare --is-public True --copy-from ${CIRROS_IMAGE_URL}

        until [ -n "$(glance image-show ${CLOUD_IMAGE_NAME} | grep status | grep active)" ]; do
            sleep 5
        done
    fi

    UUID=$(cat /proc/sys/kernel/random/uuid)

    message "Creating security group"
    SEC_GROUP="haos-access-${UUID}"
    nova secgroup-create ${SEC_GROUP} "Security Group for Haos"
    nova secgroup-add-rule ${SEC_GROUP} icmp -1 -1 0.0.0.0/0
    nova secgroup-add-rule ${SEC_GROUP} tcp 1 65535 0.0.0.0/0
    nova secgroup-add-rule ${SEC_GROUP} udp 1 65535 0.0.0.0/0

    message "Creating flavor"
    if [ -n "$(nova flavor-list | grep ${FLAVOR_NAME})" ]; then
        nova flavor-delete ${FLAVOR_NAME}
    fi
    nova flavor-create --is-public true ${FLAVOR_NAME} auto 64 0 1

    message "Creating key pair"
    KEY_NAME="haos-key-${UUID}"
    KEY="`mktemp`"
    nova keypair-add ${KEY_NAME} > ${KEY}
    chmod og-rw ${KEY}

    message "Booting VM"
    NETWORK_ID=`neutron net-show ${NETWORK_NAME} -f value -c id`
    VM="haos-template-${UUID}"
    nova boot --poll --flavor ${FLAVOR_NAME} --image ${CLOUD_IMAGE_NAME} --key_name ${KEY_NAME} --nic net-id=${NETWORK_ID} --security-groups ${SEC_GROUP} ${VM}

    message "Associating a floating IP with VM"
    FLOATING_IP=`neutron floatingip-create -f value -c floating_ip_address net04_ext | tail -1`
    nova floating-ip-associate ${VM} ${FLOATING_IP}

    message "Waiting for VM to boot up"
    until remote_shell ${FLOATING_IP} ${KEY} "echo"; do
        sleep 10
    done

    message "Installing haos agent into VM"
    remote_cp ${FLOATING_IP} ${KEY} ${TOP_DIR}/agent/haosagent /tmp/haosagent
    remote_shell ${FLOATING_IP} ${KEY} "sudo cp /tmp/haosagent /usr/bin/"
    remote_shell ${FLOATING_IP} ${KEY} "sudo chmod 755 /usr/bin/haosagent"

    HAOSAGENT_INIT="`mktemp`"
    cat > ${HAOSAGENT_INIT} << EOF
#!/bin/sh
case "\$1" in
	start)
	    export HAOS_SERVER_ENDPOINT="${HAOS_SERVER_ENDPOINT}"
		start-stop-daemon -S -b -q -p /var/run/haosagent.pid --exec /usr/bin/haosagent
		echo "OK"
		;;
	stop) :;;
	*) echo "unknown argument ${1}" 1>&2;;
esac
EOF
    remote_cp ${FLOATING_IP} ${KEY} ${HAOSAGENT_INIT} /tmp/S97-haosagent
    remote_shell ${FLOATING_IP} ${KEY} "sudo cp /tmp/S97-haosagent /etc/init.d/"
    remote_shell ${FLOATING_IP} ${KEY} "sudo chmod 755 /etc/init.d/S97-haosagent"
    remote_shell ${FLOATING_IP} ${KEY} "sudo ln -s /etc/init.d/S97-haosagent /etc/rc3.d/"
    remote_shell ${FLOATING_IP} ${KEY} "sudo /sbin/poweroff"
    sleep 10

    message "Making VM snapshot"
    nova image-create --poll ${VM} ${IMAGE_NAME}
    glance image-update --is-public True ${IMAGE_NAME}

    message "Destroy VM"
    nova delete ${VM}

    message "Waiting for VM to die"
    until [ -z "$(nova list | grep ${VM})" ]; do
        sleep 5
    done

    message "Cleaning up resources"
    FP_ID=`neutron floatingip-list -f csv -c id -c floating_ip_address --quote none | grep ${FLOATING_IP} | awk -F "," '{print $1}'`
    neutron floatingip-delete ${FP_ID}

    nova secgroup-delete ${SEC_GROUP}
    nova keypair-delete ${KEY_NAME}
}

main() {
    if [ -z ${HAOS_SERVER_ENDPOINT} ]; then
        error "Set HAOS_SERVER_ENDPOINT env var"
        exit 1
    fi

    if [ -z "$(glance image-show ${IMAGE_NAME})" ]; then
        build_image
    else
        message "Image ${IMAGE_NAME} already exists."
    fi
}

main "$@"
