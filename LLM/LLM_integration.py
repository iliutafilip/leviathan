import re
from enum import Enum
from typing import List, Optional
import requests
import yaml


with open("configs/plugins-config.yaml") as file:
    config = yaml.safe_load(file)


LLM_PROVIDER = config.get("plugin").get("llmProvider")
LLM_MODEL = config.get("plugin").get("llmModel")
OPENAI_SECRET_KEY = config.get("plugin").get("openAISecretKey")


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMProvider(Enum):
    OPENAI = "openai"
    INVALID_PROVIDER = "invalid_provider"

class Message:
    def __init__(self, role: Role, content: str):
        self.role = role.value
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}


class LLMHoneypot:

    @staticmethod
    def _get_system_prompt(username, ssh_server_ip):
        return f"""
            You are an Ubuntu Linux terminal. Respond with the exact command output, using '\r\n' for new lines, WITHOUT EXCEPTIONS.  
            No Markdown, explanations, or extra comments — just the raw terminal output.
            
            Format responses as:  
            `<username>@<ssh_server_ip>:<current_directory>$ `  
            
            - `~` represents "/home/<username>/".  
            - Adjust `<current_directory>` when using `cd`/
            
            Strict Formatting Rules:
            - Use ONLY `\r\n` for new lines—never `\n` alone.
            - NO extra blank lines before or after output.
            - If a command has no output, return only the new prompt.
            - Output results **directly**, without repeating the command.
            
            User: {username}  
            Server: {ssh_server_ip}
        """


    OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"

    def __init__(
            self,
            username: str = "unknown",
            ssh_server_ip: str = "127.0.0.1",
            host: Optional[str] = None,
            custom_prompt: Optional[str] = None,
    ):
        self.provider = LLMProvider(LLM_PROVIDER.lower())
        self.model = LLM_MODEL
        self.openai_key = OPENAI_SECRET_KEY
        self.username = username
        self.ssh_server_ip = ssh_server_ip
        self.host = host or (
            self.OPENAI_ENDPOINT if self.provider == LLMProvider.OPENAI else LLMProvider.INVALID_PROVIDER)
        self.custom_prompt = custom_prompt
        self.session = requests.Session()

        message = Message(Role.SYSTEM, self._get_system_prompt(self.username, self.ssh_server_ip) if not self.custom_prompt else self.custom_prompt)
        self.histories: List[Message] = [message]

        example_interactions = [
            Message(Role.USER, "ls"),
            Message(Role.ASSISTANT, f"Desktop  Documents  Downloads  Music  Pictures  Videos\r\n{self.username}@{self.ssh_server_ip}:~$ "),

            Message(Role.USER, "mkdir a"),
            Message(Role.ASSISTANT, f"\r\n{self.username}@{self.ssh_server_ip}:~$ "),

            Message(Role.USER, "ls"),
            Message(Role.ASSISTANT, f"Desktop  Documents  Downloads  Music  Pictures  Videos a\r\n{self.username}@{self.ssh_server_ip}:~$ "),

            Message(Role.USER, "rmdir a"),
            Message(Role.ASSISTANT, f"\r\n{self.username}@{self.ssh_server_ip}:~$ "),

            Message(Role.USER, "ls"),
            Message(Role.ASSISTANT, f"Desktop  Documents  Downloads  Music  Pictures  Videos\r\n{self.username}@{self.ssh_server_ip}:~$ "),

            Message(Role.USER, "ghdf"),
            Message(Role.ASSISTANT, f"ghdf: command not found\r\n{self.username}@{self.ssh_server_ip}:~$ "),
        ]

        self.histories.extend(example_interactions)

    def build_prompt(self, command: str) -> List[Message]:
        messages = []
        messages.extend(self.histories)
        messages.append(Message(Role.USER, command))

        return messages

    def execute_model(self, command: str) -> str:
        messages = self.build_prompt(command)

        if self.provider == LLMProvider.OPENAI:
            response = self._openai_caller(messages)
        else:
            raise ValueError("Invalid LLM Provider")

        self.histories.append(Message(Role.USER, command))
        self.histories.append(Message(Role.ASSISTANT, response))

        # TODO: save input and output for fine tuning

        return response

    def _openai_caller(self, messages: List[Message]) -> str:
        if not self.openai_key:
            raise ValueError("OpenAI key is required")

        payload = {
            "model": self.model,
            "messages": [msg.to_dict() for msg in messages],
            "stream": False,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_key}",
        }

        response = self.session.post(self.host, json=payload, headers=headers)
        response_data = response.json()

        if "choices" not in response_data or not response_data["choices"]:
            raise ValueError("No choices returned from OpenAI")

        final_response = self._remove_quotes(response_data["choices"][0]["message"]["content"])

        return final_response


    @staticmethod
    def _remove_quotes(content: str) -> str:
        regex = re.compile(r"(```( *)?([a-z]*)?(\n)?)")
        return regex.sub("", content)
