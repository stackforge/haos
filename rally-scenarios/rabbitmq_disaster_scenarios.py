import base_disaster_scenario
from rally.benchmark.scenarios import base


class BaseDisasterScenario(base_disaster_scenario.BaseDisasterScenario):

    @base.scenario()
    def test_rabbitmq_failover01(self):
        """ Test Scenario:

        1. Deploy OpenStack cloud with 3 controllers
        2. Stop RabbitMQ services on all controllers
        3. Start RabbitMQ on one controller
        4. Create VM 10 times, create networks, volumes, upload images,
           create users and etc.
        5. Start all RabbitMQ services and repeat step #4
        """

        for i in xrange(0, 3):
            self.run_disaster_command(self.context["controllers"][i],
                                      "stop rabbitmq service")

        self.run_command(self.context["controllers"][0],
                         "/etc/init.d/rabbitmq-server start")

        # (tnurlygayanov): TODO:
        # Need to write the functions which will verify that cloud
        # works fine: create/delete several VMs, networks, images,
        # volumes and etc.
        if i in xrange(0, 10):                         
            self.boot_vm("test{0}".format(i))

        for i in xrange(0, 3):
            self.run_command(self.context["controllers"][i],
                             "/etc/init.d/rabbitmq-server start")