import time

from cloud_utils import run_command
from rally.benchmark.scenarios import base
from rally.benchmark.scenarios.nova import utils as nova_utils


class BaseDisasterScenario(nova_utils.NovaScenario):

    USER_DATA = """#!/bin/bash
        shaker-agent --agent-id `hostname` --server-endpoint {0}
    """

    def wait_shaker_agent(self, agent_id, timeout=300):
        result = run_command(self.context, agent_id, "hostname",
                             executor="shaker", timeout=timeout)
        print result

    def boot_server(self, name):
        nova = self.admin_clients("nova")
        userdata = self.USER_DATA.format(self.context["shaker_endpoint"])
        kwargs = {"userdata": userdata}

        vm = self._boot_server(name=name,
                               image_id=self.context["shaker_image"],
                               flavor_id=self.context["default_flavor"],
                               auto_assign_nic=True,
                               **kwargs)

        wait_shaker_agent(name, timeout=300)

        return vm

    def power_off_controller(self, controller_id):
        control_node = self.context["power_control_node"]
        controller = self.context["controllers"][controller_id]

        run_command(self.context, control_node["agent_endpoint"],
                    command=controller["hardware_power_off_cmd"],
                    recover_command=controller["hardware_power_on_cmd"],
                    recover_timeout=controller["power_on_timeout"])
        time.sleep(controller["power_off_timeout"])

    def power_off_main_controller(self):
        pass
