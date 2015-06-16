import random

from haos.rally.plugin import base_disaster
from rally.benchmark.scenarios import base
from rally.common import log as logging


LOG = logging.getLogger(__name__)


class RunCommand(base_disaster.BaseDisaster):

    @base.scenario()
    def run_command_on_random_controller(self, command='', timeout=300):
        """This scenario executes bash command on random controller

        :param command: command which should be executed
        :param timeout: how long we will wait for command execution
        """
        controller_id = random.randint(0, len(self.context["controllers"]) - 1)
        controller = self.context["controllers"][controller_id]

        LOG.info('Running command on controller: %s', controller)
        self.run_remote_command(controller, command, timeout)
