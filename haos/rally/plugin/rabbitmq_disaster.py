import random

from rally.benchmark.scenarios import base

from haos.rally.plugin import base_disaster


class RabbitMQDisaster(base_disaster.BaseDisaster):

    @base.scenario()
    def power_off_one_controller(self):
        """Poweroff one contoller and verify cloud

        Setup:
        OpenStack cloud with at least 3 controllers

        Scenario:
        1. Poweroff one controller
        2. Verify cloud: create VM 10 times
        """

        controller_id = random.randint(0, len(self.context["controllers"]) - 1)
        self.power_off_controller(controller_id)

        for i in xrange(0, 10):
            self.boot_server("test{0}".format(i))
