import os

from rally.benchmark.context import base
from rally.benchmark.context.cleanup import manager as resource_manager
from rally.common import log as logging
from rally import consts
from rally import exceptions

from haos.remote import server
from haos.remote import ssh_remote_control


LOG = logging.getLogger(__name__)


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
            "remote_control_type": {
                "type": "string",
                "default": "ssh"
            }
        }
    }

    def setup(self):
        """This method is called before the task start."""
        self.context["controllers"] = self.config.get("controllers")
        remote_control_type = self.config.get("remote_control_type")
        self.context["remote_control_type"] = remote_control_type
        power_control_node = self.config.get("power_control_node")
        self.context["power_control_node"] = power_control_node

        env_vars = {
            'HAOS_SERVER_ENDPOINT': None,
            'HAOS_IMAGE': None,
            'HAOS_FLAVOR': None,
            'HAOS_JOIN_TIMEOUT': 100,
            'HAOS_COMMAND_TIMEOUT': 10
        }

        for var, def_value in env_vars.items():
            value = os.environ.get(var) or def_value
            if value:
                self.context[var.lower()] = value
            else:
                LOG.debug('Env var %s must be set'.format(var))

        if self.context["remote_control_type"] == "ssh":
            ssh = ssh_remote_control.SSHConnection()
            self.context["haos_remote_control"] = ssh.remote_control
        elif self.context["remote_control_type"] == "haos_agents":
            boss_inst = server.Server(self.context["haos_server_endpoint"])
            self.context["haos_remote_control"] = boss_inst.remote_control
        else:
            msg = "remote_control_type {0} doesn't implemented yet.".format(
                self.context["remote_control_type"]
            )
            raise exceptions.RallyException(msg)

    def cleanup(self):
        """This method is called after the task finish."""
        self.context["controllers"] = []
        resource_manager.cleanup(names=["nova.servers"],
                                 users=self.context.get("users", []))
