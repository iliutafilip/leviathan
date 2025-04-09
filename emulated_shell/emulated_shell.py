from LLM.LLM_integration import LLMHoneypot
from logger.logger import log_event
import socket


class EmulatedShell:

    def __init__(self, channel, session_id, src_ip, src_port, username):
        print(f"[SHELL] Emulated shell initialized")
        self.session_id = session_id
        self.src_ip = src_ip
        self.src_port = src_port
        self.channel = channel
        self.username = username
        self.llm_honeypot = LLMHoneypot(username, socket.gethostbyname(socket.gethostname()))


    def start_session(self):
        ssh_server_ip = socket.gethostbyname(socket.gethostname())
        prompt = f"{self.username}@{ssh_server_ip}:~$ ".encode()
        self.channel.send(prompt)
        command = b""

        while True:
            char = self.channel.recv(1)

            if not char:
                print(f"[SHELL - DEBUG] Client with {self.src_ip}:{self.src_port} disconnected")
                self.channel.send(b'\nConnection lost...\n')
                log_event(
                    event_id="session_disconnect",
                    session_id=self.session_id,
                    src_ip=self.src_ip,
                    src_port=self.src_port
                )
                break

            if char == b'\x1b':
                seq = self.channel.recv(2)
                if seq in [b'[A', b'[B', b'[C', b'[D']:
                    continue

            if char < b' ' and char not in [b'\r', b'\x7f']:
                continue

            if char == b'\x7f':
                if command:
                    command = command[:-1]
                    self.channel.send(b"\b \b")
                continue

            self.channel.send(char)
            command += char

            if char == b'\r':
                self.channel.send(b'\n')

                cmd_str = command.strip().decode('utf-8')
                print(f"[DEBUG - SHELL] Received command: {cmd_str} from {self.src_ip}")

                log_event(
                    event_id="command_input",
                    session_id=self.session_id,
                    src_ip=self.src_ip,
                    src_port=self.src_port,
                    username=self.username,
                    command=cmd_str
                )

                if cmd_str.lower() == "exit":
                    try:
                        self.llm_honeypot.execute_model(cmd_str)
                    except Exception as e:
                        self.channel.send(f"Error processing command: {str(e)}\n".encode())
                    break

                # LLM INTEGRATION
                try:
                    response = self.llm_honeypot.execute_model(cmd_str)
                    self.channel.send(response.encode())
                except Exception as e:
                    self.channel.send(f"Error processing command: {str(e)}\n".encode())

                command = b""

        self.channel.close()
        log_event(
            event_id="session_terminated",
            session_id=self.session_id,
            src_ip=self.src_ip,
            src_port=self.src_port
        )