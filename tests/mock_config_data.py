def get_mock_config():
    return {
        "client_handler_config": {
            "ssh_banner": None,
            "standard_banner": None,
            "authentication": {
            }
        },
        "llm_config": {
            "llmCustomSysPrompt": "",
            "llmProvider": "grok",
            "llmModel": "grok-3-mini-fast-beta",
            "apiSecretKey": "my-key"
        }
    }

def get_mock_ollama_config():
    return {
        "client_handler_config": {
            "ssh_banner": None,
            "standard_banner": None,
            "authentication": {
                "password_regex": "^(test123|admin)$"
            }
        },
        "llm_config": {
            "llmCustomSysPrompt": "",
            "llmProvider": "ollama",
            "llmModel": "llama3",
            "apiSecretKey": None
        }
    }

def get_incorrect_mock_config():
    """
    missing required `llmModel` field in llm_config
    """
    return {
        "client_handler_config": {
            "ssh_banner": "SSH-2.0-TestBanner",
            "standard_banner": "Welcome to test banner",
            "authentication": {
            },
        },
        "llm_config": {
            "llmProvider": "openai",
            # "llmModel" is missing here → invalid
            "apiSecretKey": "test-key"
        }
    }

