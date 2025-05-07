import argparse
import os
import json

# Assuming 'toni' is a package or core.py is in PYTHONPATH
# If core.py is in the same directory, use: from core import ...
from toni.core import (
    get_system_info,
    get_gemini_response,
    get_open_ai_response,
    get_mistral_response,
    command_exists,
    execute_command,
    load_app_config,  # Import the new config loader
)


def main():
    try:
        parser = argparse.ArgumentParser(
            description="TONI: Terminal Operation Natural Instruction"
        )
        parser.add_argument("query", nargs="+", help="Your natural language query")
        args = parser.parse_args()

        query = " ".join(args.query).rstrip("?")

        system_info = get_system_info()
        print(f"Detected system: {system_info}")

        app_config = load_app_config()

        # OpenAI Settings
        openai_disabled = app_config.getboolean("OPENAI", "disabled")
        openai_key_from_config = app_config.get("OPENAI", "key")
        openai_api_key = (
            openai_key_from_config
            if openai_key_from_config
            else os.environ.get("OPENAI_API_KEY")
        )
        openai_model = app_config.get(
            "OPENAI", "model"
        )  # Defaults handled by load_app_config
        openai_url = app_config.get(
            "OPENAI", "url"
        )  # Defaults handled by load_app_config

        # Gemini Settings
        gemini_disabled = app_config.getboolean("GEMINI", "disabled")
        gemini_key_from_config = app_config.get("GEMINI", "key")
        gemini_api_key = (
            gemini_key_from_config
            if gemini_key_from_config
            else os.environ.get("GOOGLEAI_API_KEY")
        )
        gemini_model = app_config.get(
            "GEMINI", "model"
        )  # Defaults handled by load_app_config
        # gemini_url = app_config.get("GEMINI", "url")

        # Mistral AI Settings
        mistral_disabled = app_config.getboolean("MISTRAL", "disabled")
        mistral_key_from_config = app_config.get("MISTRAL", "key")
        mistral_api_key = (
            mistral_key_from_config
            if mistral_key_from_config
            else os.environ.get("MISTRAL_API_KEY")
        )
        mistral_model = app_config.get(
            "MISTRAL", "model"
        )  # Defaults handled by load_app_config

        response = None
        provider_used = None

        # Try Gemini first if not disabled and API key is available
        if not gemini_disabled:
            if gemini_api_key:
                print(
                    f"Attempting to use Gemini (model: {gemini_model if gemini_model else 'gemini-2.0-flash'})..."
                )
                response = get_gemini_response(
                    gemini_api_key, query, system_info, gemini_model
                )
                if response:
                    provider_used = "Gemini"
            else:
                print(
                    "Gemini API key not found in config (GEMINI.key) or environment (GOOGLEAI_API_KEY). Skipping Gemini."
                )
        else:
            print("Gemini is disabled in the configuration.")

        # Fall back to OpenAI if Gemini failed or was skipped, and if OpenAI is not disabled and API key is available
        if response is None and not openai_disabled:
            if openai_api_key:
                print(
                    f"Attempting to use OpenAI (model: {openai_model if openai_model else 'gpt-4o-mini'}{', URL: ' + openai_url if openai_url else ''})..."
                )
                response = get_open_ai_response(
                    openai_api_key, query, system_info, openai_model, openai_url
                )
                if response:
                    provider_used = "OpenAI"
            else:
                print(
                    "OpenAI API key not found in config (OPENAI.key) or environment (OPENAI_API_KEY). Skipping OpenAI."
                )
        elif (
            response is None and openai_disabled
        ):  # Only print if it wasn't tried because it's disabled
            print("OpenAI is disabled in the configuration.")

        ## Fall back to Mistral if Gemini and OpenAI failed or was skipped
        if response is None and not mistral_disabled:
            if mistral_api_key:
                print(
                    f"Attempting to use Mistral AI (model: {mistral_model if mistral_model else 'mistral-small-latest'})..."
                )
                response = get_mistral_response(
                    mistral_api_key, query, system_info, mistral_model
                )
                if response:
                    provider_used = "Mistral AI"
            else:
                print(
                    "Mistral API key not found in config (MISTRAL.key) or environment (MISTRAL_API_KEY). Skipping Mistral."
                )
        elif (
            response is None and mistral_disabled
        ):  # Only print if it wasn't tried because it's disabled
            print("Mistral AI is disabled in the configuration.")

        if response is None:
            print("\nFailed to get a command from any LLM provider.")
            if (
                (gemini_disabled or not gemini_api_key)
                and (openai_disabled or not openai_api_key)
                and (mistral_disabled or not mistral_api_key)
            ):
                print(
                    "Please check your API key configurations in ~/.toni or environment "
                    "variables (GOOGLEAI_API_KEY, OPENAI_API_KEY, MISTRAL_API_KEY) and ensure providers are not disabled."
                )
            return

        print(
            f"Response obtained from: {provider_used if provider_used else 'Unknown'}"
        )

        try:
            data = json.loads(response)
        except Exception as e:
            print(f"An error occurred while parsing the LLM response: {e}")
            print(
                f"Raw response from {provider_used if provider_used else 'LLM'}: {response}"
            )
            return

        if data.get("exec") == False:  # Handles "exec": false
            print(f"LLM could not generate a command: {data.get('exp')}")
            return

        cmd = data.get("cmd")
        explanation = data.get("exp")

        if (
            not cmd
        ):  # Handles cases where cmd is empty but exec might not be explicitly false
            print(
                f"LLM did not provide a command. Explanation: {explanation if explanation else 'No explanation provided.'}"
            )
            return

        if not command_exists(cmd):
            print(
                f"\nWarning: The command '{cmd.split()[0]}' doesn't appear to be installed or in PATH."
            )
            print(f"Suggested command: {cmd}")
            print(f"Explanation: {explanation}")
            print("Please verify and ensure the command is available before execution.")
        else:
            print(f"\nSuggested command: {cmd}")
            print(f"Explanation: {explanation}")

        try:
            confirmation = input("Do you want to execute this command? (Y/n): ").lower()
            if confirmation == "y" or confirmation == "":  # Default to yes
                execute_command(cmd)
            else:
                print("Command execution cancelled.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user (during confirmation).")
            return

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # This is redundant if main() already handles it, but good for robustness
        print("\nOperation cancelled by user (main level).")
