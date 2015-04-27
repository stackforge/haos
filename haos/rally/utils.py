import json

from rally import exceptions
import requests
from shaker import lib
import signal


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
        return r['stdout']
