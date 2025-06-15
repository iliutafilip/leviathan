import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import yaml

from LLM.LLM_integration import LLMHoneypot
from store.user_history_store import UserHistoryStore
from config_parser.config_parser import load_config_file
from tests.mock_config_data import get_mock_config, get_mock_ollama_config


class TestLLMHoneypotIntegration(unittest.TestCase):

    def setUp(self):
        self.config_data = get_mock_config()
        self.temp_config_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
        with open(self.temp_config_file.name, "w") as f:
            yaml.dump(self.config_data, f)

        self.loaded_config = load_config_file(self.temp_config_file.name)

    def tearDown(self):
        os.unlink(self.temp_config_file.name)

    @patch("LLM.LLM_integration.requests.Session.post")
    def test_execute_model_post_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "mock\r\nuser@host:~$ "
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        user_history = UserHistoryStore("store/test_user_history.db")
        honeypot = LLMHoneypot(username="Test", ssh_server_ip="127.0.0.1", config=self.loaded_config, history_store=user_history)

        output = honeypot.execute_model("ls")
        self.assertIn("mock", output)
        self.assertIn("user@host", output)

    @patch("LLM.LLM_integration.requests.Session.post")
    def test_execute_model_post_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": []}
        mock_post.return_value = mock_response

        user_history = UserHistoryStore("store/test_user_history.db")
        honeypot = LLMHoneypot(username="Test", ssh_server_ip="127.0.0.1", config=self.loaded_config, history_store=user_history)

        with self.assertRaises(ValueError) as context:
            honeypot.execute_model("ls")

        self.assertIn("No choices", str(context.exception))

    @patch("LLM.LLM_integration.requests.Session.post")
    def test_execute_model_ollama_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "ollama output\r\nuser@host:~$ "
            }
        }
        mock_post.return_value = mock_response

        ollama_config = get_mock_ollama_config()
        with open(self.temp_config_file.name, "w") as f:
            yaml.dump(ollama_config, f)

        loaded_ollama_config = load_config_file(self.temp_config_file.name)

        user_history = UserHistoryStore("store/test_user_history.db")
        honeypot = LLMHoneypot(username="Test", ssh_server_ip="127.0.0.1", config=loaded_ollama_config,
                               history_store=user_history)

        output = honeypot.execute_model("whoami")
        self.assertIn("ollama output", output)
        self.assertIn("user@host", output)


if __name__ == '__main__':
    unittest.main()
