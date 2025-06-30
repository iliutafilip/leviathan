import os
import yaml
from cerberus import Validator

LLM_DEFAULT_SYS_PROMPT = (
    "You are an Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-1027-generic x86_64) Linux terminal. Respond with the exact command output, using STRICTLY '\r\n' for new lines instead of '\n'. NO Markdown, explanations, or extra comments. Format responses as:`<command_output>\r\n<username>@<ssh_server_ip>:<current_directory>$ ` Always end the user prompt with a white space after `$`.")

DEFAULT_STANDARD_BANNER = (
    "Welcome to Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-1027-generic x86_64)\r\n* Documentation:  https://help.ubuntu.com\r\n* Management:     https://landscape.canonical.com\r\n* Support:        https://ubuntu.com/pro\r\n"
)

DEFAULT_SSH_BANNER = (
    "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"
)

DEFAULT_PASSWORD_REGEX = (
    "^(123456|root)$"
)

schema = {
    "client_handler_config": {
        "type": "dict",
        "required": True,
        "schema": {
            "ssh_banner": {"type": "string", "required": False, "nullable": True},
            "standard_banner": {"type": "string", "required": False, "nullable": True},
            "authentication": {
                "type": "dict",
                "required": True,
                "schema": {
                    "password_regex": {"type": "string", "required": False},
                },
            },
            },
    },
    "llm_config": {
        "type": "dict",
        "required": True,
        "schema": {
            "llmCustomSysPrompt": {"type": "string", "required": False, "nullable": True},
            "llmProvider": {"type": "string", "required": True, "allowed": ["openai", "deepseek", "grok", "ollama"]},
            "llmModel": {"type": "string", "required": True},
            "apiSecretKey": {"type": "string", "required": False, "nullable": True},
        },
    },
}

def load_config_file(config_path):
    if not config_path:
        config_path = "configs/config.yaml"
    
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    v = Validator(schema)
    if not v.validate(config):
        raise ValueError(f"Invalid config: {v.errors}")

    return config

def load_llm_config(config):
    llm_config = config["llm_config"]

    llm_provider_env = os.getenv("LLM_PROVIDER", "").strip()
    llm_model_env = os.getenv("LLM_MODEL", "").strip()
    api_key_env = os.getenv("API_SECRET_KEY", "").strip()

    return {
        "llm_provider": (llm_provider_env or llm_config.get("llmProvider", "openai")).lower(),
        "llm_model": llm_model_env or llm_config.get("llmModel"),
        "api_key": api_key_env or llm_config.get("apiSecretKey"),
        "system_prompt": llm_config.get("llmCustomSysPrompt") or LLM_DEFAULT_SYS_PROMPT,
    }


def load_client_handler_config(config):
    client_handler_config = config["client_handler_config"]
    return {
        "ssh_banner": client_handler_config.get("ssh_banner") or DEFAULT_SSH_BANNER,
        "standard_banner": client_handler_config.get("standard_banner") or DEFAULT_STANDARD_BANNER,
        "password_regex": client_handler_config.get("authentication").get("password_regex") or DEFAULT_PASSWORD_REGEX,
    }


