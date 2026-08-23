import os
import subprocess
import time
import platform
import shutil
import configparser
import re
import json

try:
    import litellm
except ImportError:
    litellm = None
def get_system_message(system_info):
    """Generate system message with platform-specific examples."""

    # Base message structure
    base_message = """Your are a powerful terminal assistant generating a JSON containing a command line for my input.
You will always reply using the following json structure: {{"cmd":"the command", "exp": "some explanation", "exec": true}}.
Your answer will always only contain the json structure, never add any advice or supplementary detail or information,
even if I asked the same question before.
The field cmd will contain a single line command (don't use new lines, use separators like && and ; instead).
The field exp will contain an short explanation of the command if you managed to generate an executable command, otherwise it will contain the reason of your failure.
The field exec will contain true if you managed to generate an executable command, false otherwise.

The host system is using {system_info}. Please ensure commands are compatible with this environment.

Examples:"""

    # Platform-specific examples
    if "Windows" in system_info:
        examples = """
Me: list all files in my home dir
You: {{"cmd":"dir %USERPROFILE%", "exp": "list all files in your home directory", "exec": true}}
Me: find all PDF files in current directory
You: {{"cmd":"dir *.pdf /s", "exp": "search for all PDF files in current directory and subdirectories", "exec": true}}
Me: show my disk usage
You: {{"cmd":"wmic logicaldisk get size,freespace,caption", "exp": "display disk space information for all drives", "exec": true}}
Me: what processes are using the most memory
You: {{"cmd":"tasklist /fo csv | sort /r", "exp": "list all processes sorted by memory usage", "exec": true}}
Me: how are you ?
You: {{"cmd":"", "exp": "I'm good thanks but I cannot generate a command for this.", "exec": false}}"""
    else:
        # Unix/Linux/macOS examples
        examples = """
Me: list all files in my home dir
You: {{"cmd":"ls ~", "exp": "list all files in your home dir", "exec": true}}
Me: list all pods of all namespaces
You: {{"cmd":"kubectl get pods --all-namespaces", "exp": "list pods form all k8s namespaces", "exec": true}}
Me: show my disk usage
You: {{"cmd":"df -h", "exp": "display disk space usage in human-readable format", "exec": true}}
Me: what processes are using the most memory
You: {{"cmd":"ps aux --sort=-%mem | head", "exp": "show top processes by memory usage", "exec": true}}
Me: how are you ?
You: {{"cmd":"", "exp": "I'm good thanks but I cannot generate a command for this.", "exec": false}}"""

    return base_message + examples


def get_system_info():
    system = platform.system()
    if system == "Linux":
        try:
            # Read /etc/os-release to find distro ID
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro = line.strip().split("=")[1]
                        distro = distro.strip('"')  # Remove potential quotes
                        return f"Linux ({distro})"
            return "Linux (Unknown Distro)"  # Fallback If ID not found
        except FileNotFoundError:
            return "Linux (Unknown Distro, /etc/os-release not found)"
        except Exception:
            return "Linux (Error reading distro)"
    elif system == "Darwin":
        return "macOS"
    elif system == "Windows":
        # Provide more context for Windows
        try:
            version = platform.version()
            release = platform.release()
            return f"Windows {release} ({version})"
        except Exception:
            return "Windows"
    else:
        return system


def load_app_config():
    config_file_path = os.path.join(os.path.expanduser("~"), ".toni")
    config = configparser.ConfigParser()

    # Define default values using an INI string
    default_ini_content = """
[OPENAI]
url =
key =
env-key =
model = gpt-4o-mini
disabled = false
priority = 50

[GEMINI]
url =
key =
env-key =
model = gemini-2.0-flash
disabled = false
priority = 40

[MISTRAL]
url =
key =
env-key =
model = mistral-small-latest
disabled = false
priority = 30

[DEEPSEEK]
url =
key =
env-key =
model = deepseek-v4-flash
disabled = false
priority = 25
    """
    config.read_string(default_ini_content)  # Load built-in defaults

    if os.path.exists(config_file_path):
        config.read(config_file_path)  # User's config overrides defaults

    return config


