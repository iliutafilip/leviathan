# Leviathan LLM-Powered SSH Honeypot                                              

Leviathan is a low-code high-interaction SSH honeypot written in Python that leverages a Large Language Model to emulate realistic shell behavior. It captures attacker interactions and logs them in structured JSON format.

## Startup

Pull from git
```bash
  git clone https://github.com/iliutafilip/leviathan.git
  cd leviathan
```

To start the honeypot run:
```bash
  ./setup.sh
```

To shut down and remove containers:
```bash
  docker-compose down
```

To temporarily stop the docker container:
```bash
   docker-compose stop
```

To see Leviathan logs in real time run the following command:
```bash
   docker-compose logs -f leviathan
```

## Configuration

Leviathan honeypot can be configured via the `configs/config.yaml` file.  
You can edit `configs/config.yaml` to customize your banner, authentication rules, and LLM settings.

**Example configuration file**

```yaml
client_handler_config:
  ssh_banner: "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"
  standard_banner: "Welcome to Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-1027-generic x86_64)\r\n* Documentation:  https://help.ubuntu.com\r\n* Management:     https://landscape.canonical.com\r\n* Support:        https://ubuntu.com/pro\r\n"
  authentication:
    password_regex: "^(123456|Leviathan2|mypass|xbox|azert|robi|root)$"
llm_config:
  llmCustomSysPrompt: "Act as an Ubuntu shell"
  llmProvider: "openai"
  llmModel: "gpt-4o-mini"
  apiSecretKey: "sk-proj-1234"
```

You can override the default configuration file with a custom one:

```bash
   ./setup.sh ./configs/custom.yaml
```

You can also set the LLM provider, model and API key as environment variables using a `.env` file:

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
API_SECRET_KEY=sk-proj-1234
```

## Attacker Session Example

![Client Session Screenshot](https://github.com/user-attachments/assets/6ac4b158-b6d7-4e23-8dc9-fa3e66277ae2)

## Leviathan Output Example

![Image](https://github.com/user-attachments/assets/f1ee77fb-b40a-40be-accc-ecbe0f6344c1)

## Kibana Dashboard for Log Visualisation

Leviathan includes a prebuilt Kibana dashboard available at http://localhost:8080.  

The dashboard provides:
- Total number of attacker sessions
- Username/password tag clouds
- Histogram of attacks over time
- Attacker commands distribution

## OpenAI Support

Leviathan Honeypot offers support for **OpenAI, Deepseek** or **GROK** LLM models through **OpenAI** API calls.

## Ollama Support

Leviathan also supports running LLMs locally using **Ollama**.

The default Ollama endpoint used is: `http://localhost:11434/api/generate`

## PyUnit Tests

To run PyUnit tests, run the following:

`python3 -m unittest discover -s tests`
