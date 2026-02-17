import requests
import uuid
from uuid import uuid4 

HOST_URL = "http://localhost:9000/"

def send_to_host_agent(user_text: str):

    session_id = uuid4().hex

    # payload = {
    #     "jsonrpc": "2.0",
    #     "id": str(uuid.uuid4()),
    #     "method": "tasks/send",   # A2A standard method
    #     "params": {
    #         "input": {
    #             "type": "text",
    #             "text": user_text
    #         }
    #     }
    # }

    # payload = {
    #         "jsonrpc": "2.0",
    #         "id": uuid4().hex,  # Generate a new unique task ID for this message
    #         "sessionId": session_id,  # Reuse or create session ID
    #         "message": {
    #             "role": "user",  # The message is from the user
    #             "parts": [{"type": "text", "text": user_text}]  # Wrap user input in a text part
    #         }
    #     }
    
    payload = {
                "jsonrpc": "2.0",
                "id": "cecdb365bd0e46aba74625f50ed65883",
                "method": "tasks/send",
                "params": {
                    "id": "82ab272868a74cf48a43e1e2303a1b4f",
                    "sessionId": "30481464e53742f29e9d2d1114c90137",
                    "message": {
                    "role": "user",
                    "parts": [
                        {
                        "type": "text",
                        "text": user_text
                        }
                    ]
                    },
                    "historyLength": 0,   # integer
                    "metadata": {}        # dictionary
                }
                }

    response = requests.post(HOST_URL, json=payload)

    if response.status_code != 200:
        return f"Error: {response.text}"

    result = response.json()

    print("+++++++++++++++++++++++++++++++")
    print(result)
    print("+++++++++++++++++++++++++++++++")

    # adjust depending on your response structure
    return result.get("result", {}).get("output", result)
