#import argparse
#import sys
#import os
#import subprocess
#
#def get_ai_response(prompt, api_key):
#    # Placeholder for AI API call
#    # Implement the actual API call to Claude or OpenAI here
#    pass
#
#def execute_command(command):
#    try:
#        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
#        print("Command output:")
#        print(result.stdout)
#    except subprocess.CalledProcessError as e:
#        print(f"An error occurred while executing the command: {e}")
#        print("Error output:")
#        print(e.stderr)
#
#def main():
#    # Custom usage message
#    usage = "toni, <your natural language query>"
#    
#    parser = argparse.ArgumentParser(description="TONI: Terminal Operation Natural Instruction", usage=usage)
#    parser.add_argument('query', nargs=argparse.REMAINDER, help="Your natural language query")
#    args = parser.parse_args()
#
#    # Join all arguments into a single string
#    full_input = ' '.join(args.query)
#
#    # Check if the input starts with a comma and remove it if present
#    if full_input.startswith(','):
#        query = full_input[1:].strip()
#    else:
#        print("Usage: toni, <your natural language query>")
#        sys.exit(1)
#
#    api_key = os.environ.get('OPENAI_API_KEY')
#
#    if not api_key:
#        print("Please set the AI_API_KEY environment variable.")
#        return
#
#    prompt = f"Convert the following request into a Linux terminal command: {query}"
#    response = get_ai_response(prompt, api_key)
#
#    print(f"Suggested command: {response}")
#    
#    confirmation = input("Do you want to execute this command? (y/n): ").lower()
#    if confirmation == 'y':
#        execute_command(response)
#    else:
#        print("Command execution cancelled.")
#
#if __name__ == "__main__":
#    main()

import argparse
import requests
import os
import subprocess

def get_ai_response(prompt, api_key):
    # Placeholder for AI API call
    # Implement the actual API call to Claude or OpenAI here
    pass

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print("Command output:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the command: {e}")
        print("Error output:")
        print(e.stderr)

def main():
    parser = argparse.ArgumentParser(description="TONI: Terminal Operation Natural Instruction")
    parser.add_argument('query', nargs='+', help="Your natural language query")
    args = parser.parse_args()

    query = ' '.join(args.query)
    api_key = os.environ.get('OPENAI_API_KEY')

    if not api_key:
        print("Please set the AI_API_KEY environment variable.")
        return

    prompt = f"Convert the following request into a Linux terminal command: {query}"
    response = get_ai_response(prompt, api_key)

    print(f"Suggested command: {response}")
    
    confirmation = input("Do you want to execute this command? (y/n): ").lower()
    if confirmation == 'y' or confirmation == '':
        execute_command(response)
    else:
        print("Command execution cancelled.")

if __name__ == "__main__":
    main()
