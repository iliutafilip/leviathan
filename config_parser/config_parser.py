import os
import yaml
from cerberus import Validator

LLM_DEFAULT_SYS_PROMPT = (
    "You are an Ubuntu Linux terminal. Respond with the exact command output, using STRICTLY '\r\n' for new lines instead of '\n'. NO Markdown, explanations, or extra comments. Format responses as:`<command_output>\r\n<username>@<ssh_server_ip>:<current_directory>$ `"
)

DEFAULT_STANDARD_BANNER = (
    "Welcome to Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-1027-generic x86_64)\r\n* Documentation:  https://help.ubuntu.com\r\n* Management:     https://landscape.canonical.com\r\n* Support:        https://ubuntu.com/pro\r\n"
)

DEFAULT_SSH_BANNER = (
    "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"
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
                    "password_regex": {"type": "string", "required": True},
                },
            },
            },
    },
    "llm_config": {
        "type": "dict",
        "required": True,
        "schema": {
            "llmCustomSysPrompt": {"type": "string", "required": False, "nullable": True},
            "llmProvider": {"type": "string", "required": True, "allowed": ["openai", "deepseek", "grok"]},
            "llmModel": {"type": "string", "required": True},
            "apiSecretKey": {"type": "string", "required": True},
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

def load_llm_config(config_path):
    config = load_config_file(config_path)
    llm_config = config["llm_config"]
    return {
        "llm_provider": os.getenv("LLM_PROVIDER", llm_config.get("llmProvider", "openai")).lower(),
        "llm_model": os.getenv("LLM_MODEL", llm_config.get("llmModel")),
        "api_key": os.getenv("API_SECRET_KEY", llm_config.get("apiSecretKey")),
        "system_prompt": llm_config.get("llmSysPrompt") or LLM_DEFAULT_SYS_PROMPT,
    }

def load_client_handler_config(config_path):
    config = load_config_file(config_path)
    client_handler_config = config["client_handler_config"]
    return {
        "ssh_banner": client_handler_config.get("ssh_banner") or DEFAULT_SSH_BANNER,
        "standard_banner": client_handler_config.get("standard_banner") or DEFAULT_STANDARD_BANNER,
        "password_regex": client_handler_config.get("authentication").get("password_regex"),
    }


