from mistralai import Mistral
import os


def get_mistral_response(
    api_key,
    model_name="mistral-small-latest",
    prompt="list all files in my home dir",
    system_info="Manjaro Linux",
):
    try:
        client = Mistral(api_key=api_key)

        # The generation_config was commented out in the original, kept as is.
        # generation_config = {
        #    "temperature": 0.2,
        #    "top_p": 0.95,
        #    "top_k": 0,
        #    "max_output_tokens": 1024,
        # }
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

            print(str(response))

        import re

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


api_key = os.environ.get("MISTRAL_API_KEY")
get_mistral_response(api_key)
