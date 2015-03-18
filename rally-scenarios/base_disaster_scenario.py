import json
import requests
from rally.benchmark.scenarios import base


class BaseDisasterScenario(base.Scenario):

    def boot_vm(self, name):
        nova = self.admin_clients("nova")
        vm = nova.servers.create(name=name,
                                 image=self.context["shaker_image"],
                                 flavor=self.context["default_flavor"],
                                 {"auto_assign_nic": True})

    def execute_command_on_shaker_node(self, node, command):
        cmd = {"command": command}
        r = requests.post("http://{0}/run_command".format(node),
                          headers={"Content-Type": "application/json"},
                          data=json.dumps(cmd))

        return r.text

    def run_command(self, node, command):
        return self.execute_command_on_shaker_node(node, command)

    def run_disaster_command(self, node, command):
        do = self.context["actions"][command]["do"]

        done = {"node": node, "command": command}
        self.context["done_actions"].append(done)

        self.execute_command_on_shaker_node(node, command)