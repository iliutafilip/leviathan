import os
import threading
import time
import uuid
import socket
import paramiko
import re
import yaml
from paramiko.rsakey import RSAKey

from logger.logger import log_event
from emulated_shell.emulated_shell import EmulatedShell

with open("configs/config.yaml", "r") as f:
    config = yaml.safe_load(f)

USERNAME_REGEX = config["authentication"]["username_regex"]
PASSWORD_REGEX = config["authentication"]["password_regex"]

SSH_BANNER = "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"

key_path = os.path.expanduser("configs/server.key")

if not os.path.exists(key_path):
    print("[INFO] Generating new RSA host key...")
    RSAKey.generate(2048).write_private_key_file(key_path)

host_key = RSAKey(filename=key_path)

class ClientHandler(paramiko.ServerInterface):

    def __init__(self, client_ip, client_port, client_version, dst_ip, dst_port, input_username = None,):
        self.session_id = str(uuid.uuid4())
        self.client_ip = client_ip
        self.client_port = client_port
        self.client_version = client_version
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.event = threading.Event()
        self.emulated_shell = None
        self.input_username = input_username

        log_event(
            event_id="session_start",
            session_id=self.session_id,
            src_ip=self.client_ip,
            src_port=self.client_port,
            dst_ip=self.dst_ip,
            dst_port=self.dst_port,
        )

        log_event(
            event_id="client_version",
            session_id=self.session_id,
            src_ip=client_ip,
            src_port=client_port,
        )

    def get_session_id(self):
        return self.session_id

    def start_shell(self, channel):
        if self.input_username is None:
            self.input_username = "unknown"

        self.emulated_shell = EmulatedShell(channel, self.session_id, self.client_ip, self.client_port, username=self.input_username)
        self.emulated_shell.start_session()

    def check_channel_request(self, kind: str, channelid: int) -> int:
        if kind == 'session':
            return paramiko.common.OPEN_SUCCEEDED
        return paramiko.common.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        self.input_username = username

        username_match = re.match(USERNAME_REGEX, username)
        password_match = re.match(PASSWORD_REGEX, password)

        success = bool(username_match and password_match)

        print(f"[-] Login attempt: {username}:{password} from {self.client_ip} - {'SUCCESS' if success else 'FAILED'}")

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
        print(f"[CLIENT HANDLER - DEBUG] Shell request from {self.client_ip}:{self.client_port}")
        if self.event:
            self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        print(f"[CLIENT HANDLER - DEBUG] PTY request received from {self.client_ip}:{self.client_port}")
        return True

    def check_channel_exec_request(self, channel, command):
        print(f"[CLIENT HANDLER - DEBUG] Exec request received from {self.client_ip}:{self.client_port}")
        command = command.decode()
        log_event(
            event_id="command_exec",
            session_id=self.session_id,
            src_ip=self.client_ip,
            src_port=self.client_port,
            command=command
        )
        return True


def client_handle(client, addr):
    client_ip, client_port = addr
    dst_ip, dst_port = client.getsockname()

    transport = None

    try:

        transport = paramiko.Transport(client)
        transport.local_version = SSH_BANNER

        client_version = transport.remote_version

        server = ClientHandler(client_ip, client_port, client_version, dst_ip, dst_port)

        transport.add_server_key(host_key)

        transport.start_server(server=server)

        channel = transport.accept(100)

        if channel is None:
            print(f"[-] No channel was opened for {client_ip}.")
            return

        print(f"[-] Session started for {client_ip}:{client_port} with session ID: {server.session_id}")

        while server.input_username is None:
            time.sleep(0.1)

        standard_banner = b"Welcome to Ubuntu 20.04.5 LTS (GNU/Linux 5.4.0-128-generic x86_64)\r\r\r\n"
        channel.send(standard_banner)

        time.sleep(1)

        server.start_shell(channel)

    except Exception as e:
        print(f"[-] ERROR {e}")
    finally:
        if transport:
            transport.close()
        client.close()
        print(f"[-] Connection closed for {client_ip}:{client_port}.")


def start_server(address, port):
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socks.bind((address, port))

    socks.listen(100)
    print(f"[-] SSH Server listening on {address}:{port}")

    while True:
        try:
            client, address = socks.accept()
            print(f"[-] Incoming SSH connection from {address[0]}:{address[1]}")

            ssh_thread = threading.Thread(target=client_handle, args=(client, address))
            ssh_thread.start()

        except Exception as e:
            print(e)
