from rally.benchmark.context import base
from rally import consts

from haos.rally.utils import run_command


@base.context(name="recover_cloud", order=900)
class CloudNodesContext(base.Context):
    """This context allows to recover cloud after disaster tests."""

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

            output = run_command(self.context, controller["agent_endpoint"],
                                 command)
            rabbit_nodes = lambda str: [node for node in str.split("'")
                                        if "rabbit" in node]
            for line in output.splitlines():
                if "running_nodes" in line:
                    active_nodes = rabbit_nodes(line)
                elif "nodes" in line:
                    nodes = rabbit_nodes(line)

            if not nodes or len(active_nodes) < len(nodes):
                return False

            for node in nodes:
                if node not in active_nodes:
                    return False
        return True

    def setup(self):
        """This method is called before the task start."""
        self.context["recover_commands"] = []
        self.context["checks"] = self.config.get("checks", [])

    def cleanup(self):
        """This method is called after the task finish."""
        pass
        # for action in self.context["recover_commands"]:
        #     run_command(self.context, action["node"], action["command"],
        #                 action["executor"])
        #     time.sleep(action.get("timeout", 0))
        #
        # controllers = self.context["controllers"]
        # if "rabbitmq_cluster_status" in self.context["checks"]:
        #     if self.check_rabbitmq_cluster_status(controllers) is False:
        #         raise Exception("RabbitMQ cluster wasn't recovered")
