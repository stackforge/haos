from rally.benchmark.context import base
from rally.common import log as logging
from rally import consts
from rally import osclients

LOG = logging.getLogger(__name__)


@base.context(name="cloud_nodes", order=800)
class CloudNodesContext(base.Context):
    """This context allows to define the list of nodes in the cloud"""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "additionalProperties": False,
        "properties": {
            "controllers": {
                "type": "array",
                "default": []
            },
            "power_control_node": {
                "type": "object",
                "default": {}
            }
        }
    }

    def setup(self):
        """This method is called before the task start"""
        self.context["controllers"] = self.config.get("controllers", [])
        power_control_node = self.config.get("power_control_node", {})
        self.context["power_control_node"] = power_control_node

    def cleanup(self):
        """This method is called after the task finish"""
        self.context["controllers"] = []
