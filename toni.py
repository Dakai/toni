import argparse
from openai import OpenAI
import os
import subprocess
import json
import time
#import google.generativeai as genai

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


def get_open_ai_response(api_key, prompt):
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

#def get_gemini_response(api_key, prompt):
#    try:
#        genai.configure(api_key=api_key)
#        model = genai.GenerativeModel("gemini-1.5-pro-latest")
#        content = [
#            {'role': 'system', 'parts': [system_message]},
#            {'role': 'user', 'parts': [prompt]}
#        ]
#        response = model.generate_content(content)
#        return response.text
#    except Exception as e:
#        print(f"An error occurred: {e}")
#        return None

def write_to_zsh_history(command):
    try:
        current_time = int(time.time())  # Get current Unix timestamp
        timestamped_command = f": {current_time}:0;{command}"  # Assuming duration of 0 for now
        with open("/home/dakai/.zsh_history", "a") as f:
            f.write(timestamped_command + "\n")
    except Exception as e:
        print(f"An error occurred while writing to .zsh_history: {e}")

def reload_zsh_history():
    try:
        os.system("source ~/.zshrc")
        result = subprocess.run("source ~/.zshrc", shell=True, check=True, text=True, capture_output=True)
        print(result.stdout)
    except Exception as e:
        print(f"An error occurred while reloading .zshrc: {e}")

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print("Command output:")
        print(result.stdout)
        write_to_zsh_history(command)
        #reload_zsh_history()
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
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    #google_api_key = os.environ.get('GOOGLEAI_API_KEY')

    #if google_api_key:
    #    response = get_gemini_response(google_api_key, query)

    #else:
    if openai_api_key:
        response = get_open_ai_response(openai_api_key, query)

    else:
        print("Please set the OPENAI_API_KEY or GOOGLEAI_API_KEY environment variable.")
        return

    #response = get_open_ai_response(openai_api_key, query)
    
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
