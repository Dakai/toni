import argparse
from openai import OpenAI
import os
import subprocess
import json
import time
from google import genai
import platform
import shutil

system_message = """Your are a powerful terminal assistant generating a JSON containing a command line for my input.
You will always reply using the following json structure: {"cmd":"the command", "exp": "some explanation", "exec": true}.
Your answer will always only contain the json structure, never add any advice or supplementary detail or information,
even if I asked the same question before.
The field cmd will contain a single line command (don't use new lines, use separators like && and ; instead).
The field exp will contain an short explanation of the command if you managed to generate an executable command, otherwise it will contain the reason of your failure.
The field exec will contain true if you managed to generate an executable command, false otherwise.

The host system is using {system_info}. Please ensure commands are compatible with this environment.

Examples:
Me: list all files in my home dir
Yai: {"cmd":"ls ~", "exp": "list all files in your home dir", "exec": true}
Me: list all pods of all namespaces
Yai: {"cmd":"kubectl get pods --all-namespaces", "exp": "list pods form all k8s namespaces", "exec": true}
Me: how are you ?
Yai: {"cmd":"", "exp": "I'm good thanks but I cannot generate a command for this.", "exec": false}"""


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
        if "Windows" in system_info:
            formatted_system_message = system_message.format(system_info=system_info)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                {"role": "system", "parts": [formatted_system_message]},
                {"role": "user", "parts": [prompt]},
            ],
        )

        return response.text
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
        )
        response = chat_completion.choices[0].message.content
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


def main():
    parser = argparse.ArgumentParser(
        description="TONI: Terminal Operation Natural Instruction"
    )
    parser.add_argument("query", nargs="+", help="Your natural language query")
    args = parser.parse_args()

    # Remove trailing question mark if present
    query = " ".join(args.query).rstrip("?")

    system_info = get_system_info()
    print(f"Detected system: {system_info}")

    google_api_key = os.environ.get("GOOGLEAI_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    response = None

    # Try Gemini first, fall back to OpenAI
    if google_api_key:
        response = get_gemini_response(google_api_key, query, system_info)

    if response is None and openai_api_key:
        response = get_open_ai_response(openai_api_key, query, system_info)

    if response is None:
        print("Please set the GOOGLEAI_API_KEY or OPENAI_API_KEY environment variable.")
        return

    try:
        data = json.loads(response)
    except Exception as e:
        print(f"An error occurred while parsing the response: {e}")
        print(f"Raw response: {response}")
        return

    if data.get("exec") == False:
        print(data.get("exp"))
        return

    cmd = data.get("cmd")

    # Check if the command exists
    if cmd and not command_exists(cmd):
        print(
            f"Warning: The command '{cmd.split()[0]}' doesn't appear to be installed on your system."
        )
        print(f"Suggested command: {cmd}")
        print(f"Explanation: {data.get('exp')}")
        print("Please verify that this command will work on your system.")
    else:
        print(f"Suggested command: {cmd}")
        print(f"Explanation: {data.get('exp')}")

    confirmation = input("Do you want to execute this command? (y/n): ").lower()
    if confirmation == "y" or confirmation == "":
        execute_command(cmd)
    else:
        print("Command execution cancelled.")


if __name__ == "__main__":
    main()
