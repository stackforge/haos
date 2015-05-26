from rally.benchmark.context import base
from rally import consts


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

    def setup(self):
        """This method is called before the task start."""
        self.context["recover_commands"] = []
        self.context["checks"] = self.config.get("checks", [])

    def cleanup(self):
        """This method is called after the task finish."""
        pass
