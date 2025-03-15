import argparse
import os
import json

from toni.core import (
    get_system_info,
    get_gemini_response,
    get_open_ai_response,
    command_exists,
    execute_command,
)


def main():
    try:
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
            print(
                "Please set the GOOGLEAI_API_KEY or OPENAI_API_KEY environment variable."
            )
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

        try:
            confirmation = input("Do you want to execute this command? (y/n): ").lower()
            if confirmation == "y" or confirmation == "":
                execute_command(cmd)
            else:
                print("Command execution cancelled.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
