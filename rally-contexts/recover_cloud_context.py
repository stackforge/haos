import json
import requests
import time
from rally.benchmark.context import base
from rally.common import log as logging
from rally import consts
from rally import osclients

LOG = logging.getLogger(__name__)


@base.context(name="recover_cloud", order=900)
class CloudNodesContext(base.Context):
    """This context allows to recover cloud after disaster tests"""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "additionalProperties": False,
        "properties": {
            "checks": {
                "type": "array",
                "default": []
            }
        }
    }

    def check_rabbitmq_cluster_status(self, controllers):
        command = "rabbitmqctl cluster_status"

        for controller in controllers:
            nodes = []
            active_nodes = []

            output = self.run_command(controller["shaker_agent_id"], command)
            for line in output.splitlines():
                if "nodes" in line and "running_nodes" not in line:
                    nodes = [node for node in line.split("'")
                             if "rabbit" in node]
                if "running_nodes" in line:
                    active_nodes = [node for node in line.split("'")
                                    if "rabbit" in node]

            if len(nodes) == 0 or len(active_nodes) < len(nodes):
                return False

            for node in nodes:
                if node not in active_nodes:
                    return False
        return True

    def run_command(self, node, command, recover_command=None,
                    recover_timeout=0):
        if recover_command is not None:
            action = {"node": node, "command": command,
                      "timeout": recover_timeout}
            self.context["recover_commands"].append(action)

        r = requests.post("http://{0}/run_command".format(node),
                          headers={"Content-Type": "application/json"},
                          data=json.dumps({"command": command}))

        return r.text

    def setup(self):
        """This method is called before the task start"""
        self.context["recover_commands"] = []
        self.context["checks"] = self.config.get("checks", [])

    def cleanup(self):
        """This method is called after the task finish"""
        for action in self.context["recover_commands"]:
            self.run_command(action["node"], action["command"])
            time.sleep(action.get("timeout", 0))

        controllers = self.context["controllers"]
        if "rabbitmq_cluster_status" in self.context["checks"]:
            if self.check_rabbitmq_cluster_status(controllers) is False:
                raise "RabbitMQ cluster wasn't recovered"
