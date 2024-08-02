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
from openai import OpenAI
import os
import subprocess
import json

system_message = """Your are a powerful terminal assistant generating a JSON containing a command line for my input.
You will always reply using the following json structure: {"cmd":"the command", "exp": "some explanation", "exec": true}.
Your answer will always only contain the json structure, never add any advice or supplementary detail or information,
even if I asked the same question before.
The field cmd will contain a single line command (don't use new lines, use separators like && and ; instead).
The field exp will contain an short explanation of the command if you managed to generate an executable command, otherwise it will contain the reason of your failure.
The field exec will contain true if you managed to generate an executable command, false otherwise.

Examples:
Me: list all files in my home dir
Yai: {"cmd":"ls ~", "exp": "list all files in your home dir", "exec": true}
Me: list all pods of all namespaces
Yai: {"cmd":"kubectl get pods --all-namespaces", "exp": "list pods form all k8s namespaces", "exec": true}
Me: how are you ?
Yai: {"cmd":"", "exp": "I'm good thanks but I cannot generate a command for this.", "exec": false}"""


def get_ai_response(system_message, api_key ,prompt):
    try:
        client = OpenAI(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            model='gpt-4o-mini'
        )
        response = chat_completion.choices[0].message.content
        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

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

    #print(f"Query: {query}")
    api_key = os.environ.get('OPENAI_API_KEY')

    if not api_key:
        print("Please set the AI_API_KEY environment variable.")
        return

    #prompt = f"Convert the following request into a Linux terminal command: {query}"
    response = get_ai_response(system_message, api_key, query)
    
    if response is None:
        return
    try:
        data = json.loads(response)
    
    except Exception as e:
        print(f"An error occurred while parsing the response: {e}")
        return

    if data.get('exec') == False:
        print(data.get('exp'))
        return

    print(f"Suggested command: {data.get('cmd')}")
    print(f"Explanation: {data.get('exp')}")
    
    confirmation = input("Do you want to execute this command? (y/n): ").lower()
    if confirmation == 'y' or confirmation == '':
        execute_command(data.get('cmd'))
    else:
        print("Command execution cancelled.")

if __name__ == "__main__":
    main()
