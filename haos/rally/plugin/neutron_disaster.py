from rally.benchmark.scenarios import base

from haos.rally.plugin import base_disaster
from haos.rally import utils
from rally.common import log as logging

LOG = logging.getLogger(__name__)


class NeutronDisaster(base_disaster.BaseDisaster):

    def check_all_rescedule(self, node):
        list_agents = self.clients("neutron").list_agents()
        dhcp_for_node = None
        l3_for_node = None
        for agent in list_agents["agents"]:
            if (agent["host"] == node):
                if (agent["agent_type"] == "DHCP agent"):
                    dhcp_for_node = agent
                elif (agent["agent_type"] == "L3 agent"):
                    l3_for_node = agent
        if (l3_for_node) & (dhcp_for_node):
            list_networks = self.clients(
                "neutron").list_networks_on_dhcp_agent(dhcp_for_node["id"])
            if len(list_networks) == 0:
                raise
            list_routers = self.clients(
                "neutron").list_routers_on_l3_agent(l3_for_node["id"])
            if len(list_routers) == 0:
                raise

    # TODO(sbelous): create function find_primary_controller()
    def find_primary_controller(self):
        for controller in self.context["controllers"]:
            node = controller["agent_endpoint"]
            command = "ifconfig | grep br-ex-hapr 1>/dev/null;echo $?"
            result = utils.run_command(self.context, node, command=command,
                                       executor="shaker")
            if result and result[0] == "0":
                return node

        return None

    # TODO(sbelous): write function wait some time
    def wait_some_time(self):
        pass

    @base.scenario()
    def drop_mysql_port(self):
        """Drop mysql port

        Setup:
        OpenStack cloud with at least 3 controllers 16

        Scenario:
        1. Create router1, net1 and subnetwork1 and join router1 with net1
        2. Create router2, net2 and subnetwork2 and join router2 with net2
        3. Start vm1 in network1
        4. Start vm2 in network2
        5. Define floating ip for vm1 and vm2
        6. Define internal ip for vm1
        7. Add rules for ping
        8. ping 8.8.8.8 from vm2
        9. ping vm1 from vm2 and vm1 from vm2
        10. Run udhcp on vm1
        11. Make l3-agent for router1 and dhcp-agent for net1 on the same node
        12. drop rabbit port 3306 on node, where is l3-agent for router1
        13. Boot vm3 in network1
        14. ping 8.8.8.8 from vm3
        15. ping between vm1 and vm3 by internal ip
        16. ping between vm2 and vm3 by floating ip
        17. Run udhcp on vm1 and vm3
        """

        # Add rules to be able ping
        self.add_rules_for_ping()

        # Create 1 network, subnt, router and join this construction
        network1, subnets1, router1 = self.create_network_subnet_router()
        # Create 1 network, subnt, router and join this construction
        network2, subnets2, router2 = self.create_network_subnet_router()

        # boot vms
        net1_id = network1["network"]["id"]
        net2_id = network2["network"]["id"]
        vm1 = self.boot_server("VM1", nics=[{"net-id": net1_id}])
        vm2 = self.boot_server("VM2", nics=[{"net-id": net2_id}])

        # floatingIp for VMs
        self.associate_floating_ip(vm1)
        self.associate_floating_ip(vm2)

        # Define internal IP and floating IP
        net1_name = network1["network"]["name"]
        net2_name = network2["network"]["name"]
        vm1_internal_ip = self.define_fixed_ip_for_vm(vm1, net1_name)
        vm1_floating_ip = self.define_floating_ip_for_vm(vm1, net1_name)
        vm2_floating_ip = self.define_floating_ip_for_vm(vm2, net2_name)

        # Check on what agents are router1
        node = self.get_node_on_what_is_agent_for_router(router1)

        self.get_dhcp_on_chosen_node(node, network1)

        # Check connectivity
        self.check_connectivity("VM2", "8.8.8.8")
        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Drop rabbit MQ port
        command = "iptables -I INPUT 1 -p tcp --dport 3306 -j DROP"
        utils.run_command(self.context, node, command=command)

        vm3 = self.boot_server("VM3", nics=[{"net-id": net1_id}])

        vm3_internal_ip = self.define_fixed_ip_for_vm(vm3, net1_name)
        vm3_floating_ip = self.define_floating_ip_for_vm(vm3, net1_name)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        output = utils.run_command(self.context, "VM3", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Check connectivity
        self.check_connectivity("VM3", "8.8.8.8")

        self.check_connectivity("VM1", vm3_internal_ip)
        self.check_connectivity("VM3", vm1_internal_ip)

        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        self.check_connectivity("VM2", vm3_floating_ip)
        self.check_connectivity("VM3", vm2_floating_ip)

        self.check_connectivity("VM1", vm3_floating_ip)
        self.check_connectivity("VM3 ", vm1_floating_ip)

    @base.scenario()
    def reboot_primary_controller(self):
        """Reboot primary controller

        Setup:
        OpenStack cloud with at least 3 controllers and 1 compute

        Scenario:
        1. Create router1, net1 and subnet1 and join router1 with net1
        2. Create router2, net2 and subnet2 and join router2 with net2
        3. Start vm1 in net1
        4. Start vm2 in net2
        5. Define floating ip for vm1 and vm2
        6. Define internal ip for vm1
        7. Add rules for ping
        8. Find primary controller
        9. Get l3 agent for router1 and dhcp-agent for net1
           on primary controller
        10. ping 8.8.8.8 from vm2
        11. ping vm1 from vm2 and vm1 from vm2
        12. Run udhcp on vm1
        13. Reboot primary controller
        14. Wait some time
        15. Boot vm3 in net1
        16. ping 8.8.8.8 from vm3
        17. ping between vm1 and vm3 by internal ip
        18. ping between vm2 and vm3 by floating ip
        19. Run udhcp on vm1 and vm3
        """

        # Create 1 network, subnt, router and join this construction
        network1, subnets1, router1 = self.create_network_subnet_router()
        # Create 1 network, subnt, router and join this construction
        network2, subnets2, router2 = self.create_network_subnet_router()

        # boot vms
        net1_id = network1["network"]["id"]
        net2_id = network2["network"]["id"]
        vm1 = self.boot_server("VM1", nics=[{"net-id": net1_id}])
        vm2 = self.boot_server("VM2", nics=[{"net-id": net2_id}])

        # Add rules to be able ping
        self.add_rules_for_ping()

        # floatingIp for VMs
        self.associate_floating_ip(vm1)
        self.associate_floating_ip(vm2)

        # Define internal IP and floating IP
        net1_name = network1["network"]["name"]
        net2_name = network2["network"]["name"]
        vm1_internal_ip = self.define_fixed_ip_for_vm(vm1, net1_name)
        vm1_floating_ip = self.define_floating_ip_for_vm(vm1, net1_name)
        vm2_floating_ip = self.define_floating_ip_for_vm(vm2, net2_name)

        # Find primary controller
        primary_controller = self.find_primary_controller()

        # Get l3 agent for router1 and one dhcp agent
        # for network1 on primary controller
        self.get_dhcp_on_chosen_node(primary_controller, network1)
        self.get_l3_on_chosen_node(primary_controller, router1)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Check connectivity
        self.check_connectivity("VM2", "8.8.8.8")
        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        primary_context_controller = None
        for controller in self.context["controllers"]:
            if controller["agent_endpoint"] == primary_controller:
                primary_context_controller = controller
                break
        if primary_context_controller:
            self.power_off_controller(primary_context_controller)
        else:
            raise

        # TODO(sbelous): wait some time
        self.check_all_rescedule(primary_controller)

        vm3 = self.boot_server("VM3", nics=[{"net-id": net1_id}])

        vm3_internal_ip = self.define_fixed_ip_for_vm(vm3, net1_name)
        vm3_floating_ip = self.define_floating_ip_for_vm(vm3, net1_name)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        output = utils.run_command(self.context, "VM3", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Check connectivity
        self.check_connectivity("VM3", "8.8.8.8")

        self.check_connectivity("VM1", vm3_internal_ip)
        self.check_connectivity("VM3", vm1_internal_ip)

        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        self.check_connectivity("VM2", vm3_floating_ip)
        self.check_connectivity("VM3", vm2_floating_ip)

        self.check_connectivity("VM1", vm3_floating_ip)
        self.check_connectivity("VM3 ", vm1_floating_ip)

    @base.scenario()
    def drop_rabbit_port(self):
        """Drop rabbit port

        Setup:
        OpenStack cloud with at least 3 controllers 16

        Scenario:
        1. Create router1, net1 and subnet1 and join router1 with net1
        2. Create router2, net2 and subnet2 and join router2 with net2
        3. Start vm1 in net1
        4. Start vm2 in net2
        5. Define floating ip for vm1 and vm2
        6. Define internal ip for vm1
        7. Add rules for ping
        8. ping 8.8.8.8 from vm2
        9. ping vm1 from vm2 and vm1 from vm2
        10. Run udhcp on vm1
        11. Make l3-agent for router1 and one dhcp-agent for net1
            on the same node
        12. drop rabbit port 5673 on node, where is l3-agent for router1
        13. Boot vm3 in net1
        14. ping 8.8.8.8 from vm3
        15. ping between vm1 and vm3 by internal ip
        16. ping between vm2 and vm3 by floating ip
        17. Run udhcp on vm1 and vm3
        """
        # Add rules to be able ping
        self.add_rules_for_ping()

        # Create 1 network, subnt, router and join this construction
        network1, subnets1, router1 = self.create_network_subnet_router()
        # Create 1 network, subnt, router and join this construction
        network2, subnets2, router2 = self.create_network_subnet_router()

        # boot vms
        net1_id = network1["network"]["id"]
        net2_id = network2["network"]["id"]
        vm1 = self.boot_server("VM1", nics=[{"net-id": net1_id}])
        vm2 = self.boot_server("VM2", nics=[{"net-id": net2_id}])

        # floatingIp for VMs
        self.associate_floating_ip(vm1)
        self.associate_floating_ip(vm2)

        # Define internal IP and floating IP
        net1_name = network1["network"]["name"]
        net2_name = network2["network"]["name"]
        vm1_internal_ip = self.define_fixed_ip_for_vm(vm1, net1_name)
        vm1_floating_ip = self.define_floating_ip_for_vm(vm1, net1_name)
        vm2_floating_ip = self.define_floating_ip_for_vm(vm2, net2_name)

        # Check on what agents are router1
        node = self.get_node_on_what_is_agent_for_router(router1)

        self.get_dhcp_on_chosen_node(node, network1)

        # Check connectivity
        self.check_connectivity("VM2", "8.8.8.8")

        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Drop rabbit MQ port
        command = "iptables -I OUTPUT 1 -p tcp --dport 5673 -j DROP"
        utils.run_command(self.context, node, command=command,
                          executor="shaker")

        vm3 = self.boot_server("VM3", nics=[{"net-id": net1_id}])

        vm3_internal_ip = self.define_fixed_ip_for_vm(vm3, net1_name)
        vm3_floating_ip = self.define_floating_ip_for_vm(vm3, net1_name)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        output = utils.run_command(self.context, "VM3", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Check connectivity
        self.check_connectivity("VM3", "8.8.8.8")

        self.check_connectivity("VM1", vm3_internal_ip)
        self.check_connectivity("VM3", vm1_internal_ip)

        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        self.check_connectivity("VM2", vm3_floating_ip)
        self.check_connectivity("VM3", vm2_floating_ip)

        self.check_connectivity("VM1", vm3_floating_ip)
        self.check_connectivity("VM3 ", vm1_floating_ip)

    @base.scenario()
    def reset_primary_controller(self):
        """Reset primary controller

        Setup:
        OpenStack cloud with at least 3 controllers and 1 compute

        Scenario:
        1. Create router1, net1 and subnet1 and join router1 with net1
        2. Create router2, net2 and subnet2 and join router2 with net2
        3. Start vm1 in net1
        4. Start vm2 in net2
        5. Define floating ip for vm1 and vm2
        6. Define internal ip for vm1
        7. Add rules for ping
        8. Find primary controller
        9. Get l3 agent for router1 and one dhcp agent for net1
           on primary controller
        10. ping 8.8.8.8 from vm2
        11. ping vm1 from vm2 and vm1 from vm2
        12. Run udhcp on vm1
        13. Reset primary controller
        14. Wait some time
        15. Boot vm3 in net1
        16. ping 8.8.8.8 from vm3
        17. ping between vm1 and vm3 by internal ip
        18. ping between vm2 and vm3 by floating ip
        19. Run udhcp on vm1 and vm3
        """

        # Create 1 network, subnt, router and join this construction
        network1, subnets1, router1 = self.create_network_subnet_router()
        # Create 1 network, subnt, router and join this construction
        network2, subnets2, router2 = self.create_network_subnet_router()

        # boot vms
        net1_id = network1["network"]["id"]
        net2_id = network2["network"]["id"]
        vm1 = self.boot_server("VM1", nics=[{"net-id": net1_id}])
        vm2 = self.boot_server("VM2", nics=[{"net-id": net2_id}])

        # Add rules to be able ping
        self.add_rules_for_ping()

        # floatingIp for VMs
        self.associate_floating_ip(vm1)
        self.associate_floating_ip(vm2)

        # Define internal IP and floating IP
        net1_name = network1["network"]["name"]
        net2_name = network2["network"]["name"]
        vm1_internal_ip = self.define_fixed_ip_for_vm(vm1, net1_name)
        vm1_floating_ip = self.define_floating_ip_for_vm(vm1, net1_name)
        vm2_floating_ip = self.define_floating_ip_for_vm(vm2, net2_name)

        # Find primary controller
        primary_controller = self.find_primary_controller()

        # Get l3 agent for router1 and one dhcp agent for network1
        # on primary controller
        self.get_dhcp_on_chosen_node(primary_controller, network1)
        self.get_l3_on_chosen_node(primary_controller, router1)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Check connectivity
        self.check_connectivity("VM2", "8.8.8.8")
        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        primary_context_controller = None
        for controller in self.context["controllers"]:
            if controller["agent_endpoint"] == primary_controller:
                primary_context_controller = controller
                break
        if primary_context_controller:
            self.power_off_controller(primary_context_controller)
        else:
            raise

        # TODO(sbelous): wait some time

        self.check_all_rescedule(primary_controller)

        vm3 = self.boot_server("VM3", nics=[{"net-id": net1_id}])

        vm3_internal_ip = self.define_fixed_ip_for_vm(vm3, net1_name)
        vm3_floating_ip = self.define_floating_ip_for_vm(vm3, net1_name)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        output = utils.run_command(self.context, "VM3", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Check connectivity
        self.check_connectivity("VM3", "8.8.8.8")

        self.check_connectivity("VM1", vm3_internal_ip)
        self.check_connectivity("VM3", vm1_internal_ip)

        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        self.check_connectivity("VM2", vm3_floating_ip)
        self.check_connectivity("VM3", vm2_floating_ip)

        self.check_connectivity("VM1", vm3_floating_ip)
        self.check_connectivity("VM3 ", vm1_floating_ip)

    @base.scenario()
    def destroy_primary_controller(self):
        """Shut destroy primary controller

        Scenario:
        1. Create network1, subnets1, router1
        2. Create network2, subnets2, router2
        2. Launch 2 instances (vm1 and vm2) and associate floating ip
        3. Add rules for ping
        4. Find primary controller
        5. Rescedule network1 and router1 for primary controller
        6. ping 8.8.8.8 from vm2
        7. ping vm1 from vm2 and vm1 from vm2
        8. Run udhcp on vm1
        9. Destroy primary controller (virsh destroy <primary_controller>)
        10. Wait some time
        11. Check that all networks and routers rescedule
            from prrimary controller
        11. Boot vm3 in network1
        12. ping 8.8.8.8 from vm3
        13. ping between vm1 and vm3 by internal ip
        14. ping between vm2 and vm3 by floating ip
        15. Run udhcp on vm1 and vm3
        """
        # Create 1 network, subnt, router and join this construction
        network1, subnets1, router1 = self.create_network_subnet_router()
        # Create 1 network, subnt, router and join this construction
        network2, subnets2, router2 = self.create_network_subnet_router()

        # boot vms
        net1_id = network1["network"]["id"]
        net2_id = network2["network"]["id"]
        vm1 = self.boot_server("VM1", nics=[{"net-id": net1_id}])
        vm2 = self.boot_server("VM2", nics=[{"net-id": net2_id}])

        # Add rules to be able ping
        self.add_rules_for_ping()

        # floatingIp for VMs
        self.associate_floating_ip(vm1)
        self.associate_floating_ip(vm2)

        # Define internal IP and floating IP
        net1_name = network1["network"]["name"]
        net2_name = network2["network"]["name"]
        vm1_internal_ip = self.define_fixed_ip_for_vm(vm1, net1_name)
        vm1_floating_ip = self.define_floating_ip_for_vm(vm1, net1_name)
        vm2_floating_ip = self.define_floating_ip_for_vm(vm2, net2_name)

        # Find primary controller
        primary_controller = self.find_primary_controller()

        # Get l3 agent for router1 and one dhcp agent for network1
        # on primary controller
        self.get_dhcp_on_chosen_node(primary_controller, network1)
        self.get_l3_on_chosen_node(primary_controller, router1)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Check connectivity
        self.check_connectivity("VM2", "8.8.8.8")
        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        primary_context_controller = None
        for controller in self.context["controllers"]:
            if controller["agent_endpoint"] == primary_controller:
                primary_context_controller = controller
                break
        if primary_context_controller:
            self.power_off_controller(primary_context_controller)
        else:
            raise

        # TODO(sbelous): wait some time

        self.check_all_rescedule(primary_controller)

        vm3 = self.boot_server("VM3", nics=[{"net-id": net1_id}])

        vm3_internal_ip = self.define_fixed_ip_for_vm(vm3, net1_name)
        vm3_floating_ip = self.define_floating_ip_for_vm(vm3, net1_name)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        output = utils.run_command(self.context, "VM3", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Check connectivity
        self.check_connectivity("VM3", "8.8.8.8")

        self.check_connectivity("VM1", vm3_internal_ip)
        self.check_connectivity("VM3", vm1_internal_ip)

        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        self.check_connectivity("VM2", vm3_floating_ip)
        self.check_connectivity("VM3", vm2_floating_ip)

        self.check_connectivity("VM1", vm3_floating_ip)
        self.check_connectivity("VM3 ", vm1_floating_ip)

    @base.scenario()
    def destroy_non_primary_controller(self):
        """Destroy non primary controller

        Scenario:
        1. Create network1, subnets1, router1
        2. Create network2, subnets2, router2
        2. Launch 2 instances (vm1 and vm2) and associate floating ip
        3. Add rules for ping
        4. Choose one non primary controller
        5. Rescedule network1 and router1 for chosen non primary controller
        6. ping 8.8.8.8 from vm2
        7. ping vm1 from vm2 and vm1 from vm2
        8. Run udhcp on vm1
        9. Destroy non primary controller
        (virsh destroy <non_primary_controller>)
        10. Wait some time
        11. Check that all networks and routers rescedule
            from non primary controller
        11. Boot vm3 in network1
        12. ping 8.8.8.8 from vm3
        13. ping between vm1 and vm3 by internal ip
        14. ping between vm2 and vm3 by floating ip
        15. Run udhcp on vm1 and vm3
        """

        # Create 1 network, subnt, router and join this construction
        network1, subnets1, router1 = self.create_network_subnet_router()
        # Create 1 network, subnt, router and join this construction
        network2, subnets2, router2 = self.create_network_subnet_router()

        # boot vms
        net1_id = network1["network"]["id"]
        net2_id = network2["network"]["id"]
        vm1 = self.boot_server("VM1", nics=[{"net-id": net1_id}])
        vm2 = self.boot_server("VM2", nics=[{"net-id": net2_id}])

        # Add rules to be able ping
        self.add_rules_for_ping()

        # floatingIp for VMs
        self.associate_floating_ip(vm1)
        self.associate_floating_ip(vm2)

        # Define internal IP and floating IP
        net1_name = network1["network"]["name"]
        net2_name = network2["network"]["name"]
        vm1_internal_ip = self.define_fixed_ip_for_vm(vm1, net1_name)
        vm1_floating_ip = self.define_floating_ip_for_vm(vm1, net1_name)
        vm2_floating_ip = self.define_floating_ip_for_vm(vm2, net2_name)

        # Find primary controller
        primary_controller = self.find_primary_controller()

        # Get l3 agent for router1 and one dhcp agent for network1
        # on primary controller
        self.get_dhcp_on_chosen_node(primary_controller, network1)
        self.get_l3_on_chosen_node(primary_controller, router1)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Check connectivity
        self.check_connectivity("VM2", "8.8.8.8")
        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        non_primary_context_controller = None
        non_primary_controller = None
        for controller in self.context["controllers"]:
            if controller["agent_endpoint"] != primary_controller:
                non_primary_context_controller = controller
                non_primary_controller = controller["agent_endpoint"]
                break
        if non_primary_context_controller:
            self.power_off_controller(non_primary_context_controller)
        else:
            raise

        # TODO(sbelous): wait some time

        self.check_all_rescedule(non_primary_controller)

        vm3 = self.boot_server("VM3", nics=[{"net-id": net1_id}])

        vm3_internal_ip = self.define_fixed_ip_for_vm(vm3, net1_name)
        vm3_floating_ip = self.define_floating_ip_for_vm(vm3, net1_name)

        # dhcp work
        output = utils.run_command(self.context, "VM1", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        output = utils.run_command(self.context, "VM3", command="udhcpc",
                                   executor="shaker")
        LOG.debug("output = %s", output)

        # Check connectivity
        self.check_connectivity("VM3", "8.8.8.8")

        self.check_connectivity("VM1", vm3_internal_ip)
        self.check_connectivity("VM3", vm1_internal_ip)

        self.check_connectivity("VM1", vm2_floating_ip)
        self.check_connectivity("VM2", vm1_floating_ip)

        self.check_connectivity("VM2", vm3_floating_ip)
        self.check_connectivity("VM3", vm2_floating_ip)

        self.check_connectivity("VM1", vm3_floating_ip)
        self.check_connectivity("VM3 ", vm1_floating_ip)
