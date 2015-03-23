import random
from . import base_disaster_scenario
from rally.benchmark.scenarios import base


class RabbitMQDisasterScenarios(base_disaster_scenario.BaseDisasterScenario):

    @base.scenario()
    def power_off_one_controller(self):
        """ Poweroff one contoller and verify cloud

        Setup:
        OpenStack cloud with at least 3 controllers

        Scenario:
        1. Poweroff one controller
        2. Verify cloud: create VM 10 times, create networks,
           volumes, upload images
        """

        controller_id = random.randint(0, len(self.context["controllers"]))
        self.power_off_controller(controller_id)

        vm_list = []
        for i in xrange(0, 10):
            vm = self.boot_vm("test{0}".format(i))
            vm_list.append(vm)

        timeout = 300
        active_vms = []
        while timeout > 0 and len(active_vms) < 10:
            active_vms = [vm for vm in vm_list if vm.state == "ACTIVE"]
            timeout -= 1

        if len(active_vms) < 10:
            raise "Can't boot VMs"
