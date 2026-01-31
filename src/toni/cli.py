import argparse
import os
import json
from termcolor import colored

# Assuming 'toni' is a package or core.py is in PYTHONPATH
# If core.py is in the same directory, use: from core import ...
from toni.core import (
    get_system_info,
    get_gemini_response,
    get_mistral_response,
    call_openai_compatible,
    discover_providers,
    command_exists,
    execute_command,
    load_app_config,
)


__version__ = "0.1.15"


def main():
    try:
        parser = argparse.ArgumentParser(
            description="TONI: Terminal Operation Natural Instruction"
        )
        parser.add_argument(
            "-v", "--version", action="version", version=f"toni {__version__}"
        )
        parser.add_argument("query", nargs="*", help="Your natural language query")
        args = parser.parse_args()

        if not args.query:
            parser.print_help()
            return

        query = " ".join(args.query).rstrip("?")

        system_info = get_system_info()
        print(f"Detected system: {system_info}")

        app_config = load_app_config()
        providers = discover_providers(app_config)

        response = None
        provider_used = None

        for provider in providers["custom"]:
            env_key_name = f"{provider['name'].upper()}_API_KEY"
            api_key = provider["key"] or os.environ.get(env_key_name)

            if not api_key:
                if provider["name"] == "OPENAI":
                    print(
                        "OpenAI API key not found in config (OPENAI.key) or environment (OPENAI_API_KEY). Skipping."
                    )
                else:
                    print(
                        f"API key not found for provider '{provider['name']}'. Skipping."
                    )
                continue

            response = call_openai_compatible(
                provider["name"],
                provider["url"],
                api_key,
                provider["model"],
                query,
                system_info,
            )

            if response:
                provider_used = provider["name"]
                break

        if response is None:
            for provider in providers["native"]:
                if provider["name"] == "GEMINI":
                    api_key = provider["key"] or os.environ.get("GOOGLEAI_API_KEY")
                    if not api_key:
                        print(
                            "Gemini API key not found in config (GEMINI.key) or environment (GOOGLEAI_API_KEY). Skipping."
                        )
                        continue

                    response = get_gemini_response(
                        api_key, query, system_info, provider["model"]
                    )
                    if response:
                        provider_used = "Gemini"
                        break

                elif provider["name"] == "MISTRAL":
                    api_key = provider["key"] or os.environ.get("MISTRAL_API_KEY")
                    if not api_key:
                        print(
                            "Mistral API key not found in config (MISTRAL.key) or environment (MISTRAL_API_KEY). Skipping."
                        )
                        continue

                    response = get_mistral_response(
                        api_key, query, system_info, provider["model"]
                    )
                    if response:
                        provider_used = "Mistral"
                        break

        if response is None:
            print("\nFailed to get a command from any LLM provider.")
            print(
                "Please check your API key configurations in ~/.toni or environment variables."
            )
            return

        # print(
        #    f"Response obtained from: {provider_used if provider_used else 'Unknown'}"
        # )

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
                f"\nWarning: The command '{colored(cmd.split()[0], 'red')}' doesn't appear to be installed or in PATH."
            )
            print(f"Suggested command: {colored(cmd, 'blue')}")
            print(f"Explanation: {colored(explanation, 'blue')}")
            # print("Please verify and ensure the command is available before execution.")
        else:
            print(f"\nSuggested command: {cmd}")
            print(f"Explanation: {explanation}")

        try:
            confirmation = input("Do you want to execute the command? (Y/n): ").lower()
            if confirmation == "y" or confirmation == "":  # Default to yes
                execute_command(cmd, system_info)
            else:
                print(colored("Command execution cancelled.", "red"))
        except KeyboardInterrupt:
            print(
                colored("\nOperation cancelled by user (during confirmation).", "red")
            )
            return

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return
    except Exception as e:
        print(colored((f"An unexpected error occurred: {e}"), "red"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # This is redundant if main() already handles it, but good for robustness
        print(colored("\nOperation cancelled by user (main level).", "red"))
