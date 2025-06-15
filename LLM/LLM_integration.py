import re
from enum import Enum
from typing import List, Optional
import requests

from config_parser.config_parser import load_llm_config
from store.user_history_store import UserHistoryStore


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMProvider(Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GROK = "grok"
    OLLAMA = "ollama"
    INVALID_PROVIDER = "invalid_provider"


class Message:
    def __init__(self, role: Role, content: str):
        self.role = role.value
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}


class LLMHoneypot:

    OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
    DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
    GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"
    OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

    def __init__(
            self,
            username: str = "unknown",
            ssh_server_ip: str = "127.0.0.1",
            config = None,
            history_store = None,
    ):

        llm_config = load_llm_config(config)
        self.provider = LLMProvider(llm_config["llm_provider"])
        self.model = llm_config["llm_model"]
        self.api_key = llm_config["api_key"]
        self.sys_prompt_text = llm_config["system_prompt"]

        self.username = username
        self.ssh_server_ip = ssh_server_ip
        self.session = requests.Session()

        if self.provider == LLMProvider.OPENAI:
            self.api_endpoint = self.OPENAI_ENDPOINT
        elif self.provider == LLMProvider.DEEPSEEK:
            self.api_endpoint = self.DEEPSEEK_ENDPOINT
        elif self.provider == LLMProvider.GROK:
            self.api_endpoint = self.GROK_ENDPOINT
        elif self.provider == LLMProvider.OLLAMA:
            self.api_endpoint = self.OLLAMA_ENDPOINT

        self.history_store = history_store or UserHistoryStore()
        self.histories: List[Message] = self._load_user_history()
        self.sys_prompt_message = Message(Role.SYSTEM, self._get_system_prompt())

        if not self.histories:
            self.histories.append(self.sys_prompt_message)

            example_interactions = [
                Message(Role.USER, "ls"),
                Message(Role.ASSISTANT,
                        f"Desktop  Documents  Downloads  Music  Pictures  Public  Templates  Videos\r\n{self.username}@{self.ssh_server_ip}:~$ "),
            ]
            self.histories.extend(example_interactions)

            self._save_user_history()

        start_up = [
            self.sys_prompt_message,
            Message(Role.USER, "cd"),
            Message(Role.ASSISTANT, f"\r\n{self.username}@{self.ssh_server_ip}:~$ "),
        ]

        self.histories.extend(start_up)


    def _get_system_prompt(self):
        return self.sys_prompt_text + f" User: {self.username} Server: {self.ssh_server_ip}"

    def _load_user_history(self) -> List[Message]:
        history_data = self.history_store.load_user_history(self.username)
        return [Message(Role(entry["role"]), entry["message"]) for entry in history_data]

    def _save_user_history(self):
        data = [{"role": msg.role, "message": msg.content} for msg in self.histories]
        self.history_store.add_to_user_history(self.username, data)

    def _add_to_user_history(self, user_msg: Message, assistant_msg: Message):
        self.history_store.add_to_user_history(self.username, [
            {"role": user_msg.role, "message": user_msg.content},
            {"role": assistant_msg.role, "message": assistant_msg.content},
        ])

    def build_prompt(self, command: str) -> List[Message]:
        messages = []
        messages.extend(self.histories)
        messages.append(self.sys_prompt_message)
        messages.append(Message(Role.USER, command))
        return messages

    def execute_model(self, command: str) -> str:
        messages = self.build_prompt(command)

        response = self._api_caller(messages)

        user_msg = Message(Role.USER, command)
        assistant_msg = Message(Role.ASSISTANT, response)

        self.histories.append(user_msg)
        self.histories.append(assistant_msg)

        self._add_to_user_history(user_msg, assistant_msg)

        return response

    def _api_caller(self, messages: List[Message]):
        if self.provider != LLMProvider.OLLAMA:
            if self.api_key is None:
                raise ValueError("API key is required")

        if self.provider in [LLMProvider.OPENAI, LLMProvider.DEEPSEEK, LLMProvider.GROK, LLMProvider.OLLAMA]:
            payload, headers = self._create_payload(messages)
            response = self.session.post(self.api_endpoint, json=payload, headers=headers)
            response_data = response.json()

            if self.provider == LLMProvider.OLLAMA:
                content = response_data.get("message", {}).get("content", "")
            else:
                if "choices" not in response_data or not response_data["choices"]:
                    raise ValueError("No choices returned from LLM provider")

                content = response_data["choices"][0]["message"]["content"]
        else:
            raise ValueError("Unsupported provider in _api_caller")

        return self._clean_content(content)


    def _create_payload(self, messages: List[Message]):
        payload = {
            "model": self.model,
            "messages": [msg.to_dict() for msg in messages],
            "stream": False,
        }

        headers = {
            "Content-Type": "application/json"
        }

        if self.provider in [LLMProvider.OPENAI, LLMProvider.DEEPSEEK, LLMProvider.GROK]:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return payload, headers


    @staticmethod
    def _clean_content(content: str) -> str:
        regex = re.compile(r"(```( *)?([a-z]*)?(\n)?)")
        return re.sub(regex, "", content).lstrip("\r\n")
