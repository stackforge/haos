import base_disaster_scenario
from rally.benchmark.scenarios import base


class BaseDisasterScenario(base_disaster_scenario.BaseDisasterScenario):

    @base.scenario()
    def test_scenario_1(self):
        self.run_disaster_command(self.context["controllers"][0],
                                  "stop rabbitmq service")

        ## need to extend it
        self.boot_vm()