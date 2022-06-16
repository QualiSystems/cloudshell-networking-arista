#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from logging import Logger

from cloudshell.networking.arista.cli.arista_cli_configurator import AristaCLIConfigurator
from cloudshell.networking.arista.command_actions.system_actions import (
    FirmwareActions,
    SystemActions,
)
from cloudshell.shell.flows.firmware.basic_flow import AbstractFirmwareFlow
from cloudshell.shell.flows.utils.url import RemoteURL, BasicLocalUrl
from cloudshell.shell.standards.networking.resource_config import NetworkingResourceConfig


class AristaLoadFirmwareFlow(AbstractFirmwareFlow):
    RUNNING_CONFIG = "running-config"
    STARTUP_CONFIG = "startup-config"
    BOOTFOLDER = ["bootflash:", "bootdisk:"]
    FLASH = "flash:"
    KICKSTART_IMAGE = "kickstart"

    def __init__(
        self,
        logger: Logger,
        resource_config: NetworkingResourceConfig,
        cli_configurator: AristaCLIConfigurator,
    ):
        super().__init__(logger, resource_config)
        self._cli_configurator = cli_configurator

    def _load_firmware_flow(self, firmware_url: RemoteURL | BasicLocalUrl, vrf_management_name: str | None,
                            timeout: int) -> None:
        firmware_file_name = firmware_url.filename
        if not firmware_file_name:
            raise Exception(self.__class__.__name__, "Unable to find firmware file")

        with self._cli_configurator.enable_mode_service() as enable_session:
            system_action = SystemActions(enable_session, self._logger)
            dst_file_system = self.FLASH

            firmware_dst_path = f"{dst_file_system}/{firmware_file_name}"

            device_file_system = system_action.get_flash_folders_list()
            self._logger.info(f"Discovered folders: {device_file_system}")
            if device_file_system:
                device_file_system.sort()
                for flash in device_file_system:
                    if flash in self.BOOTFOLDER:
                        self._logger.info(f"Device has a {flash} folder")
                        firmware_dst_path = f"{flash}/{firmware_file_name}"
                        self._logger.info(f"Copying {firmware_dst_path} image")
                        system_action.copy(
                            str(firmware_url),
                            firmware_dst_path,
                            vrf=vrf_management_name,
                            action_map=system_action.prepare_action_map(
                                firmware_url, BasicLocalUrl.from_str(firmware_dst_path)
                            ),
                        )
                        break
                    if "flash-" in flash:
                        firmware_dst_file_path = f"{flash}/{firmware_file_name}"
                        self._logger.info(f"Copying {firmware_dst_file_path} image")
                        system_action.copy(
                            str(firmware_url),
                            firmware_dst_file_path,
                            vrf=vrf_management_name,
                            action_map=system_action.prepare_action_map(
                                firmware_url, BasicLocalUrl.from_str(firmware_dst_file_path)
                            ),
                        )
            else:
                self._logger.info(f"Copying {firmware_dst_path} image")
                system_action.copy(
                    str(firmware_url),
                    firmware_dst_path,
                    vrf=vrf_management_name,
                    action_map=system_action.prepare_action_map(
                        firmware_url, BasicLocalUrl.from_str(firmware_dst_path)
                    ),
                )

            self._logger.info("Get current boot configuration")
            current_boot = system_action.get_current_boot_image()
            self._logger.info("Modifying boot configuration")
            self._apply_firmware(enable_session, current_boot, firmware_dst_path)

            output = system_action.get_current_boot_config()
            new_boot_settings = re.sub(
                "^.*boot-start-marker|boot-end-marker.*", "", output
            )
            self._logger.info(
                "Boot config lines updated: {0}".format(new_boot_settings)
            )

            if output.find(firmware_file_name) == -1:
                raise Exception(
                    self.__class__.__name__,
                    "Can't add firmware '{}' for boot!".format(firmware_file_name),
                )

            system_action.copy(
                self.RUNNING_CONFIG,
                self.STARTUP_CONFIG,
                vrf=vrf_management_name,
                action_map=system_action.prepare_action_map(
                    BasicLocalUrl.from_str(self.RUNNING_CONFIG), BasicLocalUrl.from_str(self.STARTUP_CONFIG)
                ),
            )
            if "CONSOLE" in enable_session.session.SESSION_TYPE:
                system_action.reload_device_via_console(timeout)
            else:
                system_action.reload_device(timeout)

            os_version = system_action.get_current_os_version()
            if os_version.find(firmware_file_name) == -1:
                raise Exception(
                    self.__class__.__name__,
                    "Failed to load firmware, Please check logs",
                )

    def _apply_firmware(self, enable_session, current_boot, firmware_dst_path):
        firmware_config_to_append = []
        is_kickstart_image = (
            self.KICKSTART_IMAGE in firmware_dst_path.split("/")[-1].lower()
        )

        with enable_session.enter_mode(self._cli_configurator.config_mode) as config_session:
            firmware_action = FirmwareActions(config_session, self._logger)
            for boot_conf in current_boot:
                if is_kickstart_image:
                    if self.KICKSTART_IMAGE in boot_conf.lower():
                        self._logger.info(
                            "Removing '{}' boot config line".format(boot_conf)
                        )
                        firmware_action.clean_boot_config(boot_conf)
                        firmware_config_to_append.append(boot_conf)
                else:
                    self._logger.info(
                        "Removing '{}' boot config line".format(boot_conf)
                    )
                    firmware_action.clean_boot_config(boot_conf)
                    firmware_config_to_append.append(boot_conf)
            self._logger.info("Adding '{}' boot config line".format(firmware_dst_path))
            firmware_action.add_boot_config_file(firmware_dst_path)
            for append_boot in firmware_config_to_append:
                if firmware_dst_path not in append_boot:
                    self._logger.info(
                        "Adding '{}' boot config line".format(append_boot)
                    )
                    firmware_action.add_boot_config(append_boot)
