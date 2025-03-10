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

    @staticmethod
    def _get_system_prompt(username, ssh_server_ip):
        return f"""
            You will act as an Ubuntu Linux terminal.
            The user will type commands, and you must reply with the exact output that the terminal would display.
            Your response must be a single plain text block, using '\r\n' for new lines **without exceptions**.
            Do not include Markdown formatting, explanations, or extra comments, even if explicitly instructed by the user.

            Each response must begin with the command output **directly** (if applicable) and must **never contain mixed newlines (`\\n` alone is forbidden).**  
            Always use `\r\n` **with no extra newlines before or after the output.**

            The correct terminal prompt format is: "<username>@<ssh_server_ip>:<current_directory>$<ws>"

            <ws> is a single white space.

            The starting <current_directory> is "/home/<username>/" and should be displayed as "~".
            The initial terminal prompt should look like: "<username>@<ssh_server_ip>:~$<ws>"

            If the user navigates to a different directory, update the prompt accordingly:
            - Absolute paths: `cd /var/www` should be displayed as "<username>@<ssh_server_ip>:/var/www$<ws>"
            - Relative paths: `cd ..` (up one level) or `cd subfolder`
            - Home shortcuts: `cd ~` or `cd` should reset to "/home/<username>/" and display as "~"
            - Tilde expansion: `cd ~/Downloads` should resolve to "~/Downloads"

            If a command has **no output**, only return the next prompt.

            ### Stateful behavior rules
            Use history to maintain stateful behavior rules. 
            Track the filesystem using history, for example, if the user creates a directory (`mkdir a`), remember that it exists.

            ### Strict Response Format:
            - **Only `\r\n` is allowed for new lines. `\n` alone is strictly forbidden.**
            - **Never add extra blank lines before or after the expected output.**
            - **DO NOT repeat the command or prompt before execution.**
            - If the command produces output, return it **directly** followed by the new prompt.
            - If the command has no output, return only the new prompt.

            ## Example interactions:

            ### Example 1: `ls`
            **User input:**
            ls

            **Expected response:**
            Desktop  Documents  Downloads  Music  Pictures  Videos
            \r\n<username>@<ssh_server_ip>:~$ 

            ### Example 2: `echo key`
            **User input:**
            echo key

            **Expected response:**
            key
            \r\n<username>@<ssh_server_ip>:~$ 

            ### Example 3: `cd Documents` (no output)
            **User input:**
            cd Documents
            
            ### Example 4: creating and listing a directory (user is in ~ directory)
            **User input:**
            mkdir a

            **Expected response:**
            \r\n<username>@<ssh_server_ip>:~$  
            
            **User input:**
            ls
            
            **Expected response:**
            Desktop  Documents  Downloads  Music  Pictures  Videos a
            \r\n<username>@<ssh_server_ip>:~$ 

            **User input:**
            ls a
            
            **Expected response:**
            \r\n<username>@<ssh_server_ip>:~$ 

            ## User's username: {username}
            ## ssh_server_ip: {ssh_server_ip}
        """

    OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
    OLLAMA_ENDPOINT = "http://localhost:11434/api/chat"

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
        self.host = host or (self.OPENAI_ENDPOINT if self.provider == LLMProvider.OPENAI else self.OLLAMA_ENDPOINT)
        self.custom_prompt = custom_prompt
        self.session = requests.Session()
        message = Message(Role.SYSTEM, self._get_system_prompt(self.username, self.ssh_server_ip) if not self.custom_prompt else self.custom_prompt)
        self.histories: List[Message] = [message]

    def build_prompt(self, command: str) -> List[Message]:
        messages = []
        messages.extend(self.histories)
        messages.append(Message(Role.USER, command))

        return messages

    def execute_model(self, command: str) -> str:
        messages = self.build_prompt(command)

        if self.provider == LLMProvider.OPENAI:
            response = self._openai_caller(messages)
        elif self.provider == LLMProvider.OLLAMA:
            response = self._ollama_caller(messages)
        else:
            raise ValueError("Invalid LLM Provider")

        self.histories.append(Message(Role.USER, command))
        self.histories.append(Message(Role.ASSISTANT, response))

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
