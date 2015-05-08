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

import random
import re

from rally.benchmark.scenarios import base
from rally.benchmark import validation
from rally.common import log as logging
from rally import consts

from haos.rally.plugin import base_disaster

LOG = logging.getLogger(__name__)


OBTAIN_IP = 'sudo /sbin/udhcpc -n 2>/dev/null | grep obtained'


class NeutronDHCPDisaster(base_disaster.BaseDisaster):

    def _obtain_ip_address(self, server):
        server_agent_id = server.get_agent_id()
        LOG.debug('Server agent id: %s', server_agent_id)

        obtain_out = self.run_remote_command(server_agent_id, OBTAIN_IP)
        if obtain_out:
            ip = re.findall('\d+\.\d+\.\d+\.\d+', obtain_out)[0]
            LOG.info('Server IP is obtained: %s', ip)
            return ip

    @validation.required_services(consts.Service.NOVA, consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @base.scenario(context={'cleanup': ['nova'],
                            'keypair': {}, 'allow_ssh': {}})
    def kill_dhcp_agent(self, **kwargs):

        network_id = self.pick_network_id()
        server = self.boot_server_with_agent(network_id)

        # obtain IP address
        ip1 = self._obtain_ip_address(server)
        self.assertIsNotNone(
            ip1, 'Instance should be able to obtain IP from DHCP')

        # choose controller
        agents = self.admin_clients(
            'neutron').list_dhcp_agent_hosting_networks(network_id)['agents']
        controller = random.choice(agents)['host']

        # kill dhcp agent
        self.kill_remote_process(controller, 'dhcp-agent')

        # retrieve IP once again
        ip2 = self._obtain_ip_address(server)
        self.assertIsNotNone(
            ip2, 'Instance should be able to obtain IP from DHCP')

        self.assertEqual(ip1, ip2, 'DHCP should return the same IP')
