import unittest
from unittest.mock import patch, MagicMock

from LLM.LLM_integration import LLMHoneypot
from store.user_history_store import UserHistoryStore


class TestLLMHoneypotIntegration(unittest.TestCase):

    @patch("LLM.LLM_integration.OpenAI")
    def test_execute_model_openai_success(self, mock):
        mock_choice = MagicMock()
        mock_choice.message.content = "mock\r\nuser@host:~$ "

        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock.return_value = mock_client

        user_history = UserHistoryStore("store/test_user_history.db")
        honeypot = LLMHoneypot(username="Tset", ssh_server_ip="127.0.0.1", provider="openai", api_key="api_key", model="model", history_store=user_history)

        output = honeypot.execute_model("ls")
        self.assertIn("mock", output)
        self.assertIn("user@host", output)

    @patch("LLM.LLM_integration.OpenAI")
    def test_execute_model_openai_failure(self, mock):
        mock.return_value.chat.completions.create.side_effect = ValueError("No choices returned from LLM provider")

        user_history = UserHistoryStore("store/test_user_history.db")
        honeypot = LLMHoneypot(username="Tset", ssh_server_ip="127.0.0.1", provider="openai", api_key="api_key",
                               model="model", history_store=user_history)

        with self.assertRaises(ValueError) as context:
            honeypot.execute_model("ls")

        self.assertIn("No choices returned from LLM provider", str(context.exception))

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
        honeypot = LLMHoneypot(username="Tset", ssh_server_ip="127.0.0.1", provider="deepseek", api_key="api_key",
                               model="model", history_store=user_history)

        print(honeypot.provider)

        output = honeypot.execute_model("ls")
        self.assertIn("mock", output)
        self.assertIn("user@host", output)

    @patch("LLM.LLM_integration.requests.Session.post")
    def test_execute_model_post_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": []}
        mock_post.return_value = mock_response

        user_history = UserHistoryStore("store/test_user_history.db")
        honeypot = LLMHoneypot(username="Tset", ssh_server_ip="127.0.0.1", provider="deepseek", api_key="api_key", model="model", history_store=user_history)

        with self.assertRaises(ValueError) as context:
            honeypot.execute_model("ls")

        self.assertIn("No choices", str(context.exception))

    def test_invalid_provider(self):
        with self.assertRaises(ValueError) as context:
            LLMHoneypot(username="Tset", ssh_server_ip="127.0.0.1", provider="provider")

        self.assertIn("not a valid LLMProvider", str(context.exception))


    def test_custom_prompt_build(self):
        user_history = UserHistoryStore("store/test_user_history.db")
        honeypot = LLMHoneypot(username="Tset", ssh_server_ip="127.0.0.1", provider="openai", api_key="api_key",
                               model="model", custom_prompt="act as a linux ubuntu shell", history_store=user_history)

        self.assertEqual("act as a linux ubuntu shell", honeypot.custom_prompt)



if __name__ == '__main__':
    unittest.main()
