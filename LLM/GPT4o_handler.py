import re
import openai
import yaml

with open("configs/plugins-config.yaml", 'r') as f:
    config = yaml.safe_load(f)

# LLM_PROVIDER = config['plugin']['llmProvider']
LLM_MODEL = config['plugin']['llmModel']
OPENAI_KEY = config['plugin']['openAISecretKey']

DEV_PROMPT = ("You will act as an Ubuntu Linux terminal. "
              "The user will type commands, and you are to reply with what the terminal should show. "
              "Your responses must be contained within a single code block. "
              "Do not provide note. Do not provide explanations or type commands unless explicitly instructed by the user. "
              "Your entire response/output is going to consist of a simple text with \n for new line, and you will NOT wrap it within string md markers.")

class GPT4oHandler:
    # TODO: FINE-TUNED Model

    def __init__(self):
        self.client = openai.OpenAI(api_key=OPENAI_KEY)

        self.history = [
            {"role": "system", "content": DEV_PROMPT},
            {"role": "user", "content": "pwd"},
            {"role": "assistant", "content": "/home/user"},
        ]

    def build_prompt(self, command):
        messages = self.history.copy()
        messages.append(
            {
            'role': 'user',
            "content": command
            }
        )
        return messages

    def query_llm(self, command):
        if not OPENAI_KEY:
            raise Exception("OpenAI key not set")

        try:
            messages = self.build_prompt(command)

            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
            )

            result = response.choices[0].message.content
            cleaned_result = self.clean_output(result)

            self.history.append(
                {
                    "role": "assistant",
                    "content": cleaned_result,
                }
            )

            return cleaned_result

        except Exception as e:
            raise e


    @staticmethod
    def clean_output(content):
        regex = re.compile("(```( *)?([a-z]*)?(\\n)?)")
        return regex.sub("", content).strip()