# TONI - Terminal Operation Natural Instruction

TONI is an AI-powered terminal assistant that translates natural language descriptions into executable shell commands. It prioritizes Google Gemini and supports fallbacks to OpenAI and Mistral, as well as custom OpenAI-compatible providers.

## Project Overview

- **Main Technologies:** Python 3.10+, Google Gemini (genai), OpenAI API, Mistral AI, termcolor.
- **Architecture:**
  - `src/toni/cli.py`: The command-line interface entry point. It manages user input, iterates through available AI providers, and handles the execution confirmation loop.
  - `src/toni/core.py`: Contains the core logic for:
    - Detecting system information (OS, distribution, version).
    - Discovering and prioritizing AI providers from configuration.
    - Interacting with various LLM APIs (Gemini, OpenAI, Mistral).
    - Verifying command existence and executing them.
    - Managing shell history (ZSH and Windows custom history).
- **Configuration:** Users can configure providers and priorities in `~/.toni` (INI format).

## Building and Running

### Development Setup
To set up the project for development:
```bash
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

### Running TONI
You can run TONI directly from the source after installing it in editable mode:
```bash
toni "list all docker containers"
```

### Running Tests
The project uses the standard `unittest` framework:
```bash
python -m unittest discover tests
```

## Development Conventions

- **LLM Communication:** TONI expects LLMs to return a specific JSON structure:
  ```json
  {"cmd": "the-command", "exp": "explanation", "exec": true}
  ```
  - `cmd`: The single-line command to be executed.
  - `exp`: A brief explanation of what the command does.
  - `exec`: A boolean indicating if a command was successfully generated.
- **System Awareness:** Commands are tailored to the host OS. `core.get_system_message()` provides platform-specific examples to the LLM.
- **Safety First:** Commands are checked for existence using `shutil.which` before execution, and user confirmation is always required unless overridden (though currently, the CLI always asks).
- **Code Style:** The project follows standard Python practices. It uses `argparse` for CLI management and `termcolor` for formatted output.
- **Provider Priority:** Providers are tried in order of priority (highest first). Custom providers in `~/.toni` take precedence if they have higher priority values.
