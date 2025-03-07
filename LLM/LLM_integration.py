import re
from enum import Enum
from typing import List, Optional
import requests
import yaml


with open("/home/iliut/uni/licenta/configs/plugins-config.yaml") as file:
    config = yaml.safe_load(file)


LLM_PROVIDER = config.get("plugin").get("llmProvider")
LLM_MODEL = config.get("plugin").get("llmModel")
OPENAI_SECRET_KEY = config.get("plugin").get("openAISecretKey")


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"


class Message:
    def __init__(self, role: Role, content: str):
        self.role = role.value
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}


class LLMHoneypot:
    SYSTEM_PROMPT = ("You will act as an Ubuntu Linux terminal. "
                    "The user will type commands, and you are to reply with what the terminal should show. "
                    "Your responses must be contained within a single code block. "
                    "Do not provide note. Do not provide explanations or type commands unless explicitly instructed by the user. "
                    "Your entire response/output is going to consist of a simple text with \n for new line, and you will NOT wrap it within string md markers."
            )

    OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
    OLLAMA_ENDPOINT = "http://localhost:11434/api/chat"

    def __init__(
            self,
            host: Optional[str] = None,
            custom_prompt: Optional[str] = None,
    ):
        self.histories: List[Message] = []
        self.provider = LLMProvider(LLM_PROVIDER.lower())
        self.model = LLM_MODEL
        self.openai_key = OPENAI_SECRET_KEY
        self.host = host or (self.OPENAI_ENDPOINT if self.provider == LLMProvider.OPENAI else self.OLLAMA_ENDPOINT)
        self.custom_prompt = custom_prompt
        self.session = requests.Session()

    def build_prompt(self, command: str) -> List[Message]:
        messages = []
        prompt = self.SYSTEM_PROMPT if not self.custom_prompt else self.custom_prompt

        messages.append(Message(Role.SYSTEM, prompt))
        messages.append(Message(Role.USER, "pwd"))
        messages.append(Message(Role.ASSISTANT, "/home/user"))
        messages.extend(self.histories)
        messages.append(Message(Role.USER, command))

        return messages

    def execute_model(self, command: str) -> str:
        messages = self.build_prompt(command)

        if self.provider == LLMProvider.OPENAI:
            return self._openai_caller(messages)
        elif self.provider == LLMProvider.OLLAMA:
            return self._ollama_caller(messages)
        else:
            raise ValueError("Invalid LLM Provider")

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

    def _ollama_caller(self, messages: List[Message]) -> str:
        payload = {
            "model": self.model,
            "messages": [msg.to_dict() for msg in messages],
            "stream": False,
        }

        response = self.session.post(self.host, json=payload)
        response_data = response.json()

        return self._remove_quotes(response_data["message"]["content"])

    @staticmethod
    def _remove_quotes(content: str) -> str:
        regex = re.compile(r"(```( *)?([a-z]*)?(\n)?)")
        return regex.sub("", content)
