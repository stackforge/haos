from rally.benchmark.scenarios import base


class BaseDisasterScenario(base.Scenario):

    def boot_vm(self):
        self._boot_server(self.context["shaker_image"],
                          self.context["default_flavor",
                          {"auto_assign_nic": True})

    def execute_command_on_shaker_node(self, node, command):
        return None

    def run_command(self, node, command):
        return self.execute_command_on_shaker_node(node, command)

    def run_disaster_command(self, node, command):
        do = self.context["actions"][command]["do"]
        
        done = {"node": node, "command": command}
        self.context["done_actions"].append(done)
        
        self.execute_command_on_shaker_node(node, command)