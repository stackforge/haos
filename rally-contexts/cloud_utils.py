import json
import requests
import signal

from rally import exceptions
from shaker.lib import Shaker


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
        shaker = Shaker(context["shaker_endpoint"], [node])
        r = shaker.run_program(node, command)
        return r.get('stdout')
