import os
import tempfile
import unittest

import yaml

from config_parser.config_parser import load_llm_config, LLM_DEFAULT_SYS_PROMPT, load_client_handler_config, \
    DEFAULT_SSH_BANNER, DEFAULT_STANDARD_BANNER
from tests.mock_config_data import get_mock_config


class TestConfigParser(unittest.TestCase):

    def setUp(self):
        self.config_data = get_mock_config()
        self.temp_config_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
        with open(self.temp_config_file.name, "w") as f:
            yaml.dump(self.config_data, f)


    def tearDown(self):
        os.unlink(self.temp_config_file.name)


    def test_llm_config_default_and_environ_override(self):
        os.environ.pop("LLM_PROVIDER", None)
        os.environ.pop("LLM_MODEL", None)
        os.environ.pop("API_SECRET_KEY", None)

        config = load_llm_config(config_path=self.temp_config_file.name)
        self.assertEqual(config["llm_provider"], "grok")
        self.assertEqual(config["llm_model"], "grok-3-mini-fast-beta")
        self.assertEqual(config["api_key"], "my-key")
        self.assertEqual(config["system_prompt"], LLM_DEFAULT_SYS_PROMPT)

        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["LLM_MODEL"] = "gpt-4o-mini"
        os.environ["API_SECRET_KEY"] = "my-env-key"

        config_env = load_llm_config(config_path=self.temp_config_file.name)
        self.assertEqual(config_env["llm_provider"], "openai")
        self.assertEqual(config_env["llm_model"], "gpt-4o-mini")
        self.assertEqual(config_env["api_key"], "my-env-key")

    def test_client_handler_config_defaults(self):
        config = load_client_handler_config(config_path=self.temp_config_file.name)
        self.assertEqual(config["ssh_banner"], DEFAULT_SSH_BANNER)
        self.assertEqual(config["standard_banner"], DEFAULT_STANDARD_BANNER)
        self.assertEqual(config["password_regex"], "^(test123|admin)$")


if __name__ == "__main__":
    unittest.main()
