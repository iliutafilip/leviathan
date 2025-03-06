import os
import threading
import uuid
import socket
import paramiko
import re
import yaml

from logger.logger import log_event
from emulated_shell.emulated_shell import EmulatedShell

with open("configs/config.yaml", "r") as f:
    config = yaml.safe_load(f)

USERNAME_REGEX = config["authentication"]["username_regex"]
PASSWORD_REGEX = config["authentication"]["password_regex"]

SSH_BANNER = "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"

key_path = os.path.expanduser("configs/server.key")
host_key = paramiko.RSAKey(filename=key_path, password="leviathan")

class ClientHandler(paramiko.ServerInterface):

    def __init__(self, client_ip, client_port, input_username = None, input_password = None):
        self.session_id = str(uuid.uuid4())
        self.client_ip = client_ip
        self.client_port = client_port
        self.input_username = input_username
        self.input_password = input_password
        self.event = threading.Event()

        log_event(
            event_type="session_start",
            session_id=self.session_id,
            src_ip=self.client_ip,
            src_port=self.client_port
        )

    def get_session_id(self):
        return self.session_id

    def check_channel_request(self, kind: str, channelid: int) -> int:
        if kind == 'session':
            return paramiko.common.OPEN_SUCCEEDED
        return paramiko.common.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        username_match = re.match(USERNAME_REGEX, username)
        password_match = re.match(PASSWORD_REGEX, password)

        success = bool(username_match or password_match)

        log_event(
            event_type="login_attempt",
            session_id=self.session_id,
            src_ip=self.client_ip,
            src_port=self.client_port,
            username=username,
            password=password,
            success=success
        )

        return paramiko.common.AUTH_SUCCESSFUL if success else paramiko.common.AUTH_FAILED


    def check_channel_shell_request(self, channel):
        if self.event:
            self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_exec_request(self, channel, command):
        command = str(command)
        return True


def client_handle(client, addr, username, password):
    client_ip = addr[0]
    client_port = addr[1]
    transport = None

    try:

        transport = paramiko.Transport(client)
        transport.local_version = SSH_BANNER

        server = ClientHandler(client_ip, client_port, username, password)

        transport.add_server_key(host_key)

        transport.start_server(server)

        channel = transport.accept(100)

        if channel is None:
            print("No channel was opened.")

        standard_banner = b"Welcome to Ubuntu 20.04.5 LTS (GNU/Linux 5.4.0-128-generic x86_64)\n* Documentation:  https://help.ubuntu.com\n* Management:     https://landscape.canonical.com\n* Support:        https://ubuntu.com/advantage\r\r\r\n"
        channel.send(standard_banner)
        EmulatedShell(channel,server.get_session_id(), client_ip, client_port)

    except Exception as e:
        print(e)
        print("ERROR")
    finally:
        try:
            if transport is not None:
                transport.close()
        except Exception as e:
            print(e)
            print("ERROR")
        client.close()


def start_server(address, port, username, pasword):
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socks.bind((address, port))

    socks.listen(100)
    print(f"SSH Server listening on {address}:{port}")

    while True:
        try:
            client, address = socks.accept()
            ssh_thread = threading.Thread(target=client_handle, args=(client, address, username, pasword))
            ssh_thread.start()

        except Exception as e:
            print(e)
