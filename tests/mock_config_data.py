def get_mock_config():
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
            "llmProvider": "grok",
            "llmModel": "grok-3-mini-fast-beta",
            "apiSecretKey": "my-key"
        }
    }
