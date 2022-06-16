from __future__ import annotations
from functools import partial
from typing import TYPE_CHECKING

from cloudshell.cli.configurator import AbstractModeConfigurator
from cloudshell.cli.service.cli_service_impl import CliServiceImpl
from cloudshell.cli.service.command_mode_helper import CommandModeHelper

from .arista_command_modes import (
    AristaConfigCommandMode,
    AristaEnableCommandMode,
)
from .sessions.console_ssh_session import ConsoleSSHSession
from .sessions.console_telnet_session import ConsoleTelnetSession, ConsoleTelnetSessionNewLine

if TYPE_CHECKING:
    from cloudshell.api.cloudshell_api import CloudShellAPISession
    from cloudshell.cli.service.cli import CLI
    from cloudshell.shell.standards.networking.resource_config import NetworkingResourceConfig
    from logging import Logger


class AristaCLIConfigurator(AbstractModeConfigurator):

    def __init__(self, resource_config: NetworkingResourceConfig, api: CloudShellAPISession, logger: Logger, cli: CLI):
        super(AristaCLIConfigurator, self).__init__(resource_config=resource_config, logger=logger, cli=cli)
        self._resource_config = resource_config
        self.modes = CommandModeHelper.create_command_mode(resource_config, api)
        self._registered_sessions = (*self._registered_sessions,
                                     ConsoleTelnetSession,
                                     ConsoleTelnetSessionNewLine,
                                     ConsoleSSHSession
                                     )

    @property
    def enable_mode(self) -> AristaEnableCommandMode:
        return self.modes[AristaEnableCommandMode]

    @property
    def config_mode(self) -> AristaConfigCommandMode:
        return self.modes[AristaConfigCommandMode]

    @property
    def _resource_address(self) -> str:
        if self._cli_type.lower() == "console":
            return self._resource_config.console_server_ip_address
        return super()._resource_address

    @property
    def _port(self) -> int:
        if self._cli_type.lower() == "console":
            return int(self._resource_config.console_port)
        return super()._port

    def _on_session_start(self, session, logger) -> None:
        """Send default commands to configure/clear session outputs."""
        cli_service = CliServiceImpl(session, self.enable_mode, logger)
        cli_service.send_command("terminal length 0", AristaEnableCommandMode.PROMPT)
        cli_service.send_command("terminal width 300", AristaEnableCommandMode.PROMPT)
        cli_service.send_command(
            "terminal no exec prompt timestamp", AristaEnableCommandMode.PROMPT
        )
        with cli_service.enter_mode(self.config_mode) as config_session:
            config_session.send_command(
                "no logging console", AristaConfigCommandMode.PROMPT
            )
