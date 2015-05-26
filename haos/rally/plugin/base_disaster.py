# Copyright (c) 2015 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import time

from rally.benchmark.scenarios.neutron import utils as neutron_utils
from rally.benchmark.scenarios.nova import utils as nova_utils
from rally.benchmark.scenarios.vm import utils as vm_utils
from rally.benchmark import types
from rally.common import log as logging
import testtools

from haos.rally import utils

LOG = logging.getLogger(__name__)


class BaseDisaster(neutron_utils.NeutronScenario,
                   nova_utils.NovaScenario,
                   vm_utils.VMScenario,
                   testtools.TestCase):

    def wait_shaker_agent(self, agent_id, timeout=300):
        result = utils.run_command(self.context, agent_id, "hostname",
                                   executor="shaker", timeout=timeout)
        LOG.debug(result)

    def boot_server(self, name, nics=None):
        USER_DATA = """#!/bin/bash
        shaker-agent --agent-id %(agent_id)s \
        --server-endpoint %(server_endpoint)s --debug \
        --log-file /var/log/shaker.log
        """
        shaker_endpoint = self.context['shaker_endpoint']
        userdata = USER_DATA % dict(agent_id=name,
                                    server_endpoint=shaker_endpoint)
        kwargs = {"userdata": userdata}

        if nics is not None:
            kwargs['nics'] = nics

        vm = self._boot_server(name=name,
                               image_id=self.context["shaker_image"],
                               flavor_id=self.context["default_flavor"],
                               auto_assign_nic=True,
                               **kwargs)
        self.wait_shaker_agent(name, timeout=850)

        return vm

    def boot_server_with_agent(self, network_id):
        flavor_id = types.FlavorResourceType.transform(
            clients=self._clients,
            resource_config={'name': self.context["haos_flavor"]})
        image_id = types.ImageResourceType.transform(
            clients=self._clients,
            resource_config={'name': self.context["haos_image"]})
        kwargs = {'nics': [{"net-id": network_id}]}

        server = self._boot_server(image_id=image_id,
                                   flavor_id=flavor_id, auto_assign_nic=True,
                                   **kwargs)

        # extend server instance with helpers
        server.get_agent_id = functools.partial(utils.get_server_agent_id,
                                                server=server)

        # wait for agent to become active
        timeout = time.time() + self.context['haos_join_timeout']
        agent_id = server.get_agent_id()

        active = None
        while not active and time.time() < timeout:
            active = self.run_remote_command(agent_id, 'hostname')

        self.assertIsNotNone(active, 'Server should is expected to be alive')

        LOG.info('Server %s is up and agent is running', server.name)
        return server

    def power_off_controller(self, controller):
        control_node = self.context["power_control_node"]

        utils.run_command(self.context, control_node["agent_endpoint"],
                          command=controller["hardware_power_off_cmd"],
                          recover_command=controller["hardware_power_on_cmd"],
                          recover_timeout=controller["power_on_timeout"])
        time.sleep(controller["power_off_timeout"])

    # This function creates router, network, subnet and joins them
    def create_network_subnet_router(self):
        self._clients = self._admin_clients
        router = self._create_router({}, external_gw=True)
        network, subnets = self._create_network_and_subnets()

        self._add_interface_router(subnets[0]["subnet"], router["router"])
        return network, subnets, router

    # This function associate floating IP for delivered VM
    def associate_floating_ip(self, server=None):
        self._clients = self._admin_clients
        nets = self._list_networks()
        for network in nets:
            if network["router:external"]:
                external_network = network
                self._attach_floating_ip(server, external_network)
                return

    # This function define floating IP for delivered VM and name of network
    def define_floating_ip_for_vm(self, vm, net_name):
        # vm - instance: type(vm) = <class 'novaclient.v2.servers.Server'>
        # net_name - name of network on which we boot vm
        addresses = vm.addresses[net_name]
        for address in addresses:
            if address["OS-EXT-IPS:type"] == 'floating':
                return address["addr"]
        return None

    # This function define internal-fixed IP
    # for delivered VM and name of network
    def define_fixed_ip_for_vm(self, vm, net_name):
        # vm - instance: type(vm) = <class 'novaclient.v2.servers.Server'>
        # net_name - name of network on which we boot vm
        addresses = vm.addresses[net_name]
        for address in addresses:
            if address["OS-EXT-IPS:type"] == 'fixed':
                return address["addr"]
        return None

    # This function from server ping adress_ip
    def check_connectivity(self, server, adress_ip):
        # server - server where we try to ping
        # address_ip - what ping
        command = "ping -c1 %s 1>/dev/null;echo $?" % adress_ip
        output = utils.run_command(self.context, server, command=command,
                                   executor="shaker")
        return output and output[0] == "0"

    # function: get node for l3-agent
    # on what the current router is with neutron API
    def get_node_on_what_is_agent_for_router(self, router):
        # router - router with type NeutronClient
        router_id = router["router"]["id"]
        neutron_client = self.clients("neutron")
        agents = neutron_client.list_l3_agent_hosting_routers(router_id)
        for agent in agents["agents"]:
            return agent['host']
        raise "Router hasn't any l3-agent"

    # Add tcp rule for 22 port and icmp rule
    def add_rules_for_ping(self):
        # self._clients = self._admin_clients
        sec_groups = self._list_security_groups()

        self.clients("nova").security_group_rules.create(
            sec_groups[0].id,
            from_port=22,
            to_port=22,
            ip_protocol="tcp",
            cidr="0.0.0.0/0")

        self.clients("nova").security_group_rules.create(
            sec_groups[0].id,
            from_port=-1,
            to_port=-1,
            ip_protocol="icmp",
            cidr="0.0.0.0/0")

    # Get list agents, only dhcp
    def get_list_dhcp_agents(self):
        list_agents = self.clients("neutron").list_agents()
        list_dhcp_agents = []
        for agent in list_agents["agents"]:
            if agent["agent_type"] == "DHCP agent":
                list_dhcp_agents.append(agent)
        return list_dhcp_agents

    # Get list agents, only l3
    def get_list_l3_agents(self):
        list_agents = self.clients("neutron").list_agents()
        list_l3_agents = []
        for agent in list_agents["agents"]:
            if agent["agent_type"] == "L3 agent":
                list_l3_agents.append(agent)
        return list_l3_agents

    # Get dhcp agent for chosen network on chosen node
    def get_dhcp_on_chosen_node(self, node, net_id):
        """Reschedule net to agent on the chosen node if it doesn't on it yet

        :param node: controller, om which agent reascheduling is needed
        :param net_id: id of network which we should check
        """
        neutron_client = self.clients("neutron")
        dhcp_agents = neutron_client.list_dhcp_agent_hosting_networks(net_id)
        need_manually_rescheduling = True
        for agent in dhcp_agents["agents"]:
            if agent["host"] == node:
                need_manually_rescheduling = False
                break
        if need_manually_rescheduling:
            first_dhcp_agent_id = dhcp_agents["agents"][0]["id"]
            neutron_client.remove_network_from_dhcp_agent(first_dhcp_agent_id,
                                                          net_id)
            list_dhcp_agents = self.get_list_dhcp_agents()
            need_agent = None
            for agent in list_dhcp_agents:
                if agent["host"] == node:
                    need_agent = agent
                    break
            if need_agent:
                agent_id = need_agent['id']
                body = {"network_id": net_id}
                neutron_client.add_network_to_dhcp_agent(dhcp_agent=agent_id,
                                                         body=body)
            else:
                raise

    def get_l3_on_chosen_node(self, node, router_id):
        """Get l3 agent for chosen router on chosen node.

        :param node: controller node on which should be router
        :param router_id: id of chosen router which should be rescheduling
        :return: None
        """
        neutron_client = self.clients("neutron")
        l3_agents = neutron_client.list_l3_agent_hosting_routers(router_id)
        need_manually_rescheduling = True
        for agent in l3_agents["agents"]:
            if agent["host"] == node:
                need_manually_rescheduling = False
                break
        if need_manually_rescheduling:
            first_l3_agent_id = l3_agents["agents"][0]["id"]
            neutron_client.remove_router_from_l3_agent(first_l3_agent_id,
                                                       router_id)
            list_l3_agents = self.get_list_l3_agents()
            need_agent = None
            for agent in list_l3_agents:
                if agent["host"] == node:
                    need_agent = agent
                    break
            if need_agent:
                agent_id = need_agent['id']
                body = {"router_id": router_id}
                neutron_client.add_router_to_l3_agent(l3_agent=agent_id,
                                                      body=body)
            else:
                raise

    def check_reschedule_for_l3_on_node(self, node):
        """Check that routers reschedule from agents on node

        :param node: node controller on which rescheduling is being checked
        """
        list_l3_agents = self.get_list_l3_agents()
        l3_for_node = None
        for l3_agent in list_l3_agents:
            if (l3_agent["host"] == node):
                l3_for_node = l3_agent
        if (l3_for_node is not None):
            list_routers = self.clients(
                "neutron").list_routers_on_l3_agent(l3_for_node["id"])
            if len(list_routers) != 0:
                raise
        else:
            raise

    def check_reschedule_for_dhcp_on_node(self, node):
        """Check that networks and routers reschedule from agents on node

        :param node: node controller on which rescheduling is being checked
        """
        list_dhcp_agents = self.get_list_dhcp_agents()
        dhcp_for_node = None
        for dhcp_agent in list_dhcp_agents:
            if (dhcp_agent["host"] == node):
                dhcp_for_node = dhcp_agent
        if (dhcp_for_node is not None):
            list_networks = self.clients(
                "neutron").list_networks_on_dhcp_agent(dhcp_for_node["id"])
            if len(list_networks) != 0:
                raise
        else:
            raise

    def pick_network_id(self):
        networks = self.context["tenant"].get("networks")
        self.assertTrue(len(networks) >= 1,
                        'At least one network is expected in the tenant')
        return networks[0]['id']

    def kill_remote_process(self, host, process_name):
        LOG.info('Kill process %s at host %s', process_name, host)

        cmd = ("ps aux | grep '%s' | grep -v grep | awk '{print $2}'" %
               process_name)
        pid = self.run_remote_command(host, cmd)
        LOG.debug('process pid: %s', pid)

        self.run_remote_command(host, 'kill -9 %s' % pid)

    def run_remote_command(self, host, command, timeout=None):
        timeout = timeout or self.context.get('haos_command_timeout')
        return self.context.get('haos_remote_control')(host, command, timeout)
