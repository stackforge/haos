from rally.benchmark.context import base
from rally import consts


@base.context(name="cloud_nodes", order=800)
class CloudNodesContext(base.Context):
    """This context allows to define the list of nodes in the cloud."""

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
            },
            "shaker_endpoint": {
                "type": "string",
                "default": ""
            },
            "shaker_image": {
                "type": "string",
                "default": "TestVM"
            },
            "default_flavor": {
                "type": "string",
                "default": "m1.micro"
            }
        }
    }

    def setup(self):
        """This method is called before the task start."""
        self.context["controllers"] = self.config.get("controllers")
        power_control_node = self.config.get("power_control_node")
        self.context["power_control_node"] = power_control_node
        self.context["shaker_endpoint"] = self.config.get("shaker_endpoint")
        self.context["shaker_image"] = self.config.get("shaker_image")
        self.context["default_flavor"] = self.config.get("default_flavor")

    def cleanup(self):
        """This method is called after the task finish."""
        self.context["controllers"] = []
