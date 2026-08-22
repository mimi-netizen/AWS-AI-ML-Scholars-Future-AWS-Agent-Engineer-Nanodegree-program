"""
Terminal chat client for the bug-report harness. Each run is one fresh
conversation (new session id). Type 'exit' to quit.

    python chat.py
"""

import json
import uuid

import boto3

REGION = "us-east-1"


def load_harness_arn():
    with open("agentcore_config.json") as f:
        config = json.load(f)
    arn = config.get("harness_arn")
    if not arn:
        raise SystemExit("No harness_arn found in agentcore_config.json - run create_harness.py first.")
    return arn


def main():
    harness_arn = load_harness_arn()
    client = boto3.client("bedrock-agentcore", region_name=REGION)

    # runtimeSessionId must be at least 33 characters - uuid4 (36 chars) works.
    session_id = str(uuid.uuid4())
    print(f"Session: {session_id}")
    print("Type your message, or 'exit' to quit.\n")

    messages = []

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": [{"text": user_input}]})

        response = client.invoke_harness(
            harnessArn=harness_arn,
            runtimeSessionId=session_id,
            messages=messages,
        )

        assistant_text = ""
        for event in response["stream"]:
            if "contentBlockStart" in event:
                start = event["contentBlockStart"].get("start", {})
                if "toolUse" in start:
                    tool = start["toolUse"]
                    print(f"\n[tool call] {tool.get('name')}")
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"].get("delta", {})
                if "text" in delta:
                    text = delta["text"]
                    print(text, end="", flush=True)
                    assistant_text += text

        print()  # newline after streamed response
        messages.append({"role": "assistant", "content": [{"text": assistant_text}]})


if __name__ == "__main__":
    main()