_LITELLM_PREFIX = {
    "GEMINI": "gemini",
    "MISTRAL": "mistral",
    "OPENAI": "openai",
    "DEEPSEEK": "deepseek",
    "OPENROUTER": "openrouter",
}


def _litellm_model(provider):
    """Map provider dict to litellm model string."""
    name = provider["name"].upper()
    model = provider["model"]
    # already prefixed (e.g. openrouter/xxx) -> keep as-is
    if "/" in model:
        return model
    prefix = _LITELLM_PREFIX.get(name)
    if prefix:
        return f"{prefix}/{model}"
    # custom provider with url -> treat as OpenAI-compatible
    if provider.get("url"):
        return f"openai/{model}"
    return model


def get_llm_response(provider, prompt, system_info):
    """Single entry point via litellm. Returns JSON string or None."""
    if litellm is None:
        print("Error: 'litellm' package not installed. Run: pip install litellm")
        return None
    # resolve api_key
    if provider.get("env_key"):
        api_key = os.environ.get(provider["env_key"])
    else:
        env_name = f"{provider['name'].upper()}_API_KEY"
        # GEMINI historically uses GOOGLEAI_API_KEY
        if provider["name"].upper() == "GEMINI":
            api_key = provider.get("key") or os.environ.get("GOOGLEAI_API_KEY") or os.environ.get(env_name)
        else:
            api_key = provider.get("key") or os.environ.get(env_name)
    if not api_key:
        return None
    litellm_model = _litellm_model(provider)
    system_msg = get_system_message(system_info).format(system_info=system_info)
    kwargs = {
        "model": litellm_model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        "api_key": api_key,
        "temperature": 0,
        "max_tokens": 4096,
    }
    if provider.get("url"):
        kwargs["api_base"] = provider["url"]
    try:
        resp = litellm.completion(**kwargs)
        content = resp.choices[0].message.content if resp.choices else None
        if not content:
            return None
        content = str(content)
        m = re.search(r"(\{.*?\})", content, re.DOTALL)
        if m:
            try:
                json.loads(m.group(1))
                return m.group(1)
            except json.JSONDecodeError:
                pass
        return content
    except Exception as e:
        print(f"An error occurred with {provider['name']} (model: {provider['model']}): {e}")
        return None


# --- deprecated shims (keep import compatibility) ---
def get_gemini_response(api_key, prompt, system_info, model_name="gemini-2.0-flash"):
    return get_llm_response({"name": "GEMINI", "model": model_name, "url": "", "key": api_key, "env_key": ""}, prompt, system_info)


def get_mistral_response(api_key, prompt, system_info, model_name="mistral-small-latest"):
    return get_llm_response({"name": "MISTRAL", "model": model_name, "url": "", "key": api_key, "env_key": ""}, prompt, system_info)


def get_open_ai_response(api_key, prompt, system_info, model_name="gpt-4o-mini", base_url=None):
    return get_llm_response({"name": "OPENAI", "model": model_name, "url": base_url or "https://api.openai.com/v1", "key": api_key, "env_key": ""}, prompt, system_info)


def call_openai_compatible(provider_name, base_url, api_key, model_name, prompt, system_info):
    return get_llm_response({"name": provider_name, "model": model_name, "url": base_url or "", "key": api_key, "env_key": ""}, prompt, system_info)


def get_openrouter_response(api_key, prompt, system_info, model_name="openrouter/free"):
    return get_llm_response({"name": "OPENROUTER", "model": model_name, "url": "", "key": api_key, "env_key": ""}, prompt, system_info)


