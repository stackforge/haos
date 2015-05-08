# Copyright (c) 2015 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import signal

from rally.benchmark import types
from rally import exceptions
import requests
from shaker import lib


def timeout_alarm(signum, frame):
    msg = "Agent not respond"
    raise exceptions.TimeoutException(msg)


def run_command(context, node, command, recover_command=None,
                recover_timeout=0, executor="dummy", timeout=300):
    if recover_command is not None:
        action = {"node": node, "command": recover_command,
                  "timeout": recover_timeout, "executor": executor}
        context["recover_commands"].append(action)

    signal.signal(signal.SIGALRM, timeout_alarm)
    signal.alarm(timeout)
    if executor == "dummy":
        r = requests.post("http://{0}/run_command".format(node),
                          headers={"Content-Type": "application/json"},
                          data=json.dumps({"command": command}))
        return r.text
    elif executor == "shaker":
        shaker = context.get("shaker")
        if not shaker:
            shaker = lib.Shaker(context["shaker_endpoint"], [],
                                agent_loss_timeout=600)
            context["shaker"] = shaker
        r = shaker.run_script(node, command)
        return r.get('stdout')


def get_server_agent_id(server):
    for net, interfaces in server.addresses.items():
        for interface in interfaces:
            if interface.get('OS-EXT-IPS:type') == 'fixed':
                return interface.get('OS-EXT-IPS-MAC:mac_addr')

    raise Exception('Could not get MAC address from server: %s', server.id)


def get_server_net_id(clients, server):
    net_name = server.addresses.keys()[0]
    net_id = types.NeutronNetworkResourceType.transform(
        clients=clients, resource_config=net_name)
    return net_id
