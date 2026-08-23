# TONI — Terminal Operation Natural Instruction

> Describe in plain English, get a shell command. `Gemini` `OpenAI` `Mistral` `DeepSeek` `Ollama` `Groq` … one `~/.toni` via [`litellm`](https://github.com/BerriAI/litellm).

[![PyPI version](https://badge.fury.io/py/toni-cli.svg)](https://pypi.org/project/toni-cli/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/toni-cli?label=downloads&logo=pypi)](https://pypi.org/project/toni-cli/)
[![Python 3.10+](https://img.shields.io/pypi/pyversions/toni-cli?logo=python&logoColor=white)](https://pypi.org/project/toni-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/Dakai/toni?style=social)](https://github.com/Dakai/toni)

TONI is a lightweight CLI that translates natural language into terminal commands — system-aware (Linux/macOS/Windows), verifies the binary exists, and optionally executes.

## Inspiration

TONI was inspired by [YAI (Yet Another Interpreter)](https://github.com/ekzhang/yai), but with a focused approach. While YAI offers a comprehensive terminal experience, TONI is designed specifically to suggest and execute single commands based on natural language descriptions.

## Features

- Translates natural language to terminal commands
- **Unified LLM via `litellm`**: single entry point for 100+ providers (OpenAI, Gemini, Mistral, DeepSeek, OpenRouter, Ollama, Groq, etc.) — no per-provider boilerplate
- **Cross-platform**: Works on Linux, macOS, and Windows
- System-aware: Detects your OS and generates platform-appropriate commands
- Verifies command availability before execution
- Saves executed commands to shell history (ZSH on Unix, custom history on Windows)
- Simple to use and install

## Installation

```bash
# Install from PyPI
pip install toni-cli

# Or with pipx (recommended)
pipx install toni-cli
```

### Windows Installation

TONI works on Windows via pip or pipx:

```powershell
# Using pip
pip install toni-cli

# Or with pipx (recommended)
pipx install toni-cli
```

**Note**: On Windows, TONI generates Windows-native commands (CMD/PowerShell) and saves command history to `~/.toni_history`.

## Demo

![TONI demo: translating natural language into shell commands](assets/demo.gif)

## Configuration

TONI uses a configuration file at `~/.toni` (INI format) and env vars. Since `0.1.23` all providers are routed through [`litellm`](https://github.com/BerriAI/litellm) — one `completion()` call for 100+ models, no per-provider boilerplate. Old `~/.toni` files remain fully compatible.

### Built-in Providers

Defaults (override in `~/.toni` or env):

| Provider | Model default | Env var | Priority |
|---|---|---|---|
| `GEMINI` | `gemini-2.0-flash` | `GOOGLEAI_API_KEY` | 40 |
| `OPENAI` | `gpt-4o-mini` | `OPENAI_API_KEY` | 50 |
| `MISTRAL` | `mistral-small-latest` | `MISTRAL_API_KEY` | 30 |
| `DEEPSEEK` | `deepseek-v4-flash` | `DEEPSEEK_API_KEY` | 25 |
| `OPENROUTER` | `openrouter/free` | `OPENROUTER_API_KEY` | 50 |

```bash
export GOOGLEAI_API_KEY='your-gemini-api-key'
export OPENAI_API_KEY='your-openai-api-key'
export MISTRAL_API_KEY='your-mistral-api-key'
```

Per-provider `~/.toni` overrides:
```ini
[GEMINI]
model=gemini-2.5-flash-lite
priority=40

[OPENAI]
model=gpt-4o-mini
priority=50
```

### Custom Providers (litellm)

Any section with `url` is treated as an OpenAI-compatible endpoint (`model` → `openai/<model>` + `api_base=url`). Built-ins map to `litellm` prefixes (`gemini/`, `openai/`, `mistral/`, `deepseek/`, `openrouter/`).

#### Example: Ollama (local)
```ini
[ollama]
url = http://localhost:11434/v1
key = ollama
model = llama3.2:latest
priority = 100
```

#### Example: Groq / OpenRouter / custom gateway
```ini
[groq]
url = https://api.groq.com/openai/v1
model = llama-3.1-8b-instant
env-key = GROQ_API_KEY
priority = 90

[openrouter]
url = https://openrouter.ai/api/v1
key = sk-or-v1-xxx...
model = anthropic/claude-3.5-sonnet
priority = 80
```

### Priority & Fallback

- All providers (`custom` + `native`) are merged and tried in `priority` descending (higher first, default `50`).
- `disabled=true` skips a provider; failure falls through to next.
- `env-key` lets a section read its key from a custom env var (e.g. `env-key=GROQ_API_KEY`).

### Environment Variables

For any custom provider `[my-provider]`, you can set the key via:
```bash
export MY_PROVIDER_API_KEY='your-key'
```
or `env-key` in the INI. `GOOGLEAI_API_KEY` is also accepted for `GEMINI`.

## Usage

Simply type `toni` followed by your natural language description:

```bash
# Basic file operations
toni list all pdf files in current directory
toni find all files modified in the last 7 days

# System queries
toni show my disk usage
toni what processes are using the most memory

# Complex tasks
toni create a backup of my Documents folder
toni find the largest files in this directory
```

## Examples

### Linux/macOS
```
$ toni find all python files containing the word "error"

Detected system: Linux (arch)
Suggested command: grep -r "error" --include="*.py" .
Explanation: Search recursively for the word "error" in all Python files in the current directory
Do you want to execute this command? (y/n):
```

### Windows
```
> toni find all python files containing the word "error"

Detected system: Windows 10 (10.0.19045)
Suggested command: findstr /s /i "error" *.py
Explanation: Search for "error" in all Python files recursively
Do you want to execute this command? (Y/n):
```

## Development

To contribute to TONI:

```bash
git clone https://github.com/Dakai/toni.git
cd toni
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install for development:

```bash
pip install -e .
```

4. Make your changes and submit a pull request!

## License

MIT

## Acknowledgements

- [YAI](https://github.com/ekzhang/yai) for the inspiration
- [BerriAI/litellm](https://github.com/BerriAI/litellm) for the unified LLM gateway
- Google Gemini, OpenAI, Mistral, DeepSeek for their APIs
