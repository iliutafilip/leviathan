import os
import tempfile
import unittest
import yaml

from config_parser.config_parser import (
    load_config_file,
    load_llm_config,
    LLM_DEFAULT_SYS_PROMPT,
    load_client_handler_config,
    DEFAULT_SSH_BANNER,
    DEFAULT_STANDARD_BANNER,
    DEFAULT_PASSWORD_REGEX,
)
from tests.mock_config_data import get_mock_config, get_incorrect_mock_config


class TestConfigParser(unittest.TestCase):

    def setUp(self):
        self.config_data = get_mock_config()
        self.temp_config_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
        with open(self.temp_config_file.name, "w") as f:
            yaml.dump(self.config_data, f)

        self.loaded_config = load_config_file(self.temp_config_file.name)

    def tearDown(self):
        os.unlink(self.temp_config_file.name)

    def test_llm_config_default_and_environ_override(self):
        os.environ.pop("LLM_PROVIDER", None)
        os.environ.pop("LLM_MODEL", None)
        os.environ.pop("API_SECRET_KEY", None)

        config = load_llm_config(self.loaded_config)
        self.assertEqual(config["llm_provider"], "grok")
        self.assertEqual(config["llm_model"], "grok-3-mini-fast-beta")
        self.assertEqual(config["api_key"], "my-key")
        self.assertEqual(config["system_prompt"], LLM_DEFAULT_SYS_PROMPT)

        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["LLM_MODEL"] = "gpt-4o-mini"
        os.environ["API_SECRET_KEY"] = "my-env-key"

        config_env = load_llm_config(self.loaded_config)
        self.assertEqual(config_env["llm_provider"], "openai")
        self.assertEqual(config_env["llm_model"], "gpt-4o-mini")
        self.assertEqual(config_env["api_key"], "my-env-key")

    def test_client_handler_config_defaults(self):
        config = load_client_handler_config(self.loaded_config)
        self.assertEqual(config["ssh_banner"], DEFAULT_SSH_BANNER)
        self.assertEqual(config["standard_banner"], DEFAULT_STANDARD_BANNER)
        self.assertEqual(config["password_regex"], DEFAULT_PASSWORD_REGEX)

    def test_llm_custom_sys_prompt(self):
        self.config_data["llm_config"]["llmCustomSysPrompt"] = "Custom LLM prompt."
        with open(self.temp_config_file.name, "w") as f:
            yaml.dump(self.config_data, f)

        loaded_config = load_config_file(self.temp_config_file.name)
        config = load_llm_config(loaded_config)

        self.assertIn("Custom LLM prompt.", config["system_prompt"])

    def test_client_handler_config_provided_fields(self):
        self.config_data["client_handler_config"]["ssh_banner"] = "SSH-2.0-TestBanner"
        self.config_data["client_handler_config"]["standard_banner"] = "Test Banner\r\n"
        self.config_data["client_handler_config"]["authentication"]["password_regex"] = "^test$"

        with open(self.temp_config_file.name, "w") as f:
            yaml.dump(self.config_data, f)

        loaded_config = load_config_file(self.temp_config_file.name)
        client_config = load_client_handler_config(loaded_config)

        self.assertEqual(client_config["ssh_banner"], "SSH-2.0-TestBanner")
        self.assertEqual(client_config["standard_banner"], "Test Banner\r\n")
        self.assertEqual(client_config["password_regex"], "^test$")

    def test_invalid_config_raises_value_error(self):
        invalid_config = get_incorrect_mock_config()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w") as tmp:
            yaml.dump(invalid_config, tmp)
            tmp_path = tmp.name

        with self.assertRaises(ValueError) as ctx:
            _ = load_config_file(tmp_path)

        os.unlink(tmp_path)
        self.assertIn("llmModel", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()
