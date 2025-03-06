class EmulatedShell:

    def __init__(self, channel, session_id, src_ip, src_port):
        self.session_id = session_id
        self.src_ip = src_ip
        self.src_port = src_port
        self.channel = channel

    def start_session(self):
        self.channel.send(b'~$ ')
        command = b""
        while True:
            char = self.channel.recv(1)
            self.channel.send(char)
            if not char:
                self.channel.close()

            command += char

            response = ''

            if char == b'\r':
                # command handling with LLM
                if command.strip() == b'exit':
                    self.channel.close()

                self.channel.send(response)
                self.channel.send(b'~$ ')
                command = b""