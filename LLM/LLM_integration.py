import os
import re
from enum import Enum
from typing import List, Optional
import requests
import yaml

from store.user_history_store import UserHistoryStore

with open("configs/plugins-config.yaml") as file:
    config = yaml.safe_load(file)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", config.get("plugin", {}).get("llmProvider", "openai")).lower()
LLM_MODEL = os.getenv("LLM_MODEL", config.get("plugin", {}).get("llmModel", "gpt-4"))
API_SECRET_KEY = os.getenv("OPEN_AI_SECRET_KEY", config.get("plugin", {}).get("openAISecretKey"))


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMProvider(Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
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
            NO Markdown, explanations, or extra comments — just the raw terminal output.

            Format responses as:  
            `<username>@<ssh_server_ip>:<current_directory>$ `  

            - `~` represents "/home/<username>/".  
            - Adjust `<current_directory>` when using `cd`

            Strict Formatting Rules:
            - Use ONLY `\r\n` for new lines—never `\n` alone.
            - NO extra blank lines before or after output.
            - If a command has no output, return ONLY the new prompt.

            User: {username}  
            Server: {ssh_server_ip}
        """

    OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
    DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"


    def __init__(
            self,
            username: str = "unknown",
            ssh_server_ip: str = "127.0.0.1",
            custom_prompt: Optional[str] = None,
    ):
        self.provider = LLMProvider(LLM_PROVIDER.lower())
        self.model = LLM_MODEL
        self.api_key = API_SECRET_KEY
        self.username = username
        self.ssh_server_ip = ssh_server_ip
        self.custom_prompt = custom_prompt
        self.session = requests.Session()

        self.api_endpoint = self.OPENAI_ENDPOINT if self.provider == LLMProvider.OPENAI else self.DEEPSEEK_ENDPOINT

        self.histories: List[Message] = self._load_user_history()

        if not self.histories:
            system_message = Message(Role.SYSTEM, self._get_system_prompt(username, ssh_server_ip))
            self.histories.append(system_message)

            example_interactions = [
                Message(Role.USER, "ls"),
                Message(Role.ASSISTANT,
                        f"Desktop  Documents  Downloads  Music  Pictures  Videos\r\n{self.username}@{self.ssh_server_ip}:~$ "),
            ]
            self.histories.extend(example_interactions)

            self._save_user_history()

    def _load_user_history(self) -> List[Message]:
        history = UserHistoryStore.load_user_history(self.username)

        if history:
            return [
                Message(Role(entry["role"]), entry["content"]) for entry in history
            ]

        return []

    def _save_user_history(self):
        history_data = [
            {"role": msg.role, "content": msg.content} for msg in self.histories
        ]
        UserHistoryStore.save_user_history(self.username, history_data)

    def _add_to_user_history(self, user_msg: Message, assistant_msg: Message):
        data = [
            {"role": user_msg.role, "content": user_msg.content},
            {"role": assistant_msg.role, "content": assistant_msg.content},
        ]
        UserHistoryStore.save_user_history(self.username, data)


    def build_prompt(self, command: str) -> List[Message]:
        messages = []
        messages.extend(self.histories)
        messages.append(Message(Role.USER, command))
        return messages

    def execute_model(self, command: str) -> str:
        messages = self.build_prompt(command)

        if self.provider == LLMProvider.OPENAI or self.provider == LLMProvider.DEEPSEEK:
            response = self._api_caller(messages)
        else:
            raise ValueError("Invalid LLM Provider")

        user_msg = Message(Role.USER, command)
        assistant_msg = Message(Role.ASSISTANT, response)

        self.histories.append(user_msg)
        self.histories.append(assistant_msg)

        self._add_to_user_history(user_msg, assistant_msg)

        return response

    def _api_caller(self, messages: List[Message]):
        if not self.api_key:
            raise ValueError("API key is required")

        payload, headers = self._create_payload(messages)

        response = self.session.post(self.api_endpoint, json=payload, headers=headers)
        response_data = response.json()

        if "choices" not in response_data or not response_data["choices"]:
            raise ValueError("No choices returned from LLM provider")

        final_response = self._remove_quotes(response_data["choices"][0]["message"]["content"])
        return final_response


    def _create_payload(self, messages: List[Message]):
        payload = {
            "model": self.model,
            "messages": [msg.to_dict() for msg in messages],
            "stream": False,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        return payload, headers


    @staticmethod
    def _remove_quotes(content: str) -> str:
        regex = re.compile(r"(```( *)?([a-z]*)?(\n)?)")
        return regex.sub("", content)
