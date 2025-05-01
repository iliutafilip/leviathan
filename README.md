# Leviathan LLM-Powered SSH Honeypot                                              

Leviathan is a low-code high-interaction SSH honeypot written in Python that leverages a Large Language Model to emulate realistic shell behavior. It captures attacker interactions and logs them in structured JSON format.

## Quick Start Using Docker Compose

Pull from git

```bash
  git https://github.com/iliutafilip/leviathan.git
  cd leviathan
```

Build the Docker images and start the honeypot

```bash
  docker-compose build
  docker-compose up -d
```
To view the leviathan honeypot's output and logs
```bash
  docker-compose logs -f leviathan
```

## Attacker Session

![Client Session Screenshot](https://github.com/user-attachments/assets/6ac4b158-b6d7-4e23-8dc9-fa3e66277ae2)

## Leviathan Output

![Image](https://github.com/user-attachments/assets/f1ee77fb-b40a-40be-accc-ecbe0f6344c1)

## Config

Leviathan honeypot can be configured via the `configs/config.yaml` file.  
You can edit `configs/config.yaml` to customize your banner, authentication rules, and LLM settings.

**Example configuration file**

```yaml
ssh_banner: "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"
standard_banner: "Welcome to Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-1027-generic x86_64)\r\n* Documentation:  https://help.ubuntu.com\r\n* Management:     https://landscape.canonical.com\r\n* Support:        https://ubuntu.com/pro\r\n"
authentication:
  password_regex: "^(123456|Leviathan2|mypass|xbox|azert|robi|root)$"
llm_config:
  llmProvider: "openai"
  llmModel: "gpt-4o-mini"
  apiSecretKey: "sk-proj-1234"
```

## OpenAI Support

Leviathan Honeypot offers support for **OpenAI, Deepseek or GROK** LLM models through **OpenAI** API calls.

## Ollama Support

TBA
