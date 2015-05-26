import random
import time

from haos.rally.plugin import base_disaster
from rally.benchmark.scenarios import base
from rally.common import log as logging


LOG = logging.getLogger(__name__)


class ControllerShutdown(base_disaster.BaseDisaster):

    @base.scenario()
    def power_off_and_on_one_controller(self):
        """This scenario selects one controller and shutdown it

        Controller will be selected randomly, after the shutdown
        this controller will be started again.

        Setup:
        OpenStack cloud with at least 3 controllers.
        """
        controller_id = random.randint(0, len(self.context["controllers"]) - 1)
        controller = self.context["controllers"][controller_id]
        power_control_node = self.context["power_control_node"]

        self.run_remote_command(power_control_node,
                                command=controller["hardware_power_off_cmd"])
        time.sleep(controller["power_off_timeout"])

        self.run_remote_command(power_control_node,
                                command=controller["hardware_power_on_cmd"])
        time.sleep(controller["power_on_timeout"])
