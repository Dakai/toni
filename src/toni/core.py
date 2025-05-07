import os
import subprocess
import time
from google import genai  # Assuming this is google.generativeai or compatible
from openai import OpenAI
from mistralai import Mistral
import platform
import shutil
import configparser
import re


system_message = """Your are a powerful terminal assistant generating a JSON containing a command line for my input.
You will always reply using the following json structure: {{"cmd":"the command", "exp": "some explanation", "exec": true}}.
Your answer will always only contain the json structure, never add any advice or supplementary detail or information,
even if I asked the same question before.
The field cmd will contain a single line command (don't use new lines, use separators like && and ; instead).
The field exp will contain an short explanation of the command if you managed to generate an executable command, otherwise it will contain the reason of your failure.
The field exec will contain true if you managed to generate an executable command, false otherwise.

The host system is using {system_info}. Please ensure commands are compatible with this environment.

Examples:
Me: list all files in my home dir
You: {{"cmd":"ls ~", "exp": "list all files in your home dir", "exec": true}}
Me: list all pods of all namespaces
You: {{"cmd":"kubectl get pods --all-namespaces", "exp": "list pods form all k8s namespaces", "exec": true}}
Me: how are you ?
You: {{"cmd":"", "exp": "I'm good thanks but I cannot generate a command for this.", "exec": false}}"""


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
model = gpt-4o-mini
disabled = false

[GEMINI]
url =
key =
model = gemini-2.0-flash
disabled = false
    """
    config.read_string(default_ini_content)  # Load built-in defaults

    if os.path.exists(config_file_path):
        config.read(config_file_path)  # User's config overrides defaults

    return config


def get_gemini_response(api_key, prompt, system_info, model_name="gemini-2.0-flash"):
    try:
        # Note: The genai.Client() initialization might vary depending on the exact Google library version/package.
        # This code assumes the user's existing genai.Client() works as intended.
        # If using google-generativeai, it's usually:
        # import google.generativeai as genai
        # genai.configure(api_key=api_key)
        # model_service = genai.GenerativeModel(model_name)
        # response = model_service.generate_content(...)
        client = genai.Client(api_key=api_key)

        formatted_system_message = system_message.format(system_info=system_info)
        combined_prompt = f"{formatted_system_message}\n\nUser request: {prompt}"

        # The generation_config was commented out in the original, kept as is.
        # generation_config = {
        #    "temperature": 0.2,
        #    "top_p": 0.95,
        #    "top_k": 0,
        #    "max_output_tokens": 1024,
        # }

        response = client.models.generate_content(
            model=model_name,  # Use the model_name parameter
            contents=[{"parts": [{"text": combined_prompt}]}],
            # generation_config=generation_config, # If you intend to use this
        )

        response_text = response.text

        if response_text:
            json_match = re.search(r"(\{.*?\})", response_text, re.DOTALL)
            if json_match:
                return json_match.group(1)
            return response_text  # Fallback to raw text if no JSON object found
        return None  # Explicitly return None if response_text is empty

    except Exception as e:
        print(f"An error occurred with Gemini (model: {model_name}): {e}")
        return None


def get_mistral_response(
    api_key,
    prompt,
    system_info,
    model_name="mistral-small-latest",
):
    try:
        client = Mistral(api_key=api_key)

        formatted_system_message = system_message.format(system_info=system_info)

        chat_completion = client.chat.complete(
            messages=[
                {"role": "system", "content": formatted_system_message},
                {"role": "user", "content": prompt},
            ],
            model=model_name,  # Use the model_name parameter
        )

        response = None

        if chat_completion.choices:
            response = chat_completion.choices[0].message.content

        if response:
            response = str(response)
            json_match = re.search(r"(\{.*?\})", response, re.DOTALL)
            if json_match:
                return json_match.group(1)
            return response  # Fallback to raw text if no JSON object found
        return None  # Explicitly return None if response is empty

    except Exception as e:
        print(f"An error occurred with Mistral (model: {model_name}): {e}")
        return None


def get_open_ai_response(
    api_key, prompt, system_info, model_name="gpt-4o-mini", base_url=None
):
    try:
        client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)

        formatted_system_message = system_message.format(system_info=system_info)

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": formatted_system_message},
                {"role": "user", "content": prompt},
            ],
            model=model_name,  # Use the model_name parameter
            temperature=0.2,
        )

        response = chat_completion.choices[0].message.content

        if response:
            json_match = re.search(r"(\{.*?\})", response, re.DOTALL)
            if json_match:
                return json_match.group(1)
            return response  # Fallback to raw text if no JSON object found
        return None  # Explicitly return None if response is empty

    except Exception as e:
        print(f"An error occurred with OpenAI (model: {model_name}): {e}")
        return None


def write_to_zsh_history(command):
    try:
        zsh_history_file = os.path.join(os.path.expanduser("~"), ".zsh_history")
        if not os.path.exists(os.path.dirname(zsh_history_file)):
            print(
                f"Warning: ZSH history directory {os.path.dirname(zsh_history_file)} does not exist. Skipping history write."
            )
            return
        current_time = int(time.time())
        timestamped_command = f": {current_time}:0;{command}"
        with open(zsh_history_file, "a") as f:
            f.write(timestamped_command + "\n")
    except Exception as e:
        print(f"An error occurred while writing to ZSH history: {e}")


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


def execute_command(command):
    try:
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True
        )
        print("Command output:")
        print(result.stdout)
        write_to_zsh_history(command)
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