def discover_providers(config):
    custom_providers = []
    native_providers = []

    for section in config.sections():
        try:
            if config.getboolean(section, "disabled", fallback=False):
                continue
        except ValueError:
            continue

        url = config.get(section, "url", fallback="").strip()

        provider_data = {
            "name": section,
            "url": url,
            "key": config.get(section, "key", fallback=""),
            "env_key": config.get(section, "env-key", fallback=""),
            "model": config.get(section, "model", fallback=""),
            "priority": config.getint(section, "priority", fallback=50),
        }

        if url:
            custom_providers.append(provider_data)
        elif section == "OPENAI":
            provider_data["url"] = "https://api.openai.com/v1"
            if not provider_data["model"]:
                provider_data["model"] = "gpt-4o-mini"
            custom_providers.append(provider_data)
        elif section == "GEMINI":
            if not provider_data["model"]:
                provider_data["model"] = "gemini-2.0-flash"
            native_providers.append(provider_data)
        elif section == "MISTRAL":
            if not provider_data["model"]:
                provider_data["model"] = "mistral-small-latest"
            native_providers.append(provider_data)
        elif section == "OPENROUTER":
            if not provider_data["model"]:
                provider_data["model"] = "openrouter/free"
            native_providers.append(provider_data)
        elif section == "DEEPSEEK":
            provider_data["url"] = "https://api.deepseek.com/v1"
            if not provider_data["model"]:
                provider_data["model"] = "deepseek-v4-flash"
            custom_providers.append(provider_data)
        else:
            continue

    custom_providers.sort(key=lambda p: p["priority"], reverse=True)
    native_providers.sort(key=lambda p: p["priority"], reverse=True)

    return {
        "custom": custom_providers,
        "native": native_providers,
    }


def write_to_zsh_history(command):
    """Write command to ZSH history (Unix/Linux/macOS)."""
    try:
        zsh_history_file = os.path.join(os.path.expanduser("~"), ".zsh_history")
        if not os.path.exists(os.path.dirname(zsh_history_file)):
            return  # Silently skip if ZSH not configured
        current_time = int(time.time())
        timestamped_command = f": {current_time}:0;{command}"
        with open(zsh_history_file, "a") as f:
            f.write(timestamped_command + "\n")
    except Exception:
        pass  # Silently fail - history writing is not critical


def write_to_powershell_history(command):
    """Write command to PowerShell history (Windows)."""
    try:
        # PowerShell history is stored in a different location
        # The actual history file is managed by PSReadLine module
        # We can add to the command history by writing to the console history buffer
        # or by using a custom approach
        ps_history_dir = os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Roaming",
            "Microsoft",
            "Windows",
            "PowerShell",
            "PSReadLine",
        )
        if os.path.exists(ps_history_dir):
            # PowerShell history file format is complex, so we'll use a simpler approach
            # Write to a custom toni history file that users can reference
            toni_history_file = os.path.join(os.path.expanduser("~"), ".toni_history")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(toni_history_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {command}\n")
    except Exception:
        pass  # Silently fail - history writing is not critical


def write_command_history(command, system_info):
    """Write command to appropriate shell history based on system."""
    if "Windows" in system_info:
        write_to_powershell_history(command)
    else:
        write_to_zsh_history(command)


def reload_zsh_history():  # This function was unused (commented out call)
    try:
        # Sourcing .zshrc from Python may not affect the parent shell environment.
        # This is generally tricky. For now, keeping it as is.
        os.system("source ~/.zshrc")
        result = subprocess.run(
            "source ~/.zshrc", shell=True, check=True, text=True, capture_output=True
        )
        print(result.stdout)
    except Exception as e:
        print(f"An error occurred while reloading .zshrc: {e}")


def execute_command(command, system_info=""):
    try:
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True
        )
        print("Command output:")
        print(result.stdout)
        write_command_history(command, system_info)
        # reload_zsh_history() # Call was commented out in original
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the command: {e}")
        print("Error output:")
        print(e.stderr)
    except FileNotFoundError:  # Handle command not found at execution time too
        print(f"Error: Command not found: {command.split()[0]}")


def command_exists(command):
    if not command:  # Handle empty command string
        return False
    base_command = command.split()[0]
    return shutil.which(base_command) is not None
