from unittest import TestCase

from mock import MagicMock, patch

from cloudshell.networking.arista.flows.arista_add_vlan_flow import AristaAddVlanFlow


class TestAristaAddVlanFlow(TestCase):
    def setUp(self):
        self._handler = AristaAddVlanFlow(MagicMock(), MagicMock())

    @patch("cloudshell.networking.arista.flows.arista_add_vlan_flow.AddRemoveVlanActions")
    @patch("cloudshell.networking.arista.flows.arista_add_vlan_flow.IFaceActions")
    def test_execute_flow(self, iface_mock, vlan_actions_mock):
        port_mode = "trunk"
        port_name = "Ethernet4-5"
        converted_port_name = "Ethernet4/5"
        vlan_id = "45"
        qnq = False
        c_tag = ""
        iface_mock.return_value.get_port_name.return_value = converted_port_name

        self._handler.execute_flow(vlan_id, port_mode, port_name, qnq, c_tag)

        iface_obj_mock = iface_mock.return_value
        vlan_obj_mock = vlan_actions_mock.return_value

        iface_obj_mock.get_port_name.assert_called_once_with(port_name)
        vlan_obj_mock.create_vlan.assert_called_once_with(vlan_id)

        iface_obj_mock.get_current_interface_config.assert_called_with(converted_port_name)
        curr_conf_mock = iface_obj_mock.get_current_interface_config.return_value

        iface_obj_mock.enter_iface_config_mode.assert_called_once_with(converted_port_name)
        iface_obj_mock.clean_interface_switchport_config.assert_called_once_with(curr_conf_mock)
        vlan_obj_mock.set_vlan_to_interface.assert_called_once_with(
            vlan_id, port_mode, converted_port_name, qnq, c_tag)

        self.assertEqual(iface_obj_mock.get_current_interface_config.call_count, 2)

        vlan_obj_mock.verify_interface_configured.assert_called_once_with(
            vlan_id, curr_conf_mock)

    @patch("cloudshell.networking.arista.flows.arista_add_vlan_flow.AddRemoveVlanActions")
    @patch("cloudshell.networking.arista.flows.arista_add_vlan_flow.IFaceActions")
    def test_raise_exception_if_vlan_not_added(self, iface_mock, vlan_actions_mock):
        port_mode = "trunk"
        port_name = "Ethernet4-5"
        converted_port_name = "Ethernet4/5"
        vlan_id = "45"
        qnq = False
        c_tag = ""
        iface_mock.return_value.get_port_name.return_value = converted_port_name
        vlan_actions_mock.return_value.verify_interface_configured.return_value = False

        self.assertRaises(
            Exception,
            self._handler.execute_flow,
            vlan_id, port_mode, port_name, qnq, c_tag)

        iface_obj_mock = iface_mock.return_value
        vlan_obj_mock = vlan_actions_mock.return_value

        iface_obj_mock.get_port_name.assert_called_once_with(port_name)
        vlan_obj_mock.create_vlan.assert_called_once_with(vlan_id)

        iface_obj_mock.get_current_interface_config.assert_called_with(converted_port_name)
        curr_conf_mock = iface_obj_mock.get_current_interface_config.return_value

        iface_obj_mock.enter_iface_config_mode.assert_called_once_with(converted_port_name)
        iface_obj_mock.clean_interface_switchport_config.assert_called_once_with(curr_conf_mock)
        vlan_obj_mock.set_vlan_to_interface.assert_called_once_with(
            vlan_id, port_mode, converted_port_name, qnq, c_tag)

        self.assertEqual(iface_obj_mock.get_current_interface_config.call_count, 2)

        vlan_obj_mock.verify_interface_configured.assert_called_once_with(
            vlan_id, curr_conf_mock)
