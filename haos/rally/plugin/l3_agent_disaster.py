# coding=utf-8
from rally.benchmark.scenarios import base

from haos.rally.plugin import base_disaster
from haos.rally import utils
from rally.common import log as logging
import time

LOG = logging.getLogger(__name__)


class NeutronL3Disaster(base_disaster.BaseDisaster):

    def get_node_on_what_is_agent_for_router(self, router_id):
        """Return node on what is l3 agent for received router

        :param router_id: id router for which find agent node
        :return: name of node
        """
        neutron_client = self.clients("neutron")
        agents = neutron_client.list_l3_agent_hosting_routers(router_id)

        if len(agents) == 0:
            raise "Router hasn't any l3-agent"

        return agents['agents'][0]['host']

    def ban_l3_agent_on_node(self, node):
        """Ban l3 agent on the received node

        :param node: controller on which we should ban l3-agent
        :return:
        """
        command = "pcs resource ban p-neutron-l3-agent " + node
        utils.run_command(self.context, node, command=command,
                          executor="shaker")

    # TODO(sbelous): write function wait some time
    def wait_some_time(self):
        pass

    @base.scenario()
    def ban_one_l3_agent(self):
        """Ban one Neutron L3 agent and verify cloud

        Setup:
        OpenStack cloud with at least 3 controllers	16

        Scenario:
        1. Define network1, networks2, which was created by install context
        2. Define router1 and router2 id, which was also created by install
           context
        3. Boot vm1 in network1 and associate floating ip
        4. Boot vm2 in network2 and associate floating ip
        5. Add rules for ping
        6. ping vm1 and vm2 from each other with floatings ip
        7. get node with l3 agent on what is router1
        8. ban this l3 agent on the node with pcs
        9. wait some time
        10. Boot vm3 in network1 and associate floating ip
        11. ping vm1 and vm3 from each other with internal ip
        12. ping vm2 and vm1 from each other with floating ip
        13. ping vm2 and vm3 from each othe with floating ip
        """
        # for test we need 2 networks in context
        quantity_of_networks_for_test = 2

        networks = self.context["tenant"].get("networks")
        if networks is None:
            message = "Networks haven't been created with context for the " \
                      "test ban_one_l3_agent"
            LOG.debug(message)
            raise

        if len(networks) < quantity_of_networks_for_test:
            message = "Haven't enough networks for the test ban_one_l3_agent"
            LOG.debug(message)
            raise

        network1 = networks[0]
        network2 = networks[1]

        print("net1 = " + network1['name'])
        print("net2 = " + network2['name'])

        router1_id = network1.get("router_id")
        print("router1 = " + router1_id)

        net1_id = network1["id"]
        net2_id = network2["id"]

        vm1 = self.boot_server("VM1", nics=[{"net-id": net1_id}])
        vm2 = self.boot_server("VM2", nics=[{"net-id": net2_id}])

        # Add rules to be able ping
        self.add_rules_for_ping()

        # floatingIp for VMs
        self._attach_floating_ip(vm1, "net04_ext")
        self._attach_floating_ip(vm2, "net04_ext")

        # Define internal IP and floating IP
        net1_name = network1["name"]
        net2_name = network2["name"]
        vm1_internal_ip = self.define_fixed_ip_for_vm(vm1, net1_name)
        vm1_floating_ip = self.define_floating_ip_for_vm(vm1, net1_name)
        vm2_floating_ip = self.define_floating_ip_for_vm(vm2, net2_name)

        # Check connectivity
        self.check_connectivity("VM2", "8.8.8.8")
        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        # Check on what agents are router1 and ban this agent
        node_with_agent = self.get_node_on_what_is_agent_for_router(router1_id)
        self.ban_l3_agent_on_node(node=node_with_agent)

        # TODO(sbelous): wait some time
        self.wait_some_time()

        self.check_reschedule_for_l3_on_node(node=node_with_agent)

        vm3 = self.boot_server("VM3", nics=[{"net-id": net1_id}])

        vm3_internal_ip = self.define_fixed_ip_for_vm(vm3, net1_name)

        # Check connectivity
        self.check_connectivity("VM3", "8.8.8.8")

        self.check_connectivity("VM1", vm3_internal_ip)
        self.check_connectivity("VM3", vm1_internal_ip)

        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        self.check_connectivity("VM3", vm2_floating_ip)

    @base.scenario()
    def ban_some_l3_agents(self):
        """Ban some l3 agents

        Setup:
        OpenStack cloud with at least 3 controllers

        Scenario:

        4) Check ping 8.8.8.8
        5) Ping each other with floatings ip
        6) Ban l3-agents on which this new routers are
        7) Boot one more vm3 in the first net
        8) Check ping 8.8.8.8
        9) Ping vm1, vm2 and vm3 with their floatings ip
        10) from vm3 ping vm1 by internal ip

        Scenario:
        1. Define network1, networks2, which was created by install context
        2. Define router1 and router2 id, which was also created by install
           context
        3. Boot vm1 in network1 and associate floating ip
        4. Boot vm2 in network2 and associate floating ip
        5. Add rules for ping
        6. ping vm1 and vm2 from each other with floatings ip
        7. get node with l3 agent on what is router1
        8. ban this l3 agent on the node with pcs
        9. wait some time
        10. Boot vm3 in network1 and associate floating ip
        11. ping vm1 and vm3 from each other with internal ip
        12. ping vm2 and vm1 from each other with floating ip
        13. ping vm2 and vm3 from each othe with floating ip
        """
        # for test we need 2 networks in context
        quantity_of_networks_for_test = 2

        networks = self.context["tenant"].get("networks")
        if networks is None:
            message = "Networks haven't been created with context for the " \
                      "test ban_one_l3_agent"
            LOG.debug(message)
            raise

        if len(networks) < quantity_of_networks_for_test:
            message = "Haven't enough networks for the test ban_one_l3_agent"
            LOG.debug(message)
            raise

        network1 = networks[0]
        network2 = networks[1]

        print("net1 = " + network1['name'])
        print("net2 = " + network2['name'])

        router1_id = network1.get("router_id")
        print("router1 = " + router1_id)

        net1_id = network1["id"]
        net2_id = network2["id"]

        vm1 = self.boot_server("VM1", nics=[{"net-id": net1_id}])
        vm2 = self.boot_server("VM2", nics=[{"net-id": net2_id}])

        # Add rules to be able ping
        self.add_rules_for_ping()

        # floatingIp for VMs
        self._attach_floating_ip(vm1, "net04_ext")
        self._attach_floating_ip(vm2, "net04_ext")

        # Define internal IP and floating IP
        net1_name = network1["name"]
        net2_name = network2["name"]
        vm1_internal_ip = self.define_fixed_ip_for_vm(vm1, net1_name)
        vm1_floating_ip = self.define_floating_ip_for_vm(vm1, net1_name)
        vm2_floating_ip = self.define_floating_ip_for_vm(vm2, net2_name)

        # Check connectivity
        self.check_connectivity("VM2", "8.8.8.8")
        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        quantity_of_l3_agents = len(self.get_list_l3_agents())
        node_with_banned_l3_agents = []
        for i in xrange(quantity_of_l3_agents - 1):
            # Check on what agents are router1 and ban this agent
            node_with_agent = self.get_node_on_what_is_agent_for_router(
                router1_id)
            node_with_banned_l3_agents.append(node_with_agent)
            self.ban_l3_agent_on_node(node=node_with_agent)
            # TODO(sbelous): wait some time
            self.wait_some_time()
            time.sleep(15)

        if node_with_banned_l3_agents is None:
            raise
        for node_with_banned_agent in node_with_banned_l3_agents:
            self.check_reschedule_for_l3_on_node(node_with_banned_agent)

        vm3 = self.boot_server("VM3", nics=[{"net-id": net1_id}])

        vm3_internal_ip = self.define_fixed_ip_for_vm(vm3, net1_name)

        # Check connectivity
        self.check_connectivity("VM3", "8.8.8.8")

        self.check_connectivity("VM1", vm3_internal_ip)
        self.check_connectivity("VM3", vm1_internal_ip)

        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        self.check_connectivity("VM3", vm2_floating_ip)
