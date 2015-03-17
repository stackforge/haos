from rally.benchmark.context import base
from rally.common import log as logging
from rally import consts
from rally import osclients

LOG = logging.getLogger(__name__)


@base.context(name="recover_cloud", order=999)
class CloudNodesContext(base.Context):
    """This context allows to recover cloud after disaster tests"""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "additionalProperties": False,
        "properties": {}
    }

    ACTIONS = {
        "stop rabbitmq service": {
            "do": "/etc/init.d/rabbitmq-server stop",
            "undo": "/etc/init.d/rabbitmq-server start"
        },
        "ban rabbitmq service with pcs": {
            "do": "pcs resource ban rabbitmq",
            "undo": "pcs resource clear rabbitmq"
        }
    }

    def setup(self):
        """This method is called before the task start"""
        self.context["actions"] = self.ACTIONS

        # done_actions contains information about name of shaiker_id
        # and action name which were executed, example:
        # self.context["done_actions"] = [{"name": "node-1", "command": "ls"}]
        self.context["done_actions"] = []

    def cleanup(self):
        """This method is called after the task finish"""
        for action in self.context["done_actions"]:
            ## we need to import shaiker somehow :)
            shaiker.run_command_on_node(action["node"],
                                        ACTIONS[action["command"]]["undo"])
