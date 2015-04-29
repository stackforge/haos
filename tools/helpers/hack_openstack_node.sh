#!/bin/bash -xe

SERVER_ENDPOINT=$1
AGENT_ID=$(hostname)

cd /root/
if [ ! -d ".venv" ]; then
    wget https://bootstrap.pypa.io/get-pip.py
    python get-pip.py
    pip install virtualenv
    virtualenv .venv
    sudo apt-get install -y python-dev
fi

.venv/bin/pip install --upgrade pyshaker-agent

killall shaker-agent || true
screen -dmS shaker-agent-screen /root/.venv/bin/shaker-agent --server-endpoint ${SERVER_ENDPOINT} --agent-id ${AGENT_ID} --log-file /var/log/shaker-agent.log --debug
#    ssh root@${NODE_NAME} '(crontab -l ; echo "@reboot python /root/dummy_shaker_agent.py &") | sort - | uniq - | crontab -'
