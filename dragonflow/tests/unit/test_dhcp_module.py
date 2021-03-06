# Copyright (c) 2017 Huawei Tech. Co., Ltd. .
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from neutron.plugins.ml2.plugin import Ml2Plugin
from neutron_lib import constants as n_const

from dragonflow.neutron.ml2.dhcp_module import DFDHCPModule
from dragonflow.tests.unit import test_mech_driver as test_md


class TestDfDHCPModule(test_md.DFMechanismDriverTestCase):

    def setUp(self):
        super(TestDfDHCPModule, self).setUp()

    @mock.patch.object(DFDHCPModule, '_create_dhcp_port')
    def test_create_subnet_with_dhcp(self, create_mock):
        network, _ = self._test_create_network_revision()
        with self.subnet(network={'network': network}, enable_dhcp=True,
                         set_context=True):
            create_mock.assert_called_once()

    @mock.patch.object(DFDHCPModule, '_create_dhcp_port')
    def test_ipv6_not_supported(self, create_mock):
        network, _ = self._test_create_network_revision()
        with self.subnet(network={'network': network},
                         enable_dhcp=True,
                         set_context=True,
                         cidr="10::/64",
                         ip_version=6):
            create_mock.assert_not_called()

    @mock.patch.object(DFDHCPModule, '_update_dhcp_port')
    def test_subnets_on_same_network(self, update_mock):
        network, _ = self._test_create_network_revision()
        with self.subnet(network={'network': network},
                         enable_dhcp=True,
                         set_context=True), self.subnet(
            network={'network': network},
            enable_dhcp=True,
            set_context=True,
            cidr="10.1.0.0/24"
        ):
            update_mock.assert_called_once()

    @mock.patch.object(DFDHCPModule, '_update_dhcp_port')
    def test_subnets_on_diffrent_switch(self, update_mock):
        network, _ = self._test_create_network_revision()
        network2, _ = self._test_create_network_revision(name='net2')
        with self.subnet(network={'network': network},
                         enable_dhcp=True,
                         set_context=True), self.subnet(
            network={'network': network2},
            enable_dhcp=True,
            set_context=True,
            cidr="10.1.0.0/24"
        ):
            update_mock.assert_not_called()

    @mock.patch.object(Ml2Plugin, 'delete_port')
    def test_subnets_update_when_its_need(self, delete_mock):
        network, _ = self._test_create_network_revision()
        with self.subnet(network={'network': network},
                         enable_dhcp=True,
                         set_context=True) as subnet1, self.subnet(
             network={'network': network},
             enable_dhcp=True,
             set_context=True,
             cidr="10.1.0.0/24"
        ) as subnet2:
            data = {'subnet': {'enable_dhcp': False}}
            req = self.new_update_request('subnets',
                                          data, subnet1['subnet']['id'])
            req.get_response(self.api)

            delete_mock.assert_not_called()
            data = {'subnet': {'enable_dhcp': False}}
            req = self.new_update_request('subnets',
                                          data, subnet2['subnet']['id'])
            req.get_response(self.api)
            delete_mock.assert_called_once()

    def test_dhcp_port_status(self):
        network, _ = self._test_create_network_revision()
        with self.subnet(network={'network': network}, enable_dhcp=True,
                         set_context=True):
            filters = {'device_owner': [n_const.DEVICE_OWNER_DHCP],
                       'network': [network]}
            ports = self.driver.get_ports(self.context, filters=filters)
            port = ports[0]
            self.assertEqual(n_const.PORT_STATUS_ACTIVE, port['status'])
