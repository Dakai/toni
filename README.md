# TONI - Terminal Operation Natural Instruction

TONI is a lightweight CLI tool that translates natural language into terminal commands using AI. Simply describe what you want to do, and TONI will suggest the appropriate command for your system.

[![PyPI version](https://badge.fury.io/py/toni-cli.svg)](https://badge.fury.io/py/toni-cli)

## Inspiration

TONI was inspired by [YAI (Yet Another Interpreter)](https://github.com/ekzhang/yai), but with a focused approach. While YAI offers a comprehensive terminal experience, TONI is designed specifically to suggest and execute single commands based on natural language descriptions.

## Features

- Translates natural language to terminal commands
- Prioritizes Google Gemini AI with OpenAI fallback
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

## Configuration

TONI uses a configuration file at `~/.toni` (INI format). By default, it supports Google Gemini, OpenAI, and Mistral.

### Built-in Providers

1. **Google Gemini** (Preferred):
   ```bash
   export GOOGLEAI_API_KEY='your-gemini-api-key'
   ```

2. **OpenAI**:
   ```bash
   export OPENAI_API_KEY='your-openai-api-key'
   ```

3. **Mistral**:
   ```bash
   export MISTRAL_API_KEY='your-mistral-api-key'
   ```

### Custom OpenAI-Compatible Providers

You can add unlimited custom providers (Ollama, LM Studio, OpenRouter, etc.) by adding sections to `~/.toni`. Any section with a `url` field is treated as an OpenAI-compatible provider.

#### Example: Ollama
```ini
[ollama]
url = http://localhost:11434/v1
key = ollama
model = llama3.2:latest
priority = 100
```

#### Example: OpenRouter
```ini
[openrouter]
url = https://openrouter.ai/api/v1
key = sk-or-v1-xxx...
model = anthropic/claude-3.5-sonnet
priority = 80
```

### Priority System

- Custom providers are tried first, sorted by their `priority` field (higher numbers first).
- Default priority is `50`.
- Built-in providers have default priorities: OpenAI (`50`), Gemini (`40`), Mistral (`30`).
- If a provider is disabled (`disabled = true`) or fails, TONI falls back to the next one in the chain.

### Environment Variables

For any custom provider `[my-provider]`, you can set the API key via:
```bash
export MY_PROVIDER_API_KEY='your-key'
```

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

1. Clone the repository:

```bash
git clone https://github.com/yourusername/toni.git
cd toni
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install for development:

```bash
pip install -e ".[dev]"
```

4. Make your changes and submit a pull request!

## License

MIT

## Acknowledgements

- [YAI](https://github.com/ekzhang/yai) for the inspiration
- Google Gemini and OpenAI for their powerful AI APIs
