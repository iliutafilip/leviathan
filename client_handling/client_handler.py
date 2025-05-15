import os
import threading
import time
import uuid
from typing import Optional
import paramiko
import re
from paramiko.rsakey import RSAKey
from config_parser.config_parser import load_client_handler_config
from logger.logger import log_event
from emulated_shell.emulated_shell import EmulatedShell

key_path = os.path.expanduser("configs/server.key")
if not os.path.exists(key_path):
    print("[CLIENT HANDLER] Generating new RSA host key...")
    RSAKey.generate(2048).write_private_key_file(key_path)

host_key = RSAKey(filename=key_path)

class ClientHandler(paramiko.ServerInterface):

    def __init__(self, client_ip, client_port, client_version, dst_ip, dst_port, input_username = None, config: Optional[dict] = None):
        self.session_id = str(uuid.uuid4())
        self.client_ip = client_ip
        self.client_port = client_port
        self.client_version = client_version
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.event = threading.Event()
        self.emulated_shell = None
        self.input_username = input_username
        self.password_regex = config["password_regex"]

        log_event(
            event_id="session_start",
            session_id=self.session_id,
            src_ip=self.client_ip,
            src_port=self.client_port,
            dst_ip=self.dst_ip,
            dst_port=self.dst_port,
        )

    def get_session_id(self):
        return self.session_id

    def start_shell(self, channel, config_file: Optional[str] = None):
        if self.input_username is None:
            self.input_username = "unknown"

        self.emulated_shell = EmulatedShell(channel, self.session_id, self.client_ip, self.client_port, username=self.input_username, config_file=config_file)
        self.emulated_shell.start_session()

    def check_channel_request(self, kind: str, channelid: int) -> int:
        if kind == 'session':
            return paramiko.common.OPEN_SUCCEEDED
        return paramiko.common.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        self.input_username = username

        success = bool(re.match(self.password_regex, password))

        print(f"[CLIENT HANDLER] Login attempt: {username}:{password} from {self.client_ip} - {'SUCCESS' if success else 'FAILED'}")

        if success:
            log_event(
                event_id="login_success",
                session_id=self.session_id,
                src_ip=self.client_ip,
                src_port=self.client_port,
                username=username,
                password=password,
            )
            return paramiko.common.AUTH_SUCCESSFUL
        else:
            log_event(
                event_id="login_failed",
                session_id=self.session_id,
                src_ip=self.client_ip,
                src_port=self.client_port,
                username=username,
                password=password,
            )
            return paramiko.common.AUTH_FAILED

    def check_channel_shell_request(self, channel):
        print(f"[CLIENT HANDLER] Shell request from {self.client_ip}:{self.client_port}")
        if self.event:
            self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        print(f"[CLIENT HANDLER] PTY request received from {self.client_ip}:{self.client_port}")
        return True

    def check_channel_exec_request(self, channel, command):
        print(f"[CLIENT HANDLER] Exec request received from {self.client_ip}:{self.client_port}")
        command = command.decode()
        log_event(
            event_id="command_exec",
            session_id=self.session_id,
            src_ip=self.client_ip,
            src_port=self.client_port,
            command=command
        )
        return True


def client_handle(client, addr, config_file: Optional[str] = None):
    client_ip, client_port = addr
    dst_ip, dst_port = client.getsockname()

    config = load_client_handler_config(config_file)

    transport = None

    try:

        transport = paramiko.Transport(client)
        transport.local_version = config["ssh_banner"]
        server = ClientHandler(client_ip, client_port, None, dst_ip, dst_port, config=config)

        transport.add_server_key(host_key)

        transport.start_server(server=server)

        server.client_version = transport.remote_version
        log_event(
            event_id="client_version",
            session_id=server.session_id,
            src_ip=client_ip,
            src_port=client_port,
            message=server.client_version,
        )

        channel = transport.accept(100)

        if channel is None:
            print(f"[CLIENT HANDLER] No channel was opened for {client_ip}.")
            return

        print(f"[CLIENT HANDLER] Session started for {client_ip}:{client_port} with session ID: {server.session_id}")

        while server.input_username is None:
            time.sleep(0.1)

        channel.send(config["standard_banner"].encode())

        time.sleep(1)

        server.start_shell(channel, config_file=config_file)

    except Exception as e:
        print(f"[CLIENT HANDLER ERROR] {e}")
    finally:
        if transport:
            transport.close()
        client.close()
        print(f"[CLIENT HANDLER] Connection closed for {client_ip}:{client_port}.")
