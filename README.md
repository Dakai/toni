# TONI - Terminal Operation Natural Instruction

TONI is a lightweight CLI tool that translates natural language into terminal commands using AI. Simply describe what you want to do, and TONI will suggest the appropriate command for your system.

[![PyPI version](https://badge.fury.io/py/toni-cli.svg)](https://badge.fury.io/py/toni-cli)

## Inspiration

TONI was inspired by [YAI (Yet Another Interpreter)](https://github.com/ekzhang/yai), but with a focused approach. While YAI offers a comprehensive terminal experience, TONI is designed specifically to suggest and execute single commands based on natural language descriptions.

## Features

- Translates natural language to terminal commands
- Prioritizes Google Gemini AI with OpenAI fallback
- System-aware: Detects whether you're on Linux (Arch, Debian, etc.), macOS, or other systems
- Verifies command availability before execution
- Saves executed commands to ZSH history (when using ZSH)
- Simple to use and install

## Installation

```bash
# Install from PyPI
pip install toni-cli

# Or with pipx (recommended)
pipx install toni-cli
```

## Configuration

TONI requires at least one API key to function:

1. For Google Gemini (preferred):

```bash
export GOOGLEAI_API_KEY='your-gemini-api-key'
```

2. For OpenAI (fallback):

```bash
export OPENAI_API_KEY='your-openai-api-key'
```

Add these lines to your shell configuration file (~/.bashrc, ~/.zshrc, etc.) to make them persistent.

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

```
$ toni find all python files containing the word "error"

Detected system: Linux (arch)
Suggested command: grep -r "error" --include="*.py" .
Explanation: Search recursively for the word "error" in all Python files in the current directory
Do you want to execute this command? (y/n):
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
