from openai import OpenAI
import os
import subprocess
import time
from google import genai
import platform
import shutil

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
            distro = (
                subprocess.check_output("cat /etc/os-release | grep -w ID", shell=True)
                .decode()
                .strip()
                .split("=")[1]
                .strip('"')
            )
            return f"Linux ({distro})"
        except:
            return "Linux"
    elif system == "Darwin":
        return "macOS"
    elif system == "Windows":
        return "Windows"
    else:
        return system


def get_gemini_response(api_key, prompt, system_info):
    try:
        client = genai.Client(api_key=api_key)

        formatted_system_message = system_message.format(system_info=system_info)

        # Create the generation config with system instructions
        # generation_config = {
        #    "temperature": 0.2,
        #    "top_p": 0.95,
        #    "top_k": 0,
        #    "max_output_tokens": 1024,
        # }

        # The new Gemini API doesn't always handle system messages properly
        # Let's combine the system message with the user prompt
        combined_prompt = f"{formatted_system_message}\n\nUser request: {prompt}"

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"parts": [{"text": combined_prompt}]}],
        )

        # Extract just the JSON part from the response
        response_text = response.text
        # Find JSON between curly braces if there's extra text
        import re

        if response_text:
            json_match = re.search(r"(\{.*?\})", response_text, re.DOTALL)
            if json_match:
                return json_match.group(1)
            return response_text

    except Exception as e:
        print(f"An error occurred with Gemini: {e}")
        return None


def get_open_ai_response(api_key, prompt, system_info):
    try:
        client = OpenAI(api_key=api_key)

        formatted_system_message = system_message.format(system_info=system_info)

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": formatted_system_message},
                {"role": "user", "content": prompt},
            ],
            model="gpt-4o-mini",
            temperature=0.2,
        )

        response = chat_completion.choices[0].message.content

        # Extract just the JSON part from the response
        import re

        if response:
            json_match = re.search(r"(\{.*?\})", response, re.DOTALL)
            if json_match:
                return json_match.group(1)
            return response

    except Exception as e:
        print(f"An error occurred with OpenAI: {e}")
        return None


def write_to_zsh_history(command):
    try:
        current_time = int(time.time())  # Get current Unix timestamp
        timestamped_command = (
            f": {current_time}:0;{command}"  # Assuming duration of 0 for now
        )
        with open("/home/dakai/.zsh_history", "a") as f:
            f.write(timestamped_command + "\n")
    except Exception as e:
        print(f"An error occurred while writing to .zsh_history: {e}")


def reload_zsh_history():
    try:
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
        # reload_zsh_history()
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the command: {e}")
        print("Error output:")
        print(e.stderr)


def command_exists(command):
    # Extract the base command (before any options or arguments)
    base_command = command.split()[0]
    return shutil.which(base_command) is not None
