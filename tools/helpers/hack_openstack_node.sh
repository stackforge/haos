#!/bin/bash -xe

SERVER_ENDPOINT=$1
AGENT_ID=$(hostname)

cd /root/

killall haosagent || true
screen -dmS shaker-agent-screen /root/haosagent ${SERVER_ENDPOINT} ${AGENT_ID}
(crontab -l ; echo "@reboot /root/haosagent ${SERVER_ENDPOINT} ${AGENT_ID} &") | sort - | uniq - | crontab -
