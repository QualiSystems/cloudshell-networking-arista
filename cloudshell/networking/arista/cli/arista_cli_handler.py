from cloudshell.cli.cli_service_impl import CliServiceImpl
from cloudshell.cli.command_mode_helper import CommandModeHelper
from cloudshell.cli.session.ssh_session import SSHSession
from cloudshell.cli.session.telnet_session import TelnetSession
from cloudshell.devices.cli_handler_impl import CliHandlerImpl

from cloudshell.networking.arista.cli.arista_command_modes import AristaDefaultCommandMode, \
    AristaEnableCommandMode, AristaConfigCommandMode
from cloudshell.networking.arista.sessions.console_ssh_session import ConsoleSSHSession
from cloudshell.networking.arista.sessions.console_telnet_session import ConsoleTelnetSession


class AristaCliHandler(CliHandlerImpl):
    def __init__(self, cli, resource_config, logger, api):
        super(AristaCliHandler, self).__init__(cli, resource_config, logger, api)
        self.modes = CommandModeHelper.create_command_mode(resource_config, api)

    @property
    def default_mode(self):
        return self.modes[AristaDefaultCommandMode]

    @property
    def enable_mode(self):
        return self.modes[AristaEnableCommandMode]

    @property
    def config_mode(self):
        return self.modes[AristaConfigCommandMode]

    def _console_ssh_session(self):
        console_port = int(self.resource_config.console_port)
        session = ConsoleSSHSession(self.resource_config.console_server_ip_address,
                                    self.username,
                                    self.password,
                                    console_port,
                                    self.on_session_start)
        return session

    def _console_telnet_session(self):
        console_port = int(self.resource_config.console_port)
        return [ConsoleTelnetSession(self.resource_config.console_server_ip_address,
                                     self.username,
                                     self.password,
                                     console_port,
                                     self.on_session_start),
                ConsoleTelnetSession(self.resource_config.console_server_ip_address,
                                     self.username,
                                     self.password,
                                     console_port,
                                     self.on_session_start,
                                     start_with_new_line=True)
                ]

    def _new_sessions(self):
        if self.cli_type.lower() == SSHSession.SESSION_TYPE.lower():
            new_sessions = self._ssh_session()
        elif self.cli_type.lower() == TelnetSession.SESSION_TYPE.lower():
            new_sessions = self._telnet_session()
        elif self.cli_type.lower() == "console":
            new_sessions = list()
            new_sessions.append(self._console_ssh_session())
            new_sessions.extend(self._console_telnet_session())
        else:
            new_sessions = [self._ssh_session(), self._telnet_session(),
                            self._console_ssh_session()]
            new_sessions.extend(self._console_telnet_session())
        return new_sessions

    def on_session_start(self, session, logger):
        """Send default commands to configure/clear session outputs
        :return:
        """
        cli_service = CliServiceImpl(session, self.enable_mode, logger)
        cli_service.send_command("terminal length 0", AristaEnableCommandMode.PROMPT)
        cli_service.send_command("terminal width 300", AristaEnableCommandMode.PROMPT)
        cli_service.send_command("terminal no exec prompt timestamp", AristaEnableCommandMode.PROMPT)
        with cli_service.enter_mode(self.config_mode) as config_session:
            config_session.send_command("no logging console", AristaConfigCommandMode.PROMPT)
