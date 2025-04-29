import os
import re
from enum import Enum
from typing import List, Optional
import requests
import yaml
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from store.user_history_store import UserHistoryStore

with open("configs/config.yaml") as file:
    config = yaml.safe_load(file)

llm_config = config.get("llm_config", {})

LLM_PROVIDER = os.getenv("LLM_PROVIDER", llm_config.get("llmProvider", "openai")).lower()
LLM_MODEL = os.getenv("LLM_MODEL", llm_config.get("llmModel", "gpt-4o-mini"))
API_SECRET_KEY = os.getenv("API_SECRET_KEY", llm_config.get("apiSecretKey"))


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMProvider(Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GROK = "grok"
    INVALID_PROVIDER = "invalid_provider"


class Message:
    def __init__(self, role: Role, content: str):
        self.role = role.value
        self.content = content

    def to_dict(self) -> ChatCompletionMessageParam:
        return {"role": self.role, "content": self.content}


class LLMHoneypot:

    @staticmethod
    def _get_system_prompt(username, ssh_server_ip):
        return f"""
            You are an Ubuntu Linux terminal. Respond with the exact command output, using STRICTLY '\r\n' for new lines instead of '\n'. NO Markdown, explanations, or extra comments. Format responses as:`<command_output>\r\n<username>@<ssh_server_ip>:<current_directory>$ `  
            User: {username}  
            Server: {ssh_server_ip}
        """

    OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
    DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
    GROK_ENDPOINT = "https://api.x.ai/v1"

    def __init__(
            self,
            username: str = "unknown",
            ssh_server_ip: str = "127.0.0.1",
            custom_prompt: Optional[str] = None,
            provider = None,
            model = None,
            api_key = None,
            history_store = None,
    ):
        self.provider = LLMProvider(LLM_PROVIDER.lower()) if provider is None else LLMProvider(provider.lower())
        self.model = model or LLM_MODEL
        self.api_key = api_key or API_SECRET_KEY
        self.username = username
        self.ssh_server_ip = ssh_server_ip
        self.custom_prompt = custom_prompt
        self.session = requests.Session()

        if self.provider == LLMProvider.OPENAI:
            self.api_endpoint = self.OPENAI_ENDPOINT
        elif self.provider == LLMProvider.DEEPSEEK:
            self.api_endpoint = self.DEEPSEEK_ENDPOINT
        elif self.provider == LLMProvider.GROK:
            self.api_endpoint = self.GROK_ENDPOINT

        if self.provider in [LLMProvider.OPENAI, LLMProvider.GROK]:
            self.llm_client = OpenAI(
                api_key=self.api_key,
                base_url=self.GROK_ENDPOINT if self.provider == LLMProvider.GROK else None,
            )

        self.history_store = history_store or UserHistoryStore()
        self.histories: List[Message] = self._load_user_history()
        self.sys_prompt = Message(Role.SYSTEM, self._get_system_prompt(username, ssh_server_ip) if self.custom_prompt is None else self.custom_prompt)

        if not self.histories:
            self.histories.append(self.sys_prompt)

            example_interactions = [
                Message(Role.USER, "ls"),
                Message(Role.ASSISTANT,
                        f"Desktop  Documents  Downloads  Music  Pictures  Public  Templates  Videos\r\n{self.username}@{self.ssh_server_ip}:~$ "),
            ]
            self.histories.extend(example_interactions)

            self._save_user_history()

        start_up = [
            Message(Role.SYSTEM, self._get_system_prompt(username, ssh_server_ip)),
            Message(Role.USER, "cd"),
            Message(Role.ASSISTANT, f"\r\n{self.username}@{self.ssh_server_ip}:~$ "),
        ]

        self.histories.extend(start_up)

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
        messages.append(self.sys_prompt)
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
        if self.api_key is None:
            raise ValueError("API key is required")

        if self.provider in [LLMProvider.OPENAI, LLMProvider.GROK]:
            chat_messages: List[ChatCompletionMessageParam] = [msg.to_dict() for msg in messages]
            completion = self.llm_client.chat.completions.create(
                model=self.model,
                messages=chat_messages,
            )
            content = completion.choices[0].message.content
        elif self.provider == LLMProvider.DEEPSEEK:
            payload, headers = self._create_payload(messages)
            response = self.session.post(self.api_endpoint, json=payload, headers=headers)
            response_data = response.json()

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
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        return payload, headers


    @staticmethod
    def _clean_content(content: str) -> str:
        regex = re.compile(r"(```( *)?([a-z]*)?(\n)?)")
        return re.sub(regex, "", content).lstrip("\r\n")
