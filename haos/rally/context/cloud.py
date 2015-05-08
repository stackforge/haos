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

import os

from rally.benchmark.context import base
from rally.benchmark.context.cleanup import manager as resource_manager
from rally.common import log as logging
from rally import consts

from haos.remote import server


LOG = logging.getLogger(__name__)


@base.context(name="cloud", order=800)
class CloudNodesContext(base.Context):
    """This context allows to define the list of nodes in the cloud."""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "additionalProperties": False,
        "properties": {
        }
    }

    def setup(self):
        env_vars = {
            'HAOS_SERVER_ENDPOINT': None,
            'HAOS_IMAGE': None,
            'HAOS_FLAVOR': None,
            'HAOS_JOIN_TIMEOUT': 100,
            'HAOS_COMMAND_TIMEOUT': 10
        }

        for var, def_value in env_vars.items():
            value = os.environ.get(var) or def_value
            if not value:
                raise ValueError('Env var %s must be set', var)
            self.context[var.lower()] = value

        boss_inst = server.Server(self.context["haos_server_endpoint"])
        self.context["haos_remote_control"] = boss_inst.remote_control

    def cleanup(self):
        """This method is called after the task finish."""
        resource_manager.cleanup(names=["nova.servers"],
                                 users=self.context.get("users", []))